#!/usr/bin/env python3
"""Capture read-only local Git facts for one review range."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class SnapshotError(RuntimeError):
    """Raised when exact review facts cannot be established."""


def git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.quotePath=false",
        "-C",
        str(repo),
        *args,
    ]
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
        env=env,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SnapshotError(f"git command failed ({result.returncode}): {detail}")
    return result.stdout


def resolve_commit(repo: Path, revision: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").strip()


def parse_name_status(raw: str) -> list[dict[str, Any]]:
    fields = raw.split("\0")
    if fields and not fields[-1]:
        fields.pop()
    files: list[dict[str, Any]] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(fields):
                raise SnapshotError("truncated rename or copy record")
            old_path, path = fields[index], fields[index + 1]
            index += 2
            files.append({"status": status, "path": path, "old_path": old_path})
        else:
            if index >= len(fields):
                raise SnapshotError("truncated changed-file record")
            files.append({"status": status, "path": fields[index], "old_path": None})
            index += 1
    return files


def diff_path(value: str, prefix: str) -> str | None:
    value = value.strip()
    if value == "/dev/null":
        return None
    if value.startswith(prefix):
        return value[len(prefix) :]
    return value


def parse_line_ranges(diff: str) -> dict[str, dict[str, list[list[int]]]]:
    ranges: dict[str, dict[str, list[list[int]]]] = {}
    old_path: str | None = None
    new_path: str | None = None
    for line in diff.splitlines():
        if line.startswith("--- "):
            old_path = diff_path(line[4:], "a/")
            continue
        if line.startswith("+++ "):
            new_path = diff_path(line[4:], "b/")
            continue
        match = HUNK.match(line)
        if not match:
            continue
        old_start = int(match.group(1))
        old_count = int(match.group(2) or "1")
        new_start = int(match.group(3))
        new_count = int(match.group(4) or "1")
        if old_path and old_count:
            item = ranges.setdefault(old_path, {"LEFT": [], "RIGHT": []})
            item["LEFT"].append([old_start, old_start + old_count - 1])
        if new_path and new_count:
            item = ranges.setdefault(new_path, {"LEFT": [], "RIGHT": []})
            item["RIGHT"].append([new_start, new_start + new_count - 1])
    return ranges


def build_snapshot(
    repo: Path, base: str, head: str | None, working_tree: bool
) -> dict[str, Any]:
    root = Path(git(repo, "rev-parse", "--show-toplevel").strip()).resolve()
    base_oid = resolve_commit(root, base)
    head_oid = resolve_commit(root, head or "HEAD")
    merge_bases = [
        value for value in git(root, "merge-base", "--all", base_oid, head_oid).splitlines() if value
    ]
    if len(merge_bases) != 1:
        raise SnapshotError(f"expected one best merge base, found {len(merge_bases)}")
    merge_base = merge_bases[0]

    if working_tree:
        diff_endpoints = [merge_base]
    else:
        diff_endpoints = [merge_base, head_oid]

    name_status = git(
        root,
        "diff",
        "--no-ext-diff",
        "--name-status",
        "-z",
        "-M",
        "-C",
        *diff_endpoints,
        "--",
    )
    changed_files = parse_name_status(name_status)
    diff = git(
        root,
        "diff",
        "--no-ext-diff",
        "--no-color",
        "--unified=0",
        *diff_endpoints,
        "--",
    )
    line_ranges = parse_line_ranges(diff)

    if working_tree:
        tracked_paths = {item["path"] for item in changed_files}
        for entry in git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").split("\0"):
            if entry.startswith("?? "):
                path = entry[3:]
                if path not in tracked_paths:
                    changed_files.append({"status": "?", "path": path, "old_path": None})

    for item in changed_files:
        current = line_ranges.get(item["path"], {"LEFT": [], "RIGHT": []})
        old = line_ranges.get(item.get("old_path") or item["path"], current)
        item["right_ranges"] = current["RIGHT"]
        item["left_ranges"] = old["LEFT"]

    status = [
        entry
        for entry in git(root, "status", "--porcelain=v2", "-z", "--branch").split("\0")
        if entry
    ]
    return {
        "schema_version": 1,
        "mode": "working_tree" if working_tree else "committed_range",
        "repository_root": str(root),
        "base_oid": base_oid,
        "head_oid": head_oid,
        "merge_bases": merge_bases,
        "merge_base": merge_base,
        "changed_files": changed_files,
        "user_checkout_status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    parser.add_argument("--working-tree", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.working_tree and args.head:
        parser.error("--head and --working-tree are mutually exclusive")
    if not args.working_tree and not args.head:
        parser.error("--head is required for a committed range")

    try:
        snapshot = build_snapshot(args.repo, args.base, args.head, args.working_tree)
    except SnapshotError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    rendered = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
