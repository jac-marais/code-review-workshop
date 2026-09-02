#!/usr/bin/env python3
"""Validate a review result and optional changed-line snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "review_status",
    "delivery_state",
    "external_posting_authorized",
    "output_comments",
    "suppressions",
    "cleared",
    "checks",
    "blocking_limits",
    "completion_receipts",
}
WORKBENCHES = {
    "behavior-and-contracts",
    "state-and-failure",
    "security-and-privacy",
    "design-and-maintainability",
    "evidence-and-integration",
}


def is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def in_ranges(line: int, ranges: list[list[int]]) -> bool:
    return any(start <= line <= end for start, end in ranges)


def validate(data: Any, snapshot: Any | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["result must be an object"]
    missing = REQUIRED_KEYS - data.keys()
    extra = data.keys() - REQUIRED_KEYS
    if missing:
        errors.append(f"missing keys: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected keys: {', '.join(sorted(extra))}")
    if missing:
        return errors

    review_status = data["review_status"]
    if review_status not in {"complete", "incomplete"}:
        errors.append("review_status must be complete or incomplete")
    delivery_state = data["delivery_state"]
    if delivery_state not in {"draft", "posted"}:
        errors.append("delivery_state must be draft or posted")
    if not isinstance(data["external_posting_authorized"], bool):
        errors.append("external_posting_authorized must be boolean")
    if delivery_state == "posted" and data["external_posting_authorized"] is not True:
        errors.append("posted delivery requires external posting authority")

    for key in ("output_comments", "suppressions", "cleared", "checks", "blocking_limits", "completion_receipts"):
        if not isinstance(data[key], list):
            errors.append(f"{key} must be an array")
    if errors:
        return errors

    if review_status == "complete" and data["blocking_limits"]:
        errors.append("complete result cannot have blocking limits")
    if review_status == "incomplete" and not data["blocking_limits"]:
        errors.append("incomplete result requires at least one blocking limit")
    if any(not is_string(item) for item in data["blocking_limits"]):
        errors.append("every blocking limit must be a non-empty string")

    receipt_names: set[tuple[str, str]] = set()
    workbench_names: set[str] = set()
    file_names: set[str] = set()
    for index, receipt in enumerate(data["completion_receipts"]):
        prefix = f"completion_receipts[{index}]"
        if not isinstance(receipt, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(receipt) - {"kind", "name", "state", "limit"}:
            errors.append(f"{prefix} has unexpected keys")
        kind, name, state = receipt.get("kind"), receipt.get("name"), receipt.get("state")
        if kind not in {"changed_file", "workbench"}:
            errors.append(f"{prefix}.kind is invalid")
        if not is_string(name):
            errors.append(f"{prefix}.name must be a non-empty string")
            continue
        if state not in {"complete", "incomplete"}:
            errors.append(f"{prefix}.state is invalid")
        if state == "incomplete" and not is_string(receipt.get("limit")):
            errors.append(f"{prefix} needs a limit when incomplete")
        if review_status == "complete" and state != "complete":
            errors.append(f"{prefix} must be complete for a complete result")
        identity = (kind, name)
        if identity in receipt_names:
            errors.append(f"duplicate completion receipt: {kind} {name}")
        receipt_names.add(identity)
        if kind == "workbench":
            workbench_names.add(name)
        elif kind == "changed_file":
            file_names.add(name)

    missing_workbenches = WORKBENCHES - workbench_names
    if missing_workbenches:
        errors.append(f"missing mandatory workbenches: {', '.join(sorted(missing_workbenches))}")

    changed_files: dict[str, dict[str, Any]] = {}
    if snapshot is not None:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("changed_files"), list):
            errors.append("snapshot must contain a changed_files array")
        else:
            changed_files = {item["path"]: item for item in snapshot["changed_files"]}
            missing_files = changed_files.keys() - file_names
            extra_files = file_names - changed_files.keys()
            if missing_files:
                errors.append(f"missing changed-file receipts: {', '.join(sorted(missing_files))}")
            if extra_files:
                errors.append(f"unknown changed-file receipts: {', '.join(sorted(extra_files))}")

    issue_ids: set[str] = set()
    for index, comment in enumerate(data["output_comments"]):
        prefix = f"output_comments[{index}]"
        if not isinstance(comment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = {"issue_id", "priority", "path", "side", "line", "body"}
        allowed = required | {"pull_request"}
        if required - comment.keys():
            errors.append(f"{prefix} is missing required fields")
            continue
        if set(comment) - allowed:
            errors.append(f"{prefix} has unexpected fields")
        issue_id = comment["issue_id"]
        if not is_string(issue_id):
            errors.append(f"{prefix}.issue_id must be a non-empty string")
        elif issue_id in issue_ids:
            errors.append(f"duplicate output issue_id: {issue_id}")
        else:
            issue_ids.add(issue_id)
        if comment["priority"] not in {"P0", "P1", "P2", "P3"}:
            errors.append(f"{prefix}.priority is invalid")
        if not is_string(comment["path"]):
            errors.append(f"{prefix}.path must be a non-empty string")
        if comment["side"] not in {"LEFT", "RIGHT"}:
            errors.append(f"{prefix}.side is invalid")
        if not isinstance(comment["line"], int) or isinstance(comment["line"], bool) or comment["line"] < 1:
            errors.append(f"{prefix}.line must be a positive integer")
        if not is_string(comment["body"]):
            errors.append(f"{prefix}.body must be a non-empty string")
        if changed_files and comment.get("path") in changed_files and isinstance(comment.get("line"), int):
            ranges = changed_files[comment["path"]].get(
                "right_ranges" if comment.get("side") == "RIGHT" else "left_ranges", []
            )
            if not in_ranges(comment["line"], ranges):
                errors.append(f"{prefix} is not anchored to a changed {comment.get('side')} line")
        elif changed_files and comment.get("path") not in changed_files:
            errors.append(f"{prefix}.path is not in the changed-file snapshot")

    for index, entry in enumerate(data["cleared"]):
        prefix = f"cleared[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = {"behavior", "locator", "evidence"}
        allowed = required | {"from_candidate"}
        if required - entry.keys():
            errors.append(f"{prefix} is missing required fields")
            continue
        if set(entry) - allowed:
            errors.append(f"{prefix} has unexpected fields")
        for key in sorted(required):
            if not is_string(entry[key]):
                errors.append(f"{prefix}.{key} must be a non-empty string")
        from_candidate = entry.get("from_candidate")
        if from_candidate is not None and not is_string(from_candidate):
            errors.append(f"{prefix}.from_candidate must be a non-empty string or null")

    for index, suppression in enumerate(data["suppressions"]):
        prefix = f"suppressions[{index}]"
        if not isinstance(suppression, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = {"issue_id", "path", "side", "line", "existing_thread_id", "reason"}
        allowed = required | {"pull_request"}
        if required - suppression.keys():
            errors.append(f"{prefix} is missing required fields")
            continue
        if set(suppression) - allowed:
            errors.append(f"{prefix} has unexpected fields")
        issue_id = suppression["issue_id"]
        if not is_string(issue_id):
            errors.append(f"{prefix}.issue_id must be a non-empty string")
        elif issue_id in issue_ids:
            errors.append(f"duplicate issue_id across comments and suppressions: {issue_id}")
        else:
            issue_ids.add(issue_id)
        for key in ("path", "existing_thread_id", "reason"):
            if not is_string(suppression[key]):
                errors.append(f"{prefix}.{key} must be a non-empty string")
        if suppression["side"] not in {"LEFT", "RIGHT"}:
            errors.append(f"{prefix}.side is invalid")
        if not isinstance(suppression["line"], int) or isinstance(suppression["line"], bool) or suppression["line"] < 1:
            errors.append(f"{prefix}.line must be a positive integer")
        if changed_files and suppression.get("path") in changed_files and isinstance(suppression.get("line"), int):
            ranges = changed_files[suppression["path"]].get(
                "right_ranges" if suppression.get("side") == "RIGHT" else "left_ranges", []
            )
            if not in_ranges(suppression["line"], ranges):
                errors.append(f"{prefix} is not anchored to a changed {suppression.get('side')} line")
        elif changed_files and suppression.get("path") not in changed_files:
            errors.append(f"{prefix}.path is not in the changed-file snapshot")

    return errors


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    try:
        result = load(args.result)
        snapshot = load(args.snapshot) if args.snapshot else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    errors = validate(result, snapshot)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("review result is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
