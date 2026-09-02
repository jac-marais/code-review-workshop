from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
import render_review  # noqa: E402


class RenderReviewTests(unittest.TestCase):
    def test_validator_receives_repository_and_current_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            completed = subprocess.CompletedProcess([], 0, stdout="valid\n", stderr="")
            head = "1" * 40
            base = "2" * 40
            with mock.patch.object(
                render_review.subprocess, "run", return_value=completed
            ) as run_validator:
                render_review.validate_bundle(
                    root / "bundle",
                    root / "repository",
                    current_head=head,
                    current_base=base,
                )

            command = run_validator.call_args.args[0]
            self.assertEqual(
                command[-7:],
                [
                    str(root / "bundle"),
                    "--repository",
                    str(root / "repository"),
                    "--current-head",
                    head,
                    "--current-base",
                    base,
                ],
            )

    def test_validator_failure_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            validator = root / "validator.py"
            validator.write_text(
                "import sys\nprint('unknown unit reference', file=sys.stderr)\nraise SystemExit(1)\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                render_review.BundleValidationError, "unknown unit reference"
            ):
                render_review.validate_bundle(
                    root / "bundle", root / "repository", validator_path=validator
                )

    def test_runtime_uses_the_reusable_cli_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            runtime = root / "build.mjs"
            runtime.write_text("", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0, stdout="built\n", stderr="")
            with mock.patch.object(
                render_review.subprocess, "run", return_value=completed
            ) as run_node:
                render_review.run_runtime(
                    root / "bundle", root / "site", runtime_path=runtime
                )

            self.assertEqual(
                run_node.call_args.args[0],
                [
                    "node",
                    str(runtime),
                    "--bundle",
                    str(root / "bundle"),
                    "--output",
                    str(root / "site"),
                ],
            )

    def test_main_validates_before_it_runs_the_node_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            bundle.mkdir()
            output = root / "site"
            calls: list[str] = []

            def validate(*_args: object) -> None:
                calls.append("validate")

            def runtime(*_args: object) -> None:
                calls.append("runtime")

            with mock.patch.object(render_review, "validate_bundle", side_effect=validate), mock.patch.object(
                render_review, "run_runtime", side_effect=runtime
            ), mock.patch.object(render_review, "ensure_output_outside_repository"):
                result = render_review.main(
                    [str(bundle), "--repository", str(root / "repository"), "--output", str(bundle / "site")]
                )

            self.assertEqual(result, 0)
            self.assertEqual(calls, ["validate", "runtime"])

    def test_python_validation_failure_writes_only_a_safe_raw_patch_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            bundle.mkdir()
            patch = b"diff --git a/x b/x\n+</pre><script>alert(1)</script>\n"
            (bundle / "diff.patch").write_bytes(patch)
            output = bundle / "site"
            with mock.patch.object(
                render_review,
                "validate_bundle",
                side_effect=render_review.BundleValidationError("invalid book.json"),
            ), mock.patch.object(
                render_review, "ensure_output_outside_repository"
            ), mock.patch.object(render_review, "run_runtime") as runtime:
                result = render_review.main(
                    [str(bundle), "--repository", str(root / "repository"), "--output", str(output)]
                )

            self.assertEqual(result, 1)
            page = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Only the raw patch is available", page)
            self.assertIn("&lt;/pre&gt;&lt;script&gt;alert(1)&lt;/script&gt;", page)
            self.assertNotIn("</pre><script>alert(1)</script>", page)
            self.assertEqual(list(output.iterdir()), [output / "index.html"])
            runtime.assert_not_called()

    def test_node_validation_failure_preserves_the_prior_site_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "diff.patch").write_bytes(b"diff --git a/x b/x\n")
            output = bundle / "site"
            (output / "assets").mkdir(parents=True)
            (output / "index.html").write_bytes(b"previous\x00site")
            (output / "assets" / "book.css").write_bytes(b"previous css\n")
            before = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            stderr = StringIO()
            with mock.patch.object(render_review, "validate_bundle"), mock.patch.object(
                render_review,
                "run_runtime",
                side_effect=render_review.BundleValidationError("unsafe MDX"),
            ), mock.patch.object(
                render_review, "ensure_output_outside_repository"
            ), mock.patch.object(render_review.sys, "stderr", stderr):
                result = render_review.main(
                    [str(bundle), "--repository", str(root / "repository"), "--output", str(output)]
                )

            self.assertEqual(result, 1)
            after = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)
            self.assertIn("preserved the prior site without changes", stderr.getvalue())

    def test_existing_output_survives_when_fallback_cannot_read_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            bundle.mkdir()
            output = bundle / "site"
            output.mkdir()
            existing = output / "index.html"
            existing.write_text("existing", encoding="utf-8")
            with mock.patch.object(
                render_review,
                "validate_bundle",
                side_effect=render_review.BundleValidationError("invalid bundle"),
            ), mock.patch.object(render_review, "ensure_output_outside_repository"):
                result = render_review.main(
                    [str(bundle), "--repository", str(root / "repository"), "--output", str(output)]
                )

            self.assertEqual(result, 1)
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing")

    def test_main_requires_the_bundle_site_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            chapters = bundle / "chapters"
            chapters.mkdir(parents=True)
            for output in (bundle, root / "site", chapters / "site"):
                with self.subTest(output=output), mock.patch.object(
                    render_review, "validate_bundle"
                ) as validator, mock.patch.object(
                    render_review, "ensure_output_outside_repository"
                ):
                    result = render_review.main(
                        [str(bundle), "--repository", str(root / "repository"), "--output", str(output)]
                    )
                self.assertEqual(result, 1)
                validator.assert_not_called()

    def test_main_rejects_invalid_current_head_before_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            bundle.mkdir()
            with mock.patch.object(render_review, "validate_bundle") as validator, mock.patch.object(
                render_review, "ensure_output_outside_repository"
            ):
                result = render_review.main(
                    [
                        str(bundle), "--repository", str(root / "repository"),
                        "--output", str(bundle / "site"), "--current-head", "HEAD",
                    ]
                )
            self.assertEqual(result, 1)
            validator.assert_not_called()

    def test_main_rejects_invalid_current_base_before_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            bundle = root / "bundle"
            bundle.mkdir()
            with mock.patch.object(render_review, "validate_bundle") as validator, mock.patch.object(
                render_review, "ensure_output_outside_repository"
            ):
                result = render_review.main(
                    [
                        str(bundle), "--repository", str(root / "repository"),
                        "--output", str(bundle / "site"), "--current-base", "BASE",
                    ]
                )
            self.assertEqual(result, 1)
            validator.assert_not_called()

    def test_main_requires_repository(self) -> None:
        with self.assertRaises(SystemExit):
            render_review.main(["bundle", "--output", "site"])

    def test_main_rejects_output_inside_repository_including_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            repository = root / "repository"
            bundle = repository / "bundle"
            repository.mkdir()
            bundle.mkdir()
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            output = bundle / "site"
            with mock.patch.object(render_review, "validate_bundle") as validator:
                result = render_review.main(
                    [
                        str(bundle), "--repository", str(repository),
                        "--output", str(output),
                    ]
                )
            self.assertEqual(result, 1)
            self.assertFalse(output.exists())
            validator.assert_not_called()

    def test_raw_fallback_makes_invalid_bytes_and_direction_controls_visible(self) -> None:
        page = render_review.raw_patch_page(
            b"valid \xe2\x82\xac bad \xff\n", "bad \u202eerror"
        )
        self.assertIn("valid \\xE2\\x82\\xAC bad \\xFF", page)
        self.assertIn("bad \\u202Eerror", page)
        visible = render_review.raw_patch_page("A\u202eZ".encode(), "error")
        self.assertIn("A\\u202EZ", visible)
        self.assertIn("default-src 'none'", page)
        self.assertNotIn("<script", page)


if __name__ == "__main__":
    unittest.main()
