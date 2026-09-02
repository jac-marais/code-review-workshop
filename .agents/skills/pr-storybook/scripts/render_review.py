#!/usr/bin/env python3
"""Render a validated PR Storybook bundle with the bundled Node runtime."""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from _review_contract import ContractError, path_is_within_roots, reviewed_repository_roots


SKILL_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = Path(__file__).resolve().with_name("validate_review.py")
RUNTIME_PATH = SKILL_ROOT / "assets" / "review-book" / "build.mjs"
OID_PATTERN = r"[0-9a-f]{40}(?:[0-9a-f]{24})?"


class RenderError(RuntimeError):
    """Report one clear renderer failure."""


class BundleValidationError(RenderError):
    """Report a bundle that failed Python or Node validation."""


def validate_bundle(
    bundle_dir: Path,
    repository: Path,
    current_head: str | None = None,
    current_base: str | None = None,
    validator_path: Path = VALIDATOR_PATH,
) -> None:
    """Run the canonical bundle validator before the renderer reads the bundle."""

    if not validator_path.is_file():
        raise RenderError(f"Validator is missing: {validator_path}")
    command = [
        sys.executable,
        str(validator_path),
        str(bundle_dir),
        "--repository",
        str(repository),
    ]
    if current_head is not None:
        command.extend(["--current-head", current_head])
    if current_base is not None:
        command.extend(["--current-base", current_base])
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode == 0:
        return
    detail = result.stderr.strip() or result.stdout.strip() or "No validation detail was returned."
    raise BundleValidationError(f"Bundle validation failed:\n{detail}")


