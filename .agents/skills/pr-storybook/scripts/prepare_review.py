#!/usr/bin/env python3
"""Create deterministic facts and safe starter files for one Git change."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from _review_contract import (
    ContractError,
    OID_RE,
    UTC_RFC3339_RE,
    git_output,
    inventory_arguments,
    make_file_record,
    parse_name_status,
    path_is_within_roots,
    patch_arguments,
    repository_state,
    reviewed_repository_roots,
    run_identity,
    sha256_id,
    split_file_patches,
    validate_subject_url,
)


class PreparationError(RuntimeError):
    pass


def _resolve_commit(repository: Path, revision: str) -> str:
    if not revision or revision.startswith("-") or "\x00" in revision:
        raise PreparationError("a revision is empty or unsafe")
    resolved = git_output(
        repository,
        ["rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}"],
    ).decode("ascii", errors="strict").strip()
    if not OID_RE.fullmatch(resolved):
        raise PreparationError(f"Git returned an invalid commit ID for {revision!r}")
    return resolved


def _merge_base(repository: Path, base: str, head: str) -> str:
    output = git_output(repository, ["merge-base", "--all", base, head])
    candidates = [line for line in output.decode("ascii", errors="strict").splitlines() if line]
    if len(candidates) != 1:
        raise PreparationError(
            f"the revisions have {len(candidates)} best merge bases; exactly one is required"
        )
    if not OID_RE.fullmatch(candidates[0]):
        raise PreparationError("Git returned an invalid merge-base ID")
    return candidates[0]


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _ensure_repository_unchanged(repository: Path, expected_state: str) -> None:
    try:
        current_state = repository_state(repository)
    except (ContractError, OSError, UnicodeError) as error:
        raise PreparationError(
            f"cannot confirm that repository state stayed unchanged: {error}"
        ) from error
    if current_state != expected_state:
        raise PreparationError("review preparation changed the repository or checkout state")


def prepare(
    *,
    repository: Path,
    base_revision: str,
    head_revision: str,
    output: Path,
    repository_name: str,
    title: str,
    url: str,
    created_at: str,
) -> dict[str, object]:
    if not repository_name.strip():
        raise PreparationError("repository name cannot be empty")
    if not UTC_RFC3339_RE.fullmatch(created_at):
        raise PreparationError("created-at must be a UTC RFC 3339 timestamp")
    try:
        validate_subject_url(url, repository_name)
    except ContractError as error:
        raise PreparationError(str(error)) from error

    repository = repository.resolve()
    output = output.resolve()
    state_before = repository_state(repository)
    try:
        containing_root = path_is_within_roots(output, reviewed_repository_roots(repository))
        if containing_root is not None:
            raise PreparationError(
                f"output must be outside the reviewed repository: {containing_root}"
            )
        if output.exists():
            raise PreparationError(f"output already exists: {output}")

        base = _resolve_commit(repository, base_revision)
        head = _resolve_commit(repository, head_revision)
        merge_base = _merge_base(repository, base, head)
        patch = git_output(repository, patch_arguments(merge_base, head))
        changed_paths = parse_name_status(
            git_output(repository, inventory_arguments(merge_base, head))
        )
        file_patches = split_file_patches(patch)
        if len(changed_paths) != len(file_patches):
            raise PreparationError(
                "Git file inventory and raw patch disagree "
                f"({len(changed_paths)} paths, {len(file_patches)} patches)"
            )
        if not changed_paths:
            raise PreparationError("the selected revisions have no changed files")

        files = [
            make_file_record(changed, file_patch)
            for changed, file_patch in zip(changed_paths, file_patches)
        ]
    except Exception as error:
        try:
            _ensure_repository_unchanged(repository, state_before)
        except PreparationError as state_error:
            raise state_error from error
        raise
    _ensure_repository_unchanged(repository, state_before)
    unit_count = sum(len(file["units"]) for file in files)
    additions = sum(int(file["additions"]) for file in files)
    deletions = sum(int(file["deletions"]) for file in files)
    effective_title = title or f"Review of {repository_name}"
    run: dict[str, object] = {
        "schemaVersion": 1,
        "runId": "",
        "createdAt": created_at,
        "subject": {
            "repository": repository_name,
            "title": effective_title,
            "url": url,
            "base": base,
            "head": head,
            "mergeBase": merge_base,
            "patchSha256": sha256_id(patch),
        },
        "files": files,
        "totals": {
            "files": len(files),
            "units": unit_count,
            "additions": additions,
            "deletions": deletions,
        },
    }
    run["runId"] = run_identity(run)

    book = {
        "schemaVersion": 1,
        "runId": run["runId"],
        "title": effective_title,
    }
    findings = {"schemaVersion": 2, "runId": run["runId"], "findings": []}
    starter_chapter = "# Complete this review\n\nReplace this text with the first chapter.\n"
    starter_evidence = {
        "schemaVersion": 1,
        "runId": run["runId"],
        "chapter": "01-review",
        "coverage": [],
    }

    temporary_output: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = Path(
            tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent)
        )
        chapters = temporary_output / "chapters"
        chapters.mkdir()
        (temporary_output / "diff.patch").write_bytes(patch)
        _write_json(temporary_output / "run.json", run)
        _write_json(temporary_output / "book.json", book)
        _write_json(temporary_output / "findings.json", findings)
        (chapters / "01-review.mdx").write_text(starter_chapter, encoding="utf-8")
        _write_json(chapters / "01-review.evidence.json", starter_evidence)
        if output.exists():
            raise PreparationError(f"output appeared during preparation: {output}")
        temporary_output.rename(output)
        temporary_output = None
    except (OSError, TypeError, ValueError) as error:
        raise PreparationError(f"cannot publish review bundle: {error}") from error
    finally:
        if temporary_output is not None:
            shutil.rmtree(temporary_output, ignore_errors=True)
    return run


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze one Git change into a deterministic human-review bundle."
    )
    parser.add_argument("repository", type=Path, help="local checkout or bare Git repository")
    parser.add_argument("base", help="base revision")
    parser.add_argument("head", help="head revision")
    parser.add_argument("bundle", type=Path, help="new output bundle directory")
    parser.add_argument("--repository-name", help="stable repository label")
    parser.add_argument("--title", default="", help="change title")
    parser.add_argument("--url", default="", help="change URL")
    parser.add_argument(
        "--created-at",
        help="UTC RFC 3339 timestamp for reproducible tests; defaults to the current time",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    repository = arguments.repository.resolve()
    repository_name = arguments.repository_name or repository.name
    created_at = arguments.created_at or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    try:
        run = prepare(
            repository=repository,
            base_revision=arguments.base,
            head_revision=arguments.head,
            output=arguments.bundle.resolve(),
            repository_name=repository_name,
            title=arguments.title,
            url=arguments.url,
            created_at=created_at,
        )
    except (ContractError, PreparationError, UnicodeError, ValueError) as error:
        print(f"prepare_review: {error}", file=sys.stderr)
        return 1
    print(f"created review bundle {arguments.bundle} ({run['runId']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
