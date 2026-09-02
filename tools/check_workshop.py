#!/usr/bin/env python3
"""Run portable integrity checks for the code review workshop."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "library" / "raw"
# Generated review output can quote machine paths and target-repository prose.
# It is not part of a portable workshop release.
WORKING_DIRS = {
    ".git",
    "review-work",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "cache",
}
REFERENCE_DEFINITION = re.compile(
    r"(?m)^[ \t]{0,3}\[([^\]]+)\]:[ \t]*(<[^>]+>|\S+)"
)
HTML_TARGET = re.compile(r"(?i)\b(?:href|src)[ \t]*=[ \t]*(['\"])(.*?)\1")
LOCAL_MACHINE_PATH = re.compile(
    r"(?:/" r"Users/|/" r"home/|/private/" r"var/|/var/" r"folders/|~" r"/|"
    r"\b[A-Za-z]:[\\/](?:Users|Documents|Desktop|Temp)[\\/])"
)
PLACEHOLDER = re.compile(r"(?:PROJECT_NAME|FIRST_MILESTONE_TITLE|REPLACE_WITH_|\bTODO\b)")
GIST_URL = re.compile(r"https?://(?:www\.)?gist\.github\.com/\S+", re.IGNORECASE)
DELIVERY_PATH = re.compile(r"(?<![A-Za-z0-9_.-])(?:\.\.?/)?deliv" r"ery/")
PRIVATE_CLASSIFICATION = re.compile(
    r"(?:\"(?:class|redistribution)\"\s*:\s*\"[^\"]*\bprivate\b|"
    r"(?:class|redistribution)\s*:\s*private\b)",
    re.IGNORECASE,
)
RAW_SOURCE_PATH = re.compile(
    r"(?<![A-Za-z0-9_.-])(?:\.\.?/)?library/" r"raw(?:/|\b)"
)
STALE_HUMAN_REVIEW_NAME = "human-review-" "code-change"
GENERATED_TEMPLATE_LINKS = {
    "01-cynic.md",
    "02-skeptic.md",
    "03-nyaya.md",
    "04-confucian.md",
    "05-stoic.md",
    "synthesis.md",
}


def is_raw(path: Path) -> bool:
    return path.is_relative_to(RAW_ROOT)


def is_working_output(path: Path) -> bool:
    return any(part in WORKING_DIRS for part in path.parts)


def is_within_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
    except ValueError:
        return False
    return True


def iter_candidate_paths(root: Path) -> list[Path]:
    """Return the real candidate tree without generated or VCS output."""
    paths: list[Path] = []
    for directory, directories, files in os.walk(root, followlinks=False):
        current = Path(directory)
        directories[:] = [
            name for name in directories if not is_working_output(current / name)
        ]
        for name in files:
            path = current / name
            if not is_working_output(path):
                paths.append(path)
        for name in directories:
            path = current / name
            if path.is_symlink():
                paths.append(path)
    return sorted(paths)


def read_portable_text(path: Path) -> str | None:
    """Read a UTF-8 candidate without treating binary files as release text."""
    if path.is_symlink() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def git_tracked_paths(root: Path) -> set[Path]:
    """Return tracked paths when the candidate tree is a Git repository."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        return set()
    paths = {Path(name) for name in result.stdout.decode("utf-8").split("\0") if name}
    return {path for path in paths if (root / path).exists() or (root / path).is_symlink()}


def check_release_safeguards(
    errors: list[str], root: Path | None = None, tracked_paths: set[Path] | None = None
) -> None:
    """Reject local, stale, and private material from a public release."""
    candidate_root = root or ROOT
    candidates = iter_candidate_paths(candidate_root)
    tracked = tracked_paths if tracked_paths is not None else git_tracked_paths(candidate_root)

    for path in candidates:
        relative = path.relative_to(candidate_root)
        if path.is_symlink():
            target = os.readlink(path)
            if os.path.isabs(target):
                errors.append(f"absolute symlink in candidate tree: {relative}")
            elif not is_within(candidate_root, path.resolve()):
                errors.append(f"symlink outside candidate tree: {relative}")
            continue

        text = read_portable_text(path)
        if text is None:
            continue
        if LOCAL_MACHINE_PATH.search(text):
            errors.append(f"machine-local path in portable text: {relative}")
        if GIST_URL.search(text):
            errors.append(f"stale Gist URL in candidate tree: {relative}")
        if relative != Path(".gitignore") and DELIVERY_PATH.search(text):
            errors.append(f"reference to removed delivery path: {relative}")
        if STALE_HUMAN_REVIEW_NAME in text:
            errors.append(f"stale human review skill name: {relative}")
        if relative in tracked and PRIVATE_CLASSIFICATION.search(text):
            errors.append(f"tracked private source classification: {relative}")
        if relative in tracked and RAW_SOURCE_PATH.search(text):
            errors.append(f"tracked private raw source path: {relative}")

    for relative in sorted(tracked):
        if relative.parts[:2] == ("library", "raw"):
            errors.append(f"tracked private raw source file: {relative}")


