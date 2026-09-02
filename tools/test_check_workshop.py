#!/usr/bin/env python3
"""Focused tests for workshop integrity boundaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from check_workshop import (
    ROOT,
    check_harness_discoverability,
    check_release_safeguards,
    is_within_root,
    is_working_output,
    markdown_targets,
)


class RootBoundaryTests(unittest.TestCase):
    def test_accepts_workshop_path(self) -> None:
        self.assertTrue(is_within_root(ROOT / "README.md"))

    def test_rejects_parent_escape(self) -> None:
        self.assertFalse(is_within_root(ROOT / ".." / "outside.md"))

    def test_rejects_absolute_host_path(self) -> None:
        self.assertFalse(is_within_root(Path("/etc/passwd")))


class MarkdownTargetTests(unittest.TestCase):
    def test_extracts_nested_inline_destination(self) -> None:
        self.assertEqual(markdown_targets("[label](notes/a(b).md)"), ["notes/a(b).md"])

    def test_extracts_reference_definition(self) -> None:
        self.assertEqual(markdown_targets("[label][ref]\n\n[ref]: notes/file.md"), ["notes/file.md"])

    def test_extracts_raw_html_target(self) -> None:
        self.assertEqual(markdown_targets('<a href="notes/file.md">label</a>'), ["notes/file.md"])


class WorkingOutputTests(unittest.TestCase):
    def test_skips_review_artifacts(self) -> None:
        self.assertTrue(is_working_output(ROOT / "review-work" / "pr-reviews" / "report.md"))

    def test_keeps_authored_text(self) -> None:
        self.assertFalse(is_working_output(ROOT / "library" / "glossary.md"))


class ReleaseSafeguardTests(unittest.TestCase):
    def check(self, files: dict[str, str], *, tracked: set[str] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            errors: list[str] = []
            tracked_paths = None if tracked is None else {Path(name) for name in tracked}
            check_release_safeguards(errors, root, tracked_paths)
            return errors

    def test_scans_the_candidate_tree_but_ignores_review_work_and_caches(self) -> None:
        errors = self.check(
            {
                "README.md": "portable text\n",
                ".git/config": "/" + "Users/reviewer/private\n",
                "review-work/report.md": "/" + "Users/reviewer/private\n",
                "node_modules/package.md": "/" + "Users/reviewer/private\n",
                "cache/report.md": "/" + "Users/reviewer/private\n",
            }
        )
        self.assertEqual(errors, [])

    def test_rejects_absolute_personal_path_in_portable_text(self) -> None:
        errors = self.check({"README.md": "See /" + "Users/reviewer/project.\n"})
        self.assertTrue(any("machine-local path" in error for error in errors))

    def test_scans_source_files_for_personal_paths(self) -> None:
        errors = self.check({"scripts/build.py": 'ROOT = "/' + 'home/reviewer/project"\n'})
        self.assertTrue(any("machine-local path" in error for error in errors))

    def test_rejects_absolute_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "host-link").symlink_to("/etc/passwd")
            errors: list[str] = []
            check_release_safeguards(errors, root)
            self.assertTrue(any("absolute symlink" in error for error in errors))

    def test_rejects_relative_symlink_that_escapes_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            (root / "escape-link").symlink_to("../outside.txt")
            errors: list[str] = []
            check_release_safeguards(errors, root)
            self.assertTrue(any("outside candidate tree" in error for error in errors))

    def test_rejects_stale_gist_url(self) -> None:
        errors = self.check(
            {"README.md": "https://" + "gist.github.com/reviewer/abcdef\n"}
        )
        self.assertTrue(any("stale Gist URL" in error for error in errors))

    def test_rejects_removed_delivery_path_reference(self) -> None:
        errors = self.check({"README.md": "See deliv" + "ery/done/checklist.md.\n"})
        self.assertTrue(any("removed delivery path" in error for error in errors))

    def test_rejects_stale_human_review_skill_name(self) -> None:
        errors = self.check({"README.md": "human-review-" + "code-change\n"})
        self.assertTrue(any("stale human review skill name" in error for error in errors))

    def test_rejects_tracked_private_classification(self) -> None:
        manifest = json.dumps({"cl" + "ass": "pri" + "vate founding corpus"}) + "\n"
        errors = self.check(
            {"library/manifest.json": manifest},
            tracked={"library/manifest.json"},
        )
        self.assertTrue(any("tracked private source classification" in error for error in errors))

    def test_rejects_tracked_private_raw_source_path_and_file(self) -> None:
        errors = self.check(
            {
                "README.md": "library/" + "raw/source.md\n",
                "library/" + "raw/source.md": "private source\n",
            },
            tracked={"README.md", "library/" + "raw/source.md"},
        )
        self.assertTrue(any("tracked private raw source path" in error for error in errors))
        self.assertTrue(any("tracked private raw source file" in error for error in errors))


class HarnessDiscoverabilityTests(unittest.TestCase):
    def build(self, root: Path, *, skills_link: bool, claude_md: bool) -> None:
        (root / ".agents" / "skills" / "demo").mkdir(parents=True)
        (root / ".agents" / "skills" / "demo" / "SKILL.md").write_text("---\nname: demo\n---\n")
        (root / "AGENTS.md").write_text("# Workshop\n")
        if skills_link:
            (root / ".claude").mkdir()
            (root / ".claude" / "skills").symlink_to(Path("..") / ".agents" / "skills")
        if claude_md:
            (root / "CLAUDE.md").symlink_to("AGENTS.md")

    def test_passes_when_both_links_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, skills_link=True, claude_md=True)
            errors: list[str] = []
            check_harness_discoverability(errors, root)
            self.assertEqual(errors, [])

    def test_reports_unmounted_skills_and_missing_claude_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, skills_link=False, claude_md=False)
            errors: list[str] = []
            check_harness_discoverability(errors, root)
            self.assertEqual(len(errors), 2)
            self.assertIn("missing .claude/skills", errors[0])
            self.assertIn("demo", errors[0])
            self.assertIn("missing CLAUDE.md", errors[1])

    def test_reports_skills_link_pointing_elsewhere(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, skills_link=False, claude_md=True)
            (root / "other-skills").mkdir()
            (root / ".claude").mkdir()
            (root / ".claude" / "skills").symlink_to(Path("..") / "other-skills")
            errors: list[str] = []
            check_harness_discoverability(errors, root)
            self.assertTrue(any("not .agents/skills" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
