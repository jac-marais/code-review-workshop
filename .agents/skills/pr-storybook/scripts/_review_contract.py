#!/usr/bin/env python3
"""Shared deterministic data rules for human review bundles."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse


DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FILE_ID_RE = re.compile(r"^file:[0-9a-f]{64}$")
UNIT_ID_RE = re.compile(r"^unit:[0-9a-f]{64}$")
AUTHORED_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
OID_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
UTC_RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
HUNK_HEADER_RE = re.compile(
    rb"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*?)(?:\n)?$"
)
DIFF_START_RE = re.compile(rb"(?m)^diff --git ")
PULL_REQUEST_PATH_RE = re.compile(r"^/([^/]+/[^/]+)/pull/([1-9][0-9]*)/?$")

STATUS_NAMES = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
    "T": "type-changed",
    "U": "unmerged",
    "X": "unknown",
    "B": "pairing-broken",
}


class ContractError(ValueError):
    """Report data that cannot satisfy the review bundle contract."""


def git_output(repository: Path, arguments: Sequence[str]) -> bytes:
    """Run one read-only Git command with external diff behavior disabled by callers."""

    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_CONFIG_KEY_") or name.startswith("GIT_CONFIG_VALUE_"):
            environment.pop(name, None)
    for name in (
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_COUNT",
        "GIT_DIR",
        "GIT_EXTERNAL_DIFF",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_WORK_TREE",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "GCM_INTERACTIVE": "Never",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ALLOW_PROTOCOL": "file",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
            "PAGER": "cat",
        }
    )
    command = [
        "git",
        "--no-optional-locks",
        "--no-replace-objects",
        "-c",
        "color.ui=false",
        "-c",
        "core.quotePath=true",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "credential.interactive=never",
        "-c",
        "maintenance.auto=false",
        "-c",
        "gc.auto=0",
        "-C",
        str(repository),
        *arguments,
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
    except OSError as error:
        raise ContractError(f"cannot run Git: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ContractError(detail or f"Git exited with status {result.returncode}")
    return result.stdout


def _add_state_part(digest: Any, label: bytes, value: bytes) -> None:
    digest.update(len(label).to_bytes(8, "big"))
    digest.update(label)
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def _untracked_state(repository: Path, paths: bytes) -> bytes:
    """Return an exact digest for visible untracked paths without following links."""

    worktree_text = git_output(repository, ["rev-parse", "--show-toplevel"]).decode(
        "utf-8", errors="strict"
    ).strip()
    worktree = Path(worktree_text).resolve()
    digest = hashlib.sha256()
    for raw_path in paths.split(b"\0"):
        if not raw_path:
            continue
        try:
            relative_path = raw_path.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ContractError("non-UTF-8 Git paths are not supported") from error
        candidate = worktree / relative_path
        try:
            metadata = candidate.lstat()
        except OSError as error:
            raise ContractError(
                f"cannot inspect untracked path {relative_path!r}: {error}"
            ) from error
        _add_state_part(digest, b"path", raw_path)
        _add_state_part(digest, b"mode", str(stat.S_IFMT(metadata.st_mode)).encode("ascii"))
        _add_state_part(
            digest,
            b"permissions",
            f"{stat.S_IMODE(metadata.st_mode):04o}".encode("ascii"),
        )
        if stat.S_ISREG(metadata.st_mode):
            file_digest = hashlib.sha256()
            try:
                with candidate.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        file_digest.update(chunk)
            except OSError as error:
                raise ContractError(
                    f"cannot read untracked path {relative_path!r}: {error}"
                ) from error
            _add_state_part(digest, b"content", file_digest.digest())
        elif stat.S_ISLNK(metadata.st_mode):
            try:
                target = os.readlink(candidate)
            except OSError as error:
                raise ContractError(
                    f"cannot read untracked link {relative_path!r}: {error}"
                ) from error
            _add_state_part(digest, b"target", os.fsencode(target))
        else:
            _add_state_part(digest, b"special", str(metadata.st_size).encode("ascii"))
    return digest.digest()


def repository_state(repository: Path) -> str:
    """Return a stable digest of the visible Git and checkout state."""

    repository = repository.resolve()
    digest = hashlib.sha256()
    probes = (
        (b"head", ["rev-parse", "--verify", "HEAD"]),
        (b"head-name", ["rev-parse", "--symbolic-full-name", "HEAD"]),
        (
            b"refs",
            ["for-each-ref", "--format=%(refname)%00%(objectname)%00%(symref)"],
        ),
        (b"index", ["ls-files", "--stage", "-z"]),
    )
    for label, arguments in probes:
        _add_state_part(digest, label, git_output(repository, arguments))

    bare = git_output(repository, ["rev-parse", "--is-bare-repository"]).strip()
    _add_state_part(digest, b"bare", bare)
    if bare == b"false":
        status_bytes = git_output(
            repository,
            ["status", "--porcelain=v2", "--branch", "--no-ahead-behind", "-z", "--untracked-files=all"],
        )
        worktree_diff = git_output(
            repository,
            ["diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-renames", "--"],
        )
        index_diff = git_output(
            repository,
            ["diff", "--cached", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-renames", "--"],
        )
        untracked_paths = git_output(
            repository, ["ls-files", "--others", "--exclude-standard", "-z"]
        )
        _add_state_part(digest, b"status", status_bytes)
        _add_state_part(digest, b"worktree-diff", worktree_diff)
        _add_state_part(digest, b"index-diff", index_diff)
        _add_state_part(digest, b"untracked", _untracked_state(repository, untracked_paths))
    elif bare != b"true":
        raise ContractError("Git returned an invalid bare-repository state")
    return digest.hexdigest()


def reviewed_repository_roots(repository: Path) -> set[Path]:
    """Return resolved worktree and Git-data roots for output exclusion."""

    repository = repository.resolve()
    git_dir_text = git_output(repository, ["rev-parse", "--absolute-git-dir"]).decode(
        "utf-8", errors="strict"
    ).strip()
    roots = {Path(git_dir_text).resolve()}
    is_bare = git_output(repository, ["rev-parse", "--is-bare-repository"]).decode(
        "ascii", errors="strict"
    ).strip()
    if is_bare == "false":
        worktree_text = git_output(repository, ["rev-parse", "--show-toplevel"]).decode(
            "utf-8", errors="strict"
        ).strip()
        roots.add(Path(worktree_text).resolve())
    elif is_bare != "true":
        raise ContractError("Git returned an invalid bare-repository state")

    common_text = git_output(repository, ["rev-parse", "--git-common-dir"]).decode(
        "utf-8", errors="strict"
    ).strip()
    common_dir = Path(common_text)
    if not common_dir.is_absolute():
        common_dir = repository / common_dir
    roots.add(common_dir.resolve())
    return roots


def path_is_within_roots(path: Path, roots: set[Path]) -> Path | None:
    """Return the containing root after symlink resolution, if one exists."""

    resolved_path = path.resolve()
    for root in roots:
        if resolved_path == root or resolved_path.is_relative_to(root):
            return root
    return None


@dataclass(frozen=True)
class ChangedPath:
    status: str
    old_path: str | None
    path: str


def canonical_bytes(value: Any) -> bytes:
    """Return the one JSON encoding used for content identities."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_id(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def validate_subject_url(url: str, repository_name: str) -> bool:
    """Validate one subject URL and report whether it names a pull request."""

    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ContractError("subject URL must be an HTTPS URL")
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ContractError("subject URL has an invalid host or port") from error
    match = PULL_REQUEST_PATH_RE.fullmatch(parsed.path)
    if match is None:
        return False
    if (
        parsed.scheme != "https"
        or hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ContractError(
            "pull-request subject URL must be https://host/owner/repo/pull/N without credentials, a port, a query, or a fragment"
        )
    if match.group(1) != repository_name:
        raise ContractError("pull-request subject URL does not match the run repository")
    return True


def file_identity(
    *, status: str, old_path: str | None, path: str, patch_sha256: str
) -> str:
    identity = {
        "oldPath": old_path,
        "patchSha256": patch_sha256,
        "path": path,
        "status": status,
    }
    return f"file:{hashlib.sha256(canonical_bytes(identity)).hexdigest()}"


def hunk_identity(
    *,
    file_id: str,
    old_range: dict[str, int],
    new_range: dict[str, int],
    hunk_bytes: bytes,
) -> str:
    identity = {
        "fileId": file_id,
        "hunkSha256": sha256_id(hunk_bytes),
        "kind": "hunk",
        "newRange": new_range,
        "oldRange": old_range,
    }
    return f"unit:{hashlib.sha256(canonical_bytes(identity)).hexdigest()}"


def metadata_identity(*, file_id: str, patch_sha256: str) -> str:
    identity = {
        "fileId": file_id,
        "kind": "metadata",
        "patchSha256": patch_sha256,
    }
    return f"unit:{hashlib.sha256(canonical_bytes(identity)).hexdigest()}"


def run_identity(run: dict[str, Any]) -> str:
    body = {key: value for key, value in run.items() if key not in {"runId", "createdAt"}}
    return sha256_id(canonical_bytes(body))


def split_file_patches(patch: bytes) -> list[bytes]:
    """Split a normal two-tree Git patch without changing its bytes."""

    starts = [match.start() for match in DIFF_START_RE.finditer(patch)]
    if not starts:
        if patch:
            raise ContractError("diff.patch has data before its first file header")
        return []
    if starts[0] != 0:
        raise ContractError("diff.patch has data before its first file header")
    starts.append(len(patch))
    return [patch[starts[index] : starts[index + 1]] for index in range(len(starts) - 1)]


def parse_name_status(raw: bytes) -> list[ChangedPath]:
    """Parse the NUL-delimited output from `git diff --name-status -z`."""

    def path_text(value: bytes) -> str:
        try:
            return value.decode("utf-8", errors="strict")
        except UnicodeError as error:
            raise ContractError("non-UTF-8 Git paths are not supported") from error

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    result: list[ChangedPath] = []
    index = 0
    while index < len(fields):
        try:
            token = fields[index].decode("ascii", errors="strict")
        except UnicodeError as error:
            raise ContractError("Git returned a non-ASCII file status") from error
        index += 1
        if not token or token[0] not in STATUS_NAMES:
            raise ContractError(f"Git returned an unsupported file status {token!r}")
        status_code = token[0]
        if status_code in {"R", "C"}:
            if index + 1 >= len(fields):
                raise ContractError("Git returned an incomplete renamed or copied path")
            old_path = path_text(fields[index])
            path = path_text(fields[index + 1])
            index += 2
        else:
            if index >= len(fields):
                raise ContractError("Git returned an incomplete changed path")
            path = path_text(fields[index])
            index += 1
            old_path = None if status_code == "A" else path
        result.append(ChangedPath(STATUS_NAMES[status_code], old_path, path))
    return result


def patch_arguments(merge_base: str, head: str) -> list[str]:
    """Return the canonical safe Git arguments used to create diff.patch."""

    return [
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "--find-renames",
        "--find-copies",
        merge_base,
        head,
        "--",
    ]


def inventory_arguments(merge_base: str, head: str) -> list[str]:
    """Return the Git arguments used to verify ordered file metadata."""

    return [
        "diff",
        "--name-status",
        "-z",
        "--no-ext-diff",
        "--no-textconv",
        "--find-renames",
        "--find-copies",
        merge_base,
        head,
        "--",
    ]


def _text(raw: bytes) -> str:
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "".join(
            chr(byte)
            if byte == 0x0A or 0x20 <= byte <= 0x7E and byte != 0x5C
            else f"\\x{byte:02X}"
            for byte in raw
        )


def _without_line_ending(raw: bytes) -> bytes:
    return raw[:-1] if raw.endswith(b"\n") else raw


def parse_hunks(file_patch: bytes, file_id: str) -> tuple[list[dict[str, Any]], int, int]:
    """Parse ordinary unified hunks and preserve exact hunk bytes for IDs."""

    lines = file_patch.splitlines(keepends=True)
    hunk_indexes = [index for index, line in enumerate(lines) if line.startswith(b"@@ ")]
    if any(line.startswith(b"@@@ ") for line in lines):
        raise ContractError("combined diff hunks are not supported")

    units: list[dict[str, Any]] = []
    additions = 0
    deletions = 0
    for offset, line_index in enumerate(hunk_indexes):
        raw_header = lines[line_index]
        header_match = HUNK_HEADER_RE.match(raw_header)
        if not header_match:
            raise ContractError(f"invalid unified diff hunk header: {_text(raw_header).rstrip()}")
        old_start = int(header_match.group(1))
        old_count = int(header_match.group(2) or b"1")
        new_start = int(header_match.group(3))
        new_count = int(header_match.group(4) or b"1")
        end_index = hunk_indexes[offset + 1] if offset + 1 < len(hunk_indexes) else len(lines)
        hunk_lines = lines[line_index:end_index]
        hunk_bytes = b"".join(hunk_lines)
        old_line = old_start
        new_line = new_start
        parsed_lines: list[dict[str, Any]] = []
        seen_old = 0
        seen_new = 0

        for raw_line in hunk_lines[1:]:
            if raw_line.startswith(b" "):
                parsed_lines.append(
                    {
                        "kind": "context",
                        "oldLine": old_line,
                        "newLine": new_line,
                        "text": _text(_without_line_ending(raw_line[1:])),
                    }
                )
                old_line += 1
                new_line += 1
                seen_old += 1
                seen_new += 1
            elif raw_line.startswith(b"-"):
                parsed_lines.append(
                    {
                        "kind": "deletion",
                        "oldLine": old_line,
                        "newLine": None,
                        "text": _text(_without_line_ending(raw_line[1:])),
                    }
                )
                old_line += 1
                seen_old += 1
                deletions += 1
            elif raw_line.startswith(b"+"):
                parsed_lines.append(
                    {
                        "kind": "addition",
                        "oldLine": None,
                        "newLine": new_line,
                        "text": _text(_without_line_ending(raw_line[1:])),
                    }
                )
                new_line += 1
                seen_new += 1
                additions += 1
            elif raw_line.startswith(b"\\"):
                marker = _without_line_ending(raw_line[1:]).lstrip(b" ")
                parsed_lines.append(
                    {
                        "kind": "note",
                        "oldLine": None,
                        "newLine": None,
                        "text": _text(marker),
                    }
                )
            else:
                raise ContractError("a hunk contains a line without a unified diff marker")

        if seen_old != old_count or seen_new != new_count:
            raise ContractError(
                "hunk line counts do not match its header "
                f"(old {seen_old}/{old_count}, new {seen_new}/{new_count})"
            )

        old_range = {"start": old_start, "count": old_count}
        new_range = {"start": new_start, "count": new_count}
        units.append(
            {
                "id": hunk_identity(
                    file_id=file_id,
                    old_range=old_range,
                    new_range=new_range,
                    hunk_bytes=hunk_bytes,
                ),
                "kind": "hunk",
                "header": _text(_without_line_ending(raw_header)),
                "oldRange": old_range,
                "newRange": new_range,
                "lines": parsed_lines,
            }
        )

    return units, additions, deletions


def is_binary_patch(file_patch: bytes) -> bool:
    return b"\nGIT binary patch\n" in file_patch or bool(
        re.search(rb"(?m)^Binary files .* differ(?:\n|$)", file_patch)
    )


def metadata_change_label(changed: ChangedPath, file_patch: bytes, binary: bool) -> str | None:
    """Describe material file metadata that needs its own review unit."""

    changes: list[str] = []
    if changed.status == "renamed":
        changes.append("rename")
    elif changed.status == "copied":
        changes.append("copy")
    elif changed.status == "type-changed":
        changes.append("type change")
    if re.search(
        rb"(?m)^(?:old mode|new mode|new file mode|deleted file mode) [0-7]+$",
        file_patch,
    ):
        changes.append("file mode change")
    if binary:
        changes.append("binary change")
    if not changes:
        return None
    return " and ".join(changes).capitalize()


def make_file_record(changed: ChangedPath, file_patch: bytes) -> dict[str, Any]:
    patch_sha256 = sha256_id(file_patch)
    file_id = file_identity(
        status=changed.status,
        old_path=changed.old_path,
        path=changed.path,
        patch_sha256=patch_sha256,
    )
    units, additions, deletions = parse_hunks(file_patch, file_id)
    binary = is_binary_patch(file_patch)
    metadata_label = metadata_change_label(changed, file_patch, binary)
    if metadata_label is not None or not units:
        units.append(
            {
                "id": metadata_identity(file_id=file_id, patch_sha256=patch_sha256),
                "kind": "metadata",
                "label": metadata_label or "Metadata-only change",
            }
        )
    return {
        "id": file_id,
        "path": changed.path,
        "oldPath": changed.old_path,
        "status": changed.status,
        "isBinary": binary,
        "patchSha256": patch_sha256,
        "additions": additions,
        "deletions": deletions,
        "units": units,
    }