def is_within(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def destination(value: str) -> str:
    value = value.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character.isspace():
            return value[:index]
    return value


def markdown_targets(text: str) -> list[str]:
    """Extract inline, reference-definition, and raw-HTML link targets."""
    targets: list[str] = []
    cursor = 0
    while True:
        start = text.find("](", cursor)
        if start < 0:
            break
        index = start + 2
        content_start = index
        depth = 1
        escaped = False
        while index < len(text):
            character = text[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    targets.append(destination(text[content_start:index]))
                    index += 1
                    break
            index += 1
        cursor = max(index, start + 2)

    targets.extend(destination(match.group(2)) for match in REFERENCE_DEFINITION.finditer(text))
    targets.extend(match.group(2).strip() for match in HTML_TARGET.finditer(text))
    return targets


def check_json(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if is_working_output(path):
            continue
        if not is_within_root(path):
            errors.append(f"out-of-workshop JSON file: {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON: {path.relative_to(ROOT)}: {exc}")


def check_markdown(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if is_working_output(path):
            continue
        if not is_within_root(path):
            errors.append(f"out-of-workshop Markdown file: {path.relative_to(ROOT)}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"unreadable Markdown: {path.relative_to(ROOT)}: {exc}")
            continue

        if not is_raw(path):
            if "—" in text or "–" in text:
                errors.append(f"dash character in authored text: {path.relative_to(ROOT)}")
            if PLACEHOLDER.search(text):
                errors.append(f"unresolved template placeholder: {path.relative_to(ROOT)}")

        for target in markdown_targets(text):
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0].strip("<>")
            if not target:
                continue
            linked = (path.parent / unquote(target)).resolve()
            if not is_within_root(linked):
                errors.append(
                    f"out-of-workshop local link: {path.relative_to(ROOT)} -> {target}"
                )
                continue
            if path.parent.name == "templates" and Path(target).name in GENERATED_TEMPLATE_LINKS:
                continue
            if not linked.exists():
                errors.append(
                    f"broken local link: {path.relative_to(ROOT)} -> {target}"
                )


def check_harness_discoverability(errors: list[str], root: Path | None = None) -> None:
    """Confirm a harness can actually load the guidance and the mounted skills.

    A workshop whose skills and instructions are invisible to the agent passes
    every other check here while doing nothing, so this runs first among equals.
    """
    ROOT = root or globals()["ROOT"]
    skills = ROOT / ".agents" / "skills"
    if not skills.is_dir():
        errors.append("no .agents/skills directory: nothing is mounted")
        return

    mounted = sorted(p.name for p in skills.iterdir() if (p / "SKILL.md").is_file())
    if not mounted:
        errors.append("no skill under .agents/skills has a SKILL.md")

    claude_skills = ROOT / ".claude" / "skills"
    if not claude_skills.exists():
        errors.append(
            "missing .claude/skills: Claude Code reads skills from there, so "
            f"{', '.join(mounted) or 'every mounted skill'} is undiscoverable. "
            "Link it with: ln -s ../.agents/skills .claude/skills"
        )
    elif claude_skills.resolve() != skills.resolve():
        errors.append(
            f".claude/skills resolves to {claude_skills.resolve()}, not .agents/skills, "
            "so a harness sees a different skill set than the workshop mounts"
        )

    agents_md = ROOT / "AGENTS.md"
    claude_md = ROOT / "CLAUDE.md"
    if not agents_md.is_file():
        errors.append("missing AGENTS.md: the workshop states no authority or routing")
    elif not claude_md.exists():
        errors.append(
            "missing CLAUDE.md: Claude Code loads that name, so AGENTS.md never "
            "reaches the agent. Link it with: ln -s AGENTS.md CLAUDE.md"
        )
    elif claude_md.resolve() != agents_md.resolve():
        errors.append("CLAUDE.md does not resolve to AGENTS.md, so the two can drift apart")


def main() -> int:
    errors: list[str] = []
    check_harness_discoverability(errors)
    check_release_safeguards(errors)
    check_json(errors)
    check_markdown(errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("workshop integrity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