def run_runtime(
    bundle_dir: Path,
    output_dir: Path,
    runtime_path: Path = RUNTIME_PATH,
) -> None:
    """Invoke the only PR Storybook authoring and rendering runtime."""

    if not runtime_path.is_file():
        raise RenderError(f"PR Storybook runtime is missing: {runtime_path}")
    result = subprocess.run(
        [
            "node",
            str(runtime_path),
            "--bundle",
            str(bundle_dir),
            "--output",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return
    detail = result.stderr.strip() or result.stdout.strip() or "No validation detail was returned."
    raise BundleValidationError(f"PR Storybook runtime rejected the bundle:\n{detail}")


def ensure_output_outside_repository(output_path: Path, repository: Path) -> None:
    """Reject output in the reviewed worktree or its Git data."""

    try:
        roots = reviewed_repository_roots(repository)
    except (ContractError, UnicodeError) as error:
        raise RenderError(f"Cannot resolve reviewed repository roots: {error}") from error
    containing_root = path_is_within_roots(output_path, roots)
    if containing_root is not None:
        raise RenderError(
            f"--output must be outside the reviewed repository: {containing_root}"
        )


def ensure_output_is_bundle_site(output_path: Path, bundle_dir: Path) -> None:
    """Keep generated files in the one replaceable site directory."""

    expected = (bundle_dir / "site").resolve()
    if output_path != expected:
        raise RenderError(f"--output must equal the bundle site directory: {expected}")


def _visible_patch(patch: bytes) -> str:
    try:
        text = patch.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        text = "".join(
            chr(byte)
            if byte in {0x09, 0x0A, 0x0D} or 0x20 <= byte <= 0x7E and byte != 0x5C
            else f"\\x{byte:02X}"
            for byte in patch
        )
    controls = {
        "\u061c", "\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\u202a",
        "\u202b", "\u202c", "\u202d", "\u202e", "\u2060", "\u2066", "\u2067",
        "\u2068", "\u2069", "\ufeff",
    }
    return "".join(f"\\u{ord(character):04X}" if character in controls else character for character in text)


def raw_patch_page(patch: bytes, validation_error: str) -> str:
    """Create a static page that cannot execute bundle content."""

    escaped_error = html.escape(_visible_patch(validation_error.encode("utf-8")), quote=True)
    escaped_patch = html.escape(_visible_patch(patch), quote=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
  <title>PR Storybook validation failed</title>
  <style>
    body {{ margin: 0; background: #101214; color: #e7e9ec; font: 16px/1.55 system-ui, sans-serif; }}
    main {{ max-width: 96rem; margin: auto; padding: 2rem; }}
    .notice {{ border-left: .3rem solid #e3a008; background: #1b1f23; padding: 1rem; }}
    pre {{ overflow: auto; padding: 1rem; background: #090b0d; border: 1px solid #30363d; white-space: pre; }}
  </style>
</head>
<body>
  <main>
    <h1>Only the raw patch is available</h1>
    <p>The PR Storybook did not pass validation.</p>
    <p class="notice">{escaped_error}</p>
    <pre><code>{escaped_patch}</code></pre>
  </main>
</body>
</html>
"""


def publish_fallback(output_dir: Path, page: str) -> bool:
    """Publish a fallback only when no prior site exists."""

    if output_dir.exists() or output_dir.is_symlink():
        return False
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_dir.mkdir()
    except FileExistsError:
        return False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".index.html.", suffix=".tmp", dir=output_dir
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(page)
            temporary_path.replace(output_dir / "index.html")
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    except BaseException:
        try:
            output_dir.rmdir()
        except OSError:
            pass
        raise
    return True


def write_raw_fallback(
    bundle_dir: Path, output_dir: Path, validation_error: BundleValidationError
) -> bool:
    if output_dir.exists() or output_dir.is_symlink():
        return False
    patch_path = bundle_dir / "diff.patch"
    try:
        if patch_path.is_symlink():
            raise OSError("diff.patch is a symbolic link")
        patch = patch_path.read_bytes()
    except OSError as error:
        raise RenderError(f"Cannot read diff.patch for the safe fallback: {error}") from error
    return publish_fallback(output_dir, raw_patch_page(patch, str(validation_error)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a validated MDX PR Storybook as a static site."
    )
    parser.add_argument("bundle_dir", type=Path, help="directory that contains the PR Storybook")
    parser.add_argument(
        "--repository",
        required=True,
        type=Path,
        help="local checkout or bare repository used to verify Git provenance",
    )
    parser.add_argument("--output", required=True, type=Path, help="static site output directory")
    parser.add_argument(
        "--current-head",
        help="optional current commit ID used to reject a stale frozen review",
    )
    parser.add_argument(
        "--current-base",
        help="optional current base commit ID used to reject a stale frozen review",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle_dir = args.bundle_dir.expanduser().resolve()
    repository = args.repository.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()

    try:
        if not bundle_dir.is_dir():
            raise RenderError(f"Bundle directory does not exist: {bundle_dir}")
        if args.current_head is not None and not re.fullmatch(OID_PATTERN, args.current_head):
            raise RenderError("--current-head must be a lowercase 40- or 64-character Git ID")
        if args.current_base is not None and not re.fullmatch(OID_PATTERN, args.current_base):
            raise RenderError("--current-base must be a lowercase 40- or 64-character Git ID")
        ensure_output_is_bundle_site(output_dir, bundle_dir)
        ensure_output_outside_repository(output_dir, repository)
        try:
            validate_bundle(bundle_dir, repository, args.current_head, args.current_base)
            run_runtime(bundle_dir, output_dir)
        except BundleValidationError as validation_error:
            fallback_written = write_raw_fallback(bundle_dir, output_dir, validation_error)
            print(f"render_review: {validation_error}", file=sys.stderr)
            if fallback_written:
                print(
                    f"render_review: wrote safe raw-patch-only site: {output_dir / 'index.html'}",
                    file=sys.stderr,
                )
            else:
                print(
                    f"render_review: preserved the prior site without changes: {output_dir}",
                    file=sys.stderr,
                )
            return 1
    except RenderError as error:
        print(f"render_review: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"render_review: Cannot write {output_dir}: {error}", file=sys.stderr)
        return 1

    print(output_dir / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
