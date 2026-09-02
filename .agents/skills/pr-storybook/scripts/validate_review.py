#!/usr/bin/env python3
"""Validate the frozen facts and authored structure of a PR Storybook bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from _review_contract import (
    AUTHORED_ID_RE,
    DIGEST_RE,
    FILE_ID_RE,
    OID_RE,
    UTC_RFC3339_RE,
    UNIT_ID_RE,
    ChangedPath,
    ContractError,
    git_output,
    inventory_arguments,
    make_file_record,
    parse_name_status,
    patch_arguments,
    repository_state,
    run_identity,
    sha256_id,
    split_file_patches,
    validate_subject_url,
)


RUN_KEYS = {"schemaVersion", "runId", "createdAt", "subject", "files", "totals"}
SUBJECT_KEYS = {"repository", "title", "url", "base", "head", "mergeBase", "patchSha256"}
FILE_KEYS = {
    "id", "path", "oldPath", "status", "isBinary", "patchSha256",
    "additions", "deletions", "units",
}
HUNK_KEYS = {"id", "kind", "header", "oldRange", "newRange", "lines"}
METADATA_KEYS = {"id", "kind", "label"}
RANGE_KEYS = {"start", "count"}
LINE_KEYS = {"kind", "oldLine", "newLine", "text"}
TOTAL_KEYS = {"files", "units", "additions", "deletions"}
BOOK_KEYS = {"schemaVersion", "runId", "title"}
SIDECAR_KEYS = {"schemaVersion", "runId", "chapter", "coverage"}
COVERAGE_REQUIRED_KEYS = {"unitId", "section", "disposition"}
COVERAGE_OPTIONAL_KEYS = {"reason"}
FINDINGS_KEYS = {"schemaVersion", "runId", "findings"}
FINDING_REQUIRED_KEYS = {
    "id", "status", "severity", "confidence", "title", "summary", "trigger",
    "impact", "fix", "source", "anchors", "evidence",
}
FINDING_OPTIONAL_KEYS = {"externalDiscussionUrl"}
ANCHOR_REQUIRED_KEYS = {"fileId", "unitId"}
ANCHOR_POSITION_KEYS = {"side", "line"}

STATUSES = {"added", "modified", "deleted", "renamed", "copied", "type-changed"}
CONFIDENCES = {"high", "medium", "low"}
FINDING_STATUSES = {"verified", "reported", "resolved", "duplicate", "rejected"}
SEVERITIES = {"P0", "P1", "P2", "P3"}
LINE_KINDS = {"context", "addition", "deletion", "note"}
DISPOSITIONS = {"displayed", "supporting", "mechanical"}
CHAPTER_RE = re.compile(r"^[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, location: str, message: str) -> None:
        self.errors.append(f"{location}: {message}")

    def exact_keys(
        self,
        value: Any,
        required: set[str],
        location: str,
        optional: set[str] | None = None,
    ) -> bool:
        if not isinstance(value, dict):
            self.error(location, "must be an object")
            return False
        optional = optional or set()
        actual = set(value)
        missing = sorted(required - actual)
        unknown = sorted(actual - required - optional)
        if missing:
            self.error(location, f"missing fields: {', '.join(missing)}")
        if unknown:
            self.error(location, f"unknown fields: {', '.join(unknown)}")
        return not missing and not unknown

    def integer(self, value: Any, location: str, minimum: int = 0) -> bool:
        if type(value) is not int or value < minimum:
            self.error(location, f"must be an integer greater than or equal to {minimum}")
            return False
        return True

    def string(self, value: Any, location: str, *, nonempty: bool = True) -> bool:
        if not isinstance(value, str) or (nonempty and not value.strip()):
            message = "must be a non-empty string" if nonempty else "must be a string"
            self.error(location, message)
            return False
        if isinstance(value, str) and "\x00" in value:
            self.error(location, "cannot contain a NUL character")
            return False
        return True

    def string_list(
        self, value: Any, location: str, *, allow_empty: bool = True
    ) -> list[str] | None:
        if not isinstance(value, list):
            self.error(location, "must be an array")
            return None
        if not allow_empty and not value:
            self.error(location, "cannot be empty")
        result: list[str] = []
        for index, item in enumerate(value):
            if self.string(item, f"{location}[{index}]"):
                result.append(item)
        if len(result) != len(set(result)):
            self.error(location, "contains duplicate values")
        return result


def _read_bytes(path: Path, validator: Validator, location: str | None = None) -> bytes | None:
    label = location or path.name
    if path.is_symlink():
        validator.error(label, "must not be a symbolic link")
        return None
    try:
        return path.read_bytes()
    except OSError as error:
        validator.error(label, f"cannot read file: {error}")
        return None


def _read_json(path: Path, validator: Validator, location: str | None = None) -> dict[str, Any] | None:
    label = location or path.name
    raw = _read_bytes(path, validator, label)
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        validator.error(label, f"invalid JSON: {error}")
        return None
    if not isinstance(value, dict):
        validator.error(label, "top-level value must be an object")
        return None
    return value


def _schema_version(value: Any, location: str, validator: Validator, expected: int) -> None:
    if type(value) is not int or value != expected:
        validator.error(location, f"must equal integer {expected}")


def _web_url(value: Any, location: str, validator: Validator, allow_empty: bool) -> None:
    if not isinstance(value, str):
        validator.error(location, "must be a string")
        return
    if not value and allow_empty:
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        validator.error(location, "must be an HTTPS URL")


def _line_for_anchor(unit: dict[str, Any], side: str, number: int) -> list[dict[str, Any]]:
    key = "oldLine" if side == "old" else "newLine"
    lines = unit.get("lines")
    if not isinstance(lines, list):
        return []
    return [line for line in lines if isinstance(line, dict) and line.get(key) == number]


def _validate_run(
    run: dict[str, Any], patch: bytes, validator: Validator
) -> tuple[set[str], dict[str, str], dict[str, dict[str, Any]], bool]:
    file_ids: set[str] = set()
    unit_to_file: dict[str, str] = {}
    units: dict[str, dict[str, Any]] = {}
    paths: set[str] = set()
    pull_request_subject = False
    if not validator.exact_keys(run, RUN_KEYS, "run.json"):
        return file_ids, unit_to_file, units, pull_request_subject

    _schema_version(run["schemaVersion"], "run.json.schemaVersion", validator, 1)
    run_id = run["runId"]
    if not isinstance(run_id, str) or not DIGEST_RE.fullmatch(run_id):
        validator.error("run.json.runId", "must be a lowercase SHA-256 ID")
    created_at = run["createdAt"]
    if not isinstance(created_at, str) or not UTC_RFC3339_RE.fullmatch(created_at):
        validator.error("run.json.createdAt", "must be a UTC RFC 3339 timestamp")

    subject = run["subject"]
    if validator.exact_keys(subject, SUBJECT_KEYS, "run.json.subject"):
        validator.string(subject["repository"], "run.json.subject.repository")
        validator.string(subject["title"], "run.json.subject.title", nonempty=False)
        if isinstance(subject["url"], str) and isinstance(subject["repository"], str):
            try:
                pull_request_subject = validate_subject_url(
                    subject["url"], subject["repository"]
                )
            except ContractError as error:
                validator.error("run.json.subject.url", str(error))
        else:
            validator.error("run.json.subject.url", "must be a string")
        for field in ("base", "head", "mergeBase"):
            if not isinstance(subject[field], str) or not OID_RE.fullmatch(subject[field]):
                validator.error(f"run.json.subject.{field}", "must be a lowercase Git commit ID")
        actual_patch_digest = sha256_id(patch)
        if subject["patchSha256"] != actual_patch_digest:
            validator.error("run.json.subject.patchSha256", "does not match diff.patch")
        if not isinstance(subject["patchSha256"], str) or not DIGEST_RE.fullmatch(
            subject["patchSha256"]
        ):
            validator.error("run.json.subject.patchSha256", "must be a lowercase SHA-256 ID")

    try:
        expected_run_id = run_identity(run)
    except (TypeError, ValueError) as error:
        validator.error("run.json.runId", f"cannot compute identity: {error}")
    else:
        if run_id != expected_run_id:
            validator.error("run.json.runId", "does not match the canonical run content")

    try:
        file_patches = split_file_patches(patch)
    except ContractError as error:
        validator.error("diff.patch", str(error))
        file_patches = []
    files = run["files"]
    if not isinstance(files, list):
        validator.error("run.json.files", "must be an array")
        files = []
    elif not files:
        validator.error("run.json.files", "must be a non-empty array")
    if len(files) != len(file_patches):
        validator.error(
            "run.json.files",
            f"has {len(files)} records but diff.patch has {len(file_patches)} file patches",
        )

    for index, file_record in enumerate(files):
        location = f"run.json.files[{index}]"
        if not validator.exact_keys(file_record, FILE_KEYS, location):
            continue
        file_id = file_record["id"]
        if not isinstance(file_id, str) or not FILE_ID_RE.fullmatch(file_id):
            validator.error(f"{location}.id", "must be a lowercase file content ID")
        elif file_id in file_ids:
            validator.error(f"{location}.id", "is duplicated")
        else:
            file_ids.add(file_id)
        path = file_record["path"]
        if validator.string(path, f"{location}.path"):
            if path in paths:
                validator.error(f"{location}.path", "is duplicated")
            paths.add(path)
        old_path = file_record["oldPath"]
        if old_path is not None:
            validator.string(old_path, f"{location}.oldPath")
        status = file_record["status"]
        if not isinstance(status, str) or status not in STATUSES:
            validator.error(f"{location}.status", "has an unsupported status")
        if type(file_record["isBinary"]) is not bool:
            validator.error(f"{location}.isBinary", "must be a Boolean")
        patch_digest = file_record["patchSha256"]
        if not isinstance(patch_digest, str) or not DIGEST_RE.fullmatch(patch_digest):
            validator.error(f"{location}.patchSha256", "must be a lowercase SHA-256 ID")
        validator.integer(file_record["additions"], f"{location}.additions")
        validator.integer(file_record["deletions"], f"{location}.deletions")

        file_units = file_record["units"]
        if not isinstance(file_units, list) or not file_units:
            validator.error(f"{location}.units", "must be a non-empty array")
            file_units = []
        for unit_index, unit in enumerate(file_units):
            unit_location = f"{location}.units[{unit_index}]"
            if not isinstance(unit, dict):
                validator.error(unit_location, "must be an object")
                continue
            kind = unit.get("kind")
            expected_keys = HUNK_KEYS if kind == "hunk" else METADATA_KEYS if kind == "metadata" else set()
            if not expected_keys:
                validator.error(f"{unit_location}.kind", "must be hunk or metadata")
                continue
            if not validator.exact_keys(unit, expected_keys, unit_location):
                continue
            unit_id = unit["id"]
            if not isinstance(unit_id, str) or not UNIT_ID_RE.fullmatch(unit_id):
                validator.error(f"{unit_location}.id", "must be a lowercase unit content ID")
            elif unit_id in unit_to_file:
                validator.error(f"{unit_location}.id", "is duplicated")
            else:
                unit_to_file[unit_id] = file_id
                units[unit_id] = unit
            if kind == "metadata":
                validator.string(unit["label"], f"{unit_location}.label")
                continue
            validator.string(unit["header"], f"{unit_location}.header")
            for side in ("oldRange", "newRange"):
                range_value = unit[side]
                if validator.exact_keys(range_value, RANGE_KEYS, f"{unit_location}.{side}"):
                    validator.integer(range_value["start"], f"{unit_location}.{side}.start")
                    validator.integer(range_value["count"], f"{unit_location}.{side}.count")
            lines = unit["lines"]
            if not isinstance(lines, list):
                validator.error(f"{unit_location}.lines", "must be an array")
                continue
            for line_index, line in enumerate(lines):
                line_location = f"{unit_location}.lines[{line_index}]"
                if not validator.exact_keys(line, LINE_KEYS, line_location):
                    continue
                if not isinstance(line["kind"], str) or line["kind"] not in LINE_KINDS:
                    validator.error(f"{line_location}.kind", "has an unknown line kind")
                for side in ("oldLine", "newLine"):
                    if line[side] is not None:
                        validator.integer(line[side], f"{line_location}.{side}", minimum=1)
                validator.string(line["text"], f"{line_location}.text", nonempty=False)

        if index < len(file_patches):
            try:
                expected_file = make_file_record(
                    ChangedPath(status, old_path, path), file_patches[index]
                )
            except (ContractError, KeyError, TypeError, ValueError) as error:
                validator.error(location, f"cannot compare with diff.patch: {error}")
            else:
                if file_record != expected_file:
                    validator.error(location, "does not match its exact diff.patch bytes")

    totals = run["totals"]
    if validator.exact_keys(totals, TOTAL_KEYS, "run.json.totals"):
        for name in TOTAL_KEYS:
            validator.integer(totals[name], f"run.json.totals.{name}")
        calculated = {
            "files": len(files),
            "units": sum(
                len(file_record.get("units", []))
                for file_record in files
                if isinstance(file_record, dict) and isinstance(file_record.get("units"), list)
            ),
            "additions": sum(
                file_record.get("additions", 0)
                for file_record in files
                if isinstance(file_record, dict) and type(file_record.get("additions")) is int
            ),
            "deletions": sum(
                file_record.get("deletions", 0)
                for file_record in files
                if isinstance(file_record, dict) and type(file_record.get("deletions")) is int
            ),
        }
        if totals != calculated:
            validator.error("run.json.totals", "does not match the file inventory")
    return file_ids, unit_to_file, units, pull_request_subject


def _validate_book(book: dict[str, Any], run_id: Any, validator: Validator) -> None:
    validator.exact_keys(book, BOOK_KEYS, "book.json")
    if not BOOK_KEYS.issubset(book):
        return
    _schema_version(book["schemaVersion"], "book.json.schemaVersion", validator, 1)
    if book["runId"] != run_id:
        validator.error("book.json.runId", "does not match run.json")
    validator.string(book["title"], "book.json.title")


def _validate_chapters(
    bundle: Path,
    run_id: Any,
    units: dict[str, dict[str, Any]],
    validator: Validator,
) -> None:
    chapters_dir = bundle / "chapters"
    if chapters_dir.is_symlink():
        validator.error("chapters", "must not be a symbolic link")
        return
    if not chapters_dir.is_dir():
        validator.error("chapters", "directory is missing")
        return
    try:
        entries = sorted(chapters_dir.iterdir(), key=lambda path: path.name)
    except OSError as error:
        validator.error("chapters", f"cannot read directory: {error}")
        return

    mdx_by_slug: dict[str, Path] = {}
    sidecar_by_slug: dict[str, Path] = {}
    for entry in entries:
        name = entry.name
        if name.endswith(".evidence.json"):
            sidecar_by_slug[name.removesuffix(".evidence.json")] = entry
        elif name.endswith(".mdx"):
            mdx_by_slug[name.removesuffix(".mdx")] = entry
        else:
            validator.error(f"chapters/{name}", "is not a chapter or evidence sidecar")

    if not mdx_by_slug:
        validator.error("chapters", "must contain at least one numbered MDX chapter")
    for index, slug in enumerate(sorted(mdx_by_slug), start=1):
        expected_number = f"{index:02d}"
        if slug[:2] != expected_number:
            validator.error(
                f"chapters/{slug}.mdx",
                f"chapter number must be {expected_number}",
            )
    for slug in sorted(set(mdx_by_slug) | set(sidecar_by_slug)):
        if not CHAPTER_RE.fullmatch(slug):
            validator.error(
                f"chapters/{slug}",
                "must use a two-digit number and a lowercase hyphenated name",
            )
        if slug not in mdx_by_slug:
            validator.error(f"chapters/{slug}.mdx", "is missing")
        if slug not in sidecar_by_slug:
            validator.error(f"chapters/{slug}.evidence.json", "is missing")

    assigned: dict[str, list[str]] = {unit_id: [] for unit_id in units}
    for slug, mdx_path in sorted(mdx_by_slug.items()):
        mdx_location = f"chapters/{mdx_path.name}"
        raw = _read_bytes(mdx_path, validator, mdx_location)
        if raw is not None:
            try:
                source = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                validator.error(mdx_location, f"must be UTF-8 text: {error}")
            else:
                if not source.strip():
                    validator.error(mdx_location, "cannot be empty")

        sidecar_path = sidecar_by_slug.get(slug)
        if sidecar_path is None:
            continue
        sidecar_location = f"chapters/{sidecar_path.name}"
        sidecar = _read_json(sidecar_path, validator, sidecar_location)
        if sidecar is None:
            continue
        validator.exact_keys(sidecar, SIDECAR_KEYS, sidecar_location)
        if not SIDECAR_KEYS.issubset(sidecar):
            continue
        _schema_version(
            sidecar["schemaVersion"], f"{sidecar_location}.schemaVersion", validator, 1
        )
        if sidecar["runId"] != run_id:
            validator.error(f"{sidecar_location}.runId", "does not match run.json")
        if sidecar["chapter"] != slug:
            validator.error(f"{sidecar_location}.chapter", "does not match its filename")
        coverage = sidecar["coverage"]
        if not isinstance(coverage, list):
            validator.error(f"{sidecar_location}.coverage", "must be an array")
            continue
        for index, record in enumerate(coverage):
            record_location = f"{sidecar_location}.coverage[{index}]"
            if not validator.exact_keys(
                record,
                COVERAGE_REQUIRED_KEYS,
                record_location,
                optional=COVERAGE_OPTIONAL_KEYS,
            ):
                continue
            unit_id = record["unitId"]
            if not isinstance(unit_id, str) or not UNIT_ID_RE.fullmatch(unit_id):
                validator.error(f"{record_location}.unitId", "must be a lowercase unit content ID")
            elif unit_id not in units:
                validator.error(f"{record_location}.unitId", "references an unknown unit")
            else:
                assigned[unit_id].append(record_location)
            validator.string(record["section"], f"{record_location}.section")
            disposition = record["disposition"]
            if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
                validator.error(
                    f"{record_location}.disposition",
                    "must be displayed, supporting, or mechanical",
                )
                continue
            has_reason = "reason" in record
            if disposition == "displayed" and has_reason:
                validator.error(record_location, "displayed coverage must not have a reason")
            elif disposition != "displayed" and not has_reason:
                validator.error(record_location, f"{disposition} coverage needs a reason")
            elif has_reason:
                reason_location = f"{record_location}.reason"
                if validator.string(record["reason"], reason_location) and len(record["reason"].strip()) > 240:
                    validator.error(reason_location, "must contain at most 240 characters")

    for slug in sorted(set(sidecar_by_slug) - set(mdx_by_slug)):
        _read_json(sidecar_by_slug[slug], validator, f"chapters/{sidecar_by_slug[slug].name}")
    for unit_id, owners in sorted(assigned.items()):
        if not owners:
            validator.error("chapters", f"review unit {unit_id!r} has no owner or disposition")
        elif len(owners) > 1:
            validator.error(
                "chapters",
                f"review unit {unit_id!r} has {len(owners)} owners or dispositions",
            )


def _validate_findings(
    findings_document: dict[str, Any],
    run_id: Any,
    file_ids: set[str],
    unit_to_file: dict[str, str],
    units: dict[str, dict[str, Any]],
    validator: Validator,
) -> None:
    if not validator.exact_keys(findings_document, FINDINGS_KEYS, "findings.json"):
        return
    _schema_version(findings_document["schemaVersion"], "findings.json.schemaVersion", validator, 2)
    if findings_document["runId"] != run_id:
        validator.error("findings.json.runId", "does not match run.json")
    findings = findings_document["findings"]
    if not isinstance(findings, list):
        validator.error("findings.json.findings", "must be an array")
        return
    known_finding_ids: set[str] = set()
    for index, finding in enumerate(findings):
        location = f"findings.json.findings[{index}]"
        if not validator.exact_keys(
            finding, FINDING_REQUIRED_KEYS, location, optional=FINDING_OPTIONAL_KEYS
        ):
            continue
        finding_id = finding["id"]
        if not isinstance(finding_id, str) or not AUTHORED_ID_RE.fullmatch(finding_id):
            validator.error(
                f"{location}.id",
                "must start with a lowercase letter and contain only lowercase letters, digits, or hyphens",
            )
        elif finding_id in known_finding_ids:
            validator.error(f"{location}.id", "is duplicated")
        else:
            known_finding_ids.add(finding_id)
        status = finding["status"]
        if not isinstance(status, str) or status not in FINDING_STATUSES:
            validator.error(f"{location}.status", "has an unknown status")
        if not isinstance(finding["severity"], str) or finding["severity"] not in SEVERITIES:
            validator.error(f"{location}.severity", "has an unknown severity")
        if not isinstance(finding["confidence"], str) or finding["confidence"] not in CONFIDENCES:
            validator.error(f"{location}.confidence", "has an unknown confidence")
        for field in ("title", "summary", "trigger", "impact", "fix", "source"):
            validator.string(finding[field], f"{location}.{field}")
        validator.string_list(
            finding["evidence"],
            f"{location}.evidence",
            allow_empty=status != "verified",
        )
        anchors = finding["anchors"]
        if not isinstance(anchors, list):
            validator.error(f"{location}.anchors", "must be an array")
            anchors = []
        valid_anchor_count = 0
        anchor_values: set[tuple[Any, ...]] = set()
        for anchor_index, anchor in enumerate(anchors):
            anchor_location = f"{location}.anchors[{anchor_index}]"
            if not validator.exact_keys(
                anchor,
                ANCHOR_REQUIRED_KEYS,
                anchor_location,
                optional=ANCHOR_POSITION_KEYS,
            ):
                continue
            file_id = anchor["fileId"]
            unit_id = anchor["unitId"]
            side = anchor.get("side")
            line_number = anchor.get("line")
            identity = (file_id, unit_id, side, line_number)
            try:
                duplicated = identity in anchor_values
            except TypeError:
                duplicated = False
            if duplicated:
                validator.error(anchor_location, "is duplicated")
            else:
                try:
                    anchor_values.add(identity)
                except TypeError:
                    pass
            if not isinstance(file_id, str):
                validator.error(f"{anchor_location}.fileId", "must be a string")
                continue
            if not isinstance(unit_id, str):
                validator.error(f"{anchor_location}.unitId", "must be a string")
                continue
            if file_id not in file_ids:
                validator.error(f"{anchor_location}.fileId", "references an unknown file")
            if unit_id not in units:
                validator.error(f"{anchor_location}.unitId", "references an unknown unit")
                continue
            if unit_to_file.get(unit_id) != file_id:
                validator.error(anchor_location, "unit does not belong to the referenced file")
            unit = units[unit_id]
            if unit.get("kind") == "metadata":
                if "side" in anchor or "line" in anchor:
                    validator.error(anchor_location, "a metadata anchor must omit side and line")
                else:
                    valid_anchor_count += 1
                continue
            if "side" not in anchor or "line" not in anchor:
                validator.error(anchor_location, "a hunk anchor needs side and line")
                continue
            if not isinstance(side, str) or side not in {"old", "new"}:
                validator.error(f"{anchor_location}.side", "must be old or new")
                continue
            if not validator.integer(line_number, f"{anchor_location}.line", minimum=1):
                continue
            matching_lines = _line_for_anchor(unit, side, line_number)
            if not matching_lines:
                validator.error(anchor_location, "does not identify a line in the referenced unit")
                continue
            changed_kind = "deletion" if side == "old" else "addition"
            if any(line.get("kind") == changed_kind for line in matching_lines):
                valid_anchor_count += 1
        if status == "verified" and valid_anchor_count == 0:
            validator.error(location, "a verified finding needs a valid evidence anchor")
        if "externalDiscussionUrl" in finding:
            _web_url(
                finding["externalDiscussionUrl"],
                f"{location}.externalDiscussionUrl",
                validator,
                False,
            )


def _validate_repository_provenance(
    run: dict[str, Any], patch: bytes, repository: Path, validator: Validator
) -> None:
    subject = run.get("subject")
    files = run.get("files")
    if not isinstance(subject, dict) or not isinstance(files, list):
        validator.error("repository", "cannot verify malformed run.json Git facts")
        return
    commit_fields = ("base", "head", "mergeBase")
    if any(
        not isinstance(subject.get(field), str) or not OID_RE.fullmatch(subject[field])
        for field in commit_fields
    ):
        validator.error("repository", "cannot verify invalid Git commit IDs")
        return
    base = subject["base"]
    head = subject["head"]
    merge_base = subject["mergeBase"]
    repository = repository.resolve()
    try:
        for field, commit_id in (("base", base), ("head", head), ("mergeBase", merge_base)):
            resolved = git_output(
                repository,
                ["rev-parse", "--verify", "--end-of-options", f"{commit_id}^{{commit}}"],
            ).decode("ascii", errors="strict").strip()
            if resolved != commit_id:
                validator.error(
                    f"run.json.subject.{field}",
                    "does not resolve to the declared commit in the repository",
                )
        merge_bases = [
            line
            for line in git_output(repository, ["merge-base", "--all", base, head])
            .decode("ascii", errors="strict")
            .splitlines()
            if line
        ]
        if merge_bases != [merge_base]:
            validator.error(
                "run.json.subject.mergeBase",
                "does not match the repository's single best merge base",
            )
        if git_output(repository, patch_arguments(merge_base, head)) != patch:
            validator.error("diff.patch", "does not match the declared repository revisions")
        repository_inventory = parse_name_status(
            git_output(repository, inventory_arguments(merge_base, head))
        )
    except (ContractError, UnicodeError) as error:
        validator.error("repository", f"Git provenance validation failed: {error}")
        return

    declared_inventory: list[ChangedPath] = []
    well_formed = True
    for index, file_record in enumerate(files):
        if not isinstance(file_record, dict):
            well_formed = False
            continue
        status = file_record.get("status")
        old_path = file_record.get("oldPath")
        path = file_record.get("path")
        if (
            not isinstance(status, str)
            or (old_path is not None and not isinstance(old_path, str))
            or not isinstance(path, str)
        ):
            well_formed = False
            validator.error(
                f"run.json.files[{index}]",
                "cannot compare malformed path metadata with the repository",
            )
            continue
        declared_inventory.append(ChangedPath(status, old_path, path))
    if well_formed and declared_inventory != repository_inventory:
        validator.error(
            "run.json.files",
            "ordered status, old-path, or new-path metadata does not match the repository",
        )


def _validate_current_revisions(
    run: dict[str, Any],
    current_head: str | None,
    current_base: str | None,
    validator: Validator,
    *,
    required: bool,
) -> None:
    subject = run.get("subject")
    frozen_head = subject.get("head") if isinstance(subject, dict) else None
    frozen_base = subject.get("base") if isinstance(subject, dict) else None
    for name, current, frozen in (
        ("current-head", current_head, frozen_head),
        ("current-base", current_base, frozen_base),
    ):
        if current is None:
            if required:
                validator.error(name, "is required for repository validation of a pull request")
            continue
        if not isinstance(current, str) or not OID_RE.fullmatch(current):
            validator.error(name, "must be a lowercase 40- or 64-character Git ID")
        elif current != frozen:
            validator.error(name, f"does not match the frozen {name.removeprefix('current-')}; the review is stale")


def validate_bundle(
    bundle: Path,
    repository: Path | None = None,
    current_head: str | None = None,
    current_base: str | None = None,
) -> list[str]:
    validator = Validator()
    patch = _read_bytes(bundle / "diff.patch", validator)
    if patch is None:
        patch = b""
    run = _read_json(bundle / "run.json", validator)
    book = _read_json(bundle / "book.json", validator)
    findings = _read_json(bundle / "findings.json", validator)
    if run is None:
        return validator.errors

    file_ids, unit_to_file, units, pull_request_subject = _validate_run(run, patch, validator)
    if repository is not None:
        try:
            state_before = repository_state(repository)
        except (ContractError, OSError, UnicodeError) as error:
            validator.error("repository", f"cannot capture initial repository state: {error}")
        else:
            _validate_repository_provenance(run, patch, repository, validator)
            try:
                state_after = repository_state(repository)
            except (ContractError, OSError, UnicodeError) as error:
                validator.error("repository", f"cannot capture final repository state: {error}")
            else:
                if state_after != state_before:
                    validator.error(
                        "repository",
                        "review validation changed the repository or checkout state",
                    )
    _validate_current_revisions(
        run,
        current_head,
        current_base,
        validator,
        required=repository is not None and pull_request_subject,
    )
    if book is not None:
        _validate_book(book, run.get("runId"), validator)
    if findings is not None:
        _validate_findings(
            findings,
            run.get("runId"),
            file_ids,
            unit_to_file,
            units,
            validator,
        )
    _validate_chapters(bundle, run.get("runId"), units, validator)
    return validator.errors


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one PR Storybook bundle.")
    parser.add_argument("bundle", type=Path, help="PR Storybook bundle directory")
    parser.add_argument(
        "--repository",
        type=Path,
        help="local checkout or bare repository used to verify Git provenance",
    )
    parser.add_argument(
        "--current-head",
        help="optional current commit ID used to reject a stale frozen review",
    )
    parser.add_argument(
        "--current-base",
        help="optional current base commit ID used to reject a stale frozen review",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    repository = arguments.repository.resolve() if arguments.repository is not None else None
    errors = validate_bundle(
        arguments.bundle.resolve(),
        repository=repository,
        current_head=arguments.current_head,
        current_base=arguments.current_base,
    )
    if errors:
        print(f"invalid PR Storybook bundle ({len(errors)} error(s))", file=sys.stderr)
        for error in errors[:40]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > 40:
            print(f"- {len(errors) - 40} more error(s)", file=sys.stderr)
        return 1
    run = _read_json(arguments.bundle.resolve() / "run.json", Validator())
    run_id = run.get("runId", "unknown") if run else "unknown"
    print(f"valid frozen PR Storybook data and sidecars: {run_id}")
    print("MDX: not checked here; the PR Storybook renderer validates MDX")
    if repository is None:
        print("provenance: offline integrity only; Git metadata was not independently verified")
    else:
        print(f"provenance: Git metadata verified against {repository}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
