#!/usr/bin/env python3
"""Tests for local Git snapshot capture."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from capture_review_snapshot import build_snapshot


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class CaptureSnapshotTests(unittest.TestCase):
    def test_captures_exact_committed_range_and_changed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            run(repo, "init", "-b", "main")
            run(repo, "config", "user.name", "Fixture")
            run(repo, "config", "user.email", "fixture@example.test")
            source = repo / "source.ts"
            source.write_text("export const value = 1;\n", encoding="utf-8")
            run(repo, "add", "source.ts")
            run(repo, "commit", "-m", "base")
            source.write_text("export const value = 2;\n", encoding="utf-8")
            run(repo, "add", "source.ts")
            run(repo, "commit", "-m", "head")

            snapshot = build_snapshot(repo, "HEAD~1", "HEAD", False)

            self.assertEqual(snapshot["mode"], "committed_range")
            self.assertEqual(len(snapshot["merge_bases"]), 1)
            self.assertEqual(snapshot["changed_files"][0]["path"], "source.ts")
            self.assertEqual(snapshot["changed_files"][0]["right_ranges"], [[1, 1]])


if __name__ == "__main__":
    unittest.main()
