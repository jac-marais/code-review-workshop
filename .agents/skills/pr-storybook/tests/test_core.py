from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
PREPARE = SKILL_ROOT / "scripts" / "prepare_review.py"
VALIDATE = SKILL_ROOT / "scripts" / "validate_review.py"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git(repository: Path, *arguments: str) -> str:
    result = run(["git", "-C", str(repository), *arguments])
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class CoreContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        self.assertEqual(run(["git", "init", "-q", str(self.repository)]).returncode, 0)
        git(self.repository, "config", "user.name", "Review Test")
        git(self.repository, "config", "user.email", "review@example.test")

        (self.repository / "sample.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        (self.repository / "other.txt").write_text("one\ntwo\n", encoding="utf-8")
        git(self.repository, "add", "sample.txt", "other.txt")
        git(self.repository, "commit", "-q", "-m", "base")
        self.base = git(self.repository, "rev-parse", "HEAD")

        (self.repository / "sample.txt").write_text(
            "alpha\nbeta changed\ngamma\ndelta\n", encoding="utf-8"
        )
        (self.repository / "sample.txt").chmod(0o755)
        (self.repository / "other.txt").write_text(
            "one\ntwo changed\nthree\n", encoding="utf-8"
        )
        git(self.repository, "add", "sample.txt", "other.txt")
        git(self.repository, "commit", "-q", "-m", "head")
        self.head = git(self.repository, "rev-parse", "HEAD")
        self.bundle = self.root / "bundle"
        prepared = run(
            [
                sys.executable,
                str(PREPARE),
                str(self.repository),
                self.base,
                self.head,
                str(self.bundle),
                "--repository-name",
                "example/repository",
                "--title",
                "Test change",
                "--url",
                "https://github.com/example/repository/pull/1",
                "--created-at",
                "2026-09-01T12:00:00Z",
            ]
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def load(self, relative_path: str) -> dict[str, Any]:
        return json.loads((self.bundle / relative_path).read_text(encoding="utf-8"))

    def save(self, relative_path: str, value: dict[str, Any]) -> None:
        (self.bundle / relative_path).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def validation(
        self,
        *,
        repository: bool = False,
        current_head: str | None = None,
        current_base: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(VALIDATE), str(self.bundle)]
        if repository:
            command.extend(["--repository", str(self.repository)])
        if current_head is not None:
            command.extend(["--current-head", current_head])
        if current_base is not None:
            command.extend(["--current-base", current_base])
        return run(command)

    def unit_records(self) -> list[dict[str, Any]]:
        return [
            unit
            for file_record in self.load("run.json")["files"]
            for unit in file_record["units"]
        ]

    def author_valid_book(self) -> None:
        run_document = self.load("run.json")
        units = self.unit_records()
        first = units[0]
        changed_index = next(
            index
            for index, line in enumerate(first["lines"])
            if line["kind"] in {"addition", "deletion"}
        )
        (self.bundle / "chapters" / "01-review.mdx").write_text(
            "# Behavior\n\nThe change updates the stored values.\n\n"
            f'<Diff ref="{first["id"]}@{changed_index}:1" />\n',
            encoding="utf-8",
        )
        coverage = []
        for index, unit in enumerate(units):
            record: dict[str, Any] = {
                "unitId": unit["id"],
                "section": "Behavior",
                "disposition": "displayed" if index == 0 else "supporting",
            }
            if index:
                record["reason"] = "This unit supports the same behavior."
            coverage.append(record)
        self.save(
            "chapters/01-review.evidence.json",
            {
                "schemaVersion": 1,
                "runId": run_document["runId"],
                "chapter": "01-review",
                "coverage": coverage,
            },
        )

    def replace_run_id(self, run_document: dict[str, Any]) -> None:
        identity_body = {
            key: value
            for key, value in run_document.items()
            if key not in {"runId", "createdAt"}
        }
        encoded = json.dumps(
            identity_body,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        run_id = "sha256:" + hashlib.sha256(encoded).hexdigest()
        run_document["runId"] = run_id
        self.save("run.json", run_document)
        for name in ("book.json", "findings.json", "chapters/01-review.evidence.json"):
            document = self.load(name)
            document["runId"] = run_id
            self.save(name, document)

    def changed_anchor(self, unit_id: str | None = None) -> dict[str, Any]:
        run_document = self.load("run.json")
        for file_record in run_document["files"]:
            for unit in file_record["units"]:
                if unit_id is not None and unit["id"] != unit_id:
                    continue
                for line in unit.get("lines", []):
                    if line["kind"] == "addition":
                        return {
                            "fileId": file_record["id"],
                            "unitId": unit["id"],
                            "side": "new",
                            "line": line["newLine"],
                        }
                    if line["kind"] == "deletion":
                        return {
                            "fileId": file_record["id"],
                            "unitId": unit["id"],
                            "side": "old",
                            "line": line["oldLine"],
                        }
        raise AssertionError("test change has no changed line")

    def metadata_anchor(self) -> dict[str, Any]:
        run_document = self.load("run.json")
        for file_record in run_document["files"]:
            for unit in file_record["units"]:
                if unit["kind"] == "metadata":
                    return {"fileId": file_record["id"], "unitId": unit["id"]}
        raise AssertionError("test change has no metadata unit")

    def finding(self, finding_id: str, status: str = "verified") -> dict[str, Any]:
        return {
            "id": finding_id,
            "status": status,
            "severity": "P1",
            "confidence": "high",
            "title": "The change can fail",
            "summary": "This finding explains the failure.",
            "trigger": "A caller uses the changed path.",
            "impact": "The operation fails.",
            "fix": "Handle the changed path.",
            "source": "review-lead",
            "anchors": [self.changed_anchor()] if status == "verified" else [],
            "evidence": ["diff.patch"] if status == "verified" else [],
        }

    def test_preparation_creates_a_stable_incomplete_mdx_skeleton(self) -> None:
        validation = self.validation()
        self.assertNotEqual(validation.returncode, 0)
        self.assertIn("has no owner or disposition", validation.stderr)
        run_document = self.load("run.json")
        book = self.load("book.json")
        findings = self.load("findings.json")
        sidecar = self.load("chapters/01-review.evidence.json")
        self.assertEqual(run_document["schemaVersion"], 1)
        self.assertEqual(book, {
            "schemaVersion": 1,
            "runId": run_document["runId"],
            "title": "Test change",
        })
        self.assertEqual(findings["schemaVersion"], 2)
        self.assertEqual(sidecar["coverage"], [])
        self.assertTrue((self.bundle / "chapters" / "01-review.mdx").is_file())
        self.assertFalse((self.bundle / "review-manifest.json").exists())

        second_bundle = self.root / "second-bundle"
        prepared = run(
            [
                sys.executable, str(PREPARE), str(self.repository), self.base, self.head,
                str(second_bundle), "--repository-name", "example/repository",
                "--title", "Test change", "--url", "https://github.com/example/repository/pull/1",
                "--created-at", "2026-09-01T12:00:00Z",
            ]
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        second_run = json.loads((second_bundle / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(run_document["runId"], second_run["runId"])
        self.assertEqual(run_document["files"], second_run["files"])

    def test_preparation_uses_one_nonempty_title(self) -> None:
        untitled_bundle = self.root / "untitled-bundle"
        prepared = run(
            [
                sys.executable, str(PREPARE), str(self.repository), self.base, self.head,
                str(untitled_bundle), "--repository-name", "example/repository",
            ]
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        run_document = json.loads((untitled_bundle / "run.json").read_text(encoding="utf-8"))
        book = json.loads((untitled_bundle / "book.json").read_text(encoding="utf-8"))
        self.assertEqual(run_document["subject"]["title"], "Review of example/repository")
        self.assertEqual(book["title"], "Review of example/repository")

    def test_preparation_rejects_empty_changes_and_non_https_urls(self) -> None:
        for output, base, head, url, message in (
            (self.root / "empty", self.head, self.head, "", "no changed files"),
            (
                self.root / "http",
                self.base,
                self.head,
                "http://github.com/example/repository/pull/1",
                "HTTPS URL",
            ),
        ):
            prepared = run(
                [
                    sys.executable, str(PREPARE), str(self.repository), base, head,
                    str(output), "--repository-name", "example/repository", "--url", url,
                ]
            )
            self.assertNotEqual(prepared.returncode, 0)
            self.assertIn(message, prepared.stderr)
            self.assertFalse(output.exists())

    def test_subject_url_validation_distinguishes_github_pull_requests(self) -> None:
        contract = importlib.import_module("_review_contract")
        self.assertTrue(
            contract.validate_subject_url(
                "https://github.com/example/repository/pull/1",
                "example/repository",
            )
        )
        self.assertTrue(
            contract.validate_subject_url(
                "https://github.enterprise.test/example/repository/pull/1",
                "example/repository",
            )
        )
        self.assertFalse(
            contract.validate_subject_url(
                "https://reviews.example.test/changes/9?tab=diff#L1",
                "example/repository",
            )
        )
        for url, message in (
            (
                "https://github.com/different/repository/pull/1",
                "does not match the run repository",
            ),
            (
                "https://github.com/example/repository/issues/1",
                None,
            ),
            (
                "https://github.com/example/repository/pull/1?diff=split",
                "must be https://host/owner/repo/pull/N",
            ),
            (
                "https://github.enterprise.test:8443/example/repository/pull/1",
                "must be https://host/owner/repo/pull/N",
            ),
            (
                "https://github.enterprise.test/example/repository/pull/1#discussion",
                "must be https://host/owner/repo/pull/N",
            ),
            (
                "https://reviewer:secret@github.enterprise.test/example/repository/pull/1",
                "must be https://host/owner/repo/pull/N",
            ),
        ):
            with self.subTest(url=url):
                if message is None:
                    self.assertFalse(
                        contract.validate_subject_url(url, "example/repository")
                    )
                else:
                    with self.assertRaisesRegex(contract.ContractError, message):
                        contract.validate_subject_url(url, "example/repository")

    def test_preparation_accepts_a_general_non_github_https_url(self) -> None:
        output = self.root / "non-github"
        url = "https://reviews.example.test/changes/9?tab=diff#L1"
        prepared = run(
            [
                sys.executable,
                str(PREPARE),
                str(self.repository),
                self.base,
                self.head,
                str(output),
                "--repository-name",
                "example/repository",
                "--url",
                url,
                "--created-at",
                "2026-09-01T12:00:00Z",
            ]
        )

        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertEqual(
            json.loads((output / "run.json").read_text(encoding="utf-8"))["subject"]["url"],
            url,
        )

    def test_valid_book_can_own_units_from_multiple_files(self) -> None:
        self.author_valid_book()
        self.assertGreaterEqual(len(self.unit_records()), 2)
        validation = self.validation(
            repository=True, current_head=self.head, current_base=self.base
        )
        self.assertEqual(validation.returncode, 0, validation.stderr)
        self.assertIn("Git metadata verified", validation.stdout)

    def test_book_and_sidecars_require_exact_run_ids_and_fields(self) -> None:
        self.author_valid_book()
        book = self.load("book.json")
        book["runId"] = "sha256:" + "0" * 64
        book["repository"] = "copied metadata"
        self.save("book.json", book)
        sidecar = self.load("chapters/01-review.evidence.json")
        sidecar["runId"] = "sha256:" + "0" * 64
        sidecar["path"] = "sample.txt"
        self.save("chapters/01-review.evidence.json", sidecar)

        validation = self.validation()

        self.assertIn("book.json.runId: does not match run.json", validation.stderr)
        self.assertIn("unknown fields: repository", validation.stderr)
        self.assertIn("evidence.json.runId: does not match run.json", validation.stderr)
        self.assertIn("unknown fields: path", validation.stderr)

    def test_each_unit_needs_one_owner_and_disposition(self) -> None:
        self.author_valid_book()
        sidecar = self.load("chapters/01-review.evidence.json")
        missing = sidecar["coverage"].pop()["unitId"]
        first = sidecar["coverage"][0]
        sidecar["coverage"].append(dict(first))
        sidecar["coverage"][0]["disposition"] = "supporting"
        sidecar["coverage"][0].pop("reason", None)
        sidecar["coverage"][1]["disposition"] = "displayed"
        sidecar["coverage"][1]["reason"] = "This must not be present."
        self.save("chapters/01-review.evidence.json", sidecar)

        validation = self.validation()

        self.assertIn(f"review unit {missing!r} has no owner or disposition", validation.stderr)
        self.assertIn("has 2 owners or dispositions", validation.stderr)
        self.assertIn("supporting coverage needs a reason", validation.stderr)
        self.assertIn("displayed coverage must not have a reason", validation.stderr)

    def test_unknown_unit_and_bad_disposition_are_rejected(self) -> None:
        self.author_valid_book()
        sidecar = self.load("chapters/01-review.evidence.json")
        sidecar["coverage"][0]["unitId"] = "unit:" + "0" * 64
        sidecar["coverage"][0]["disposition"] = "ignored"
        self.save("chapters/01-review.evidence.json", sidecar)

        validation = self.validation()

        self.assertIn("references an unknown unit", validation.stderr)
        self.assertIn("must be displayed, supporting, or mechanical", validation.stderr)

    def test_support_reason_has_a_small_bound(self) -> None:
        self.author_valid_book()
        sidecar = self.load("chapters/01-review.evidence.json")
        sidecar["coverage"][1]["reason"] = "x" * 241
        self.save("chapters/01-review.evidence.json", sidecar)

        validation = self.validation()

        self.assertIn("must contain at most 240 characters", validation.stderr)

    def test_chapter_and_sidecar_names_must_pair(self) -> None:
        self.author_valid_book()
        (self.bundle / "chapters" / "01-review.evidence.json").rename(
            self.bundle / "chapters" / "wrong name.evidence.json"
        )

        validation = self.validation()

        self.assertIn("01-review.evidence.json: is missing", validation.stderr)
        self.assertIn("wrong name.mdx: is missing", validation.stderr)
        self.assertIn("lowercase hyphenated name", validation.stderr)

    def test_repository_validation_proves_facts_that_offline_mode_cannot(self) -> None:
        self.author_valid_book()
        run_document = self.load("run.json")
        run_document["subject"]["base"] = self.head
        run_document["subject"]["mergeBase"] = self.head
        self.replace_run_id(run_document)

        offline_validation = self.validation()
        self.assertEqual(offline_validation.returncode, 0, offline_validation.stderr)
        repository_validation = self.validation(
            repository=True, current_head=self.head, current_base=self.base
        )
        self.assertNotEqual(repository_validation.returncode, 0)
        self.assertIn("does not match the declared repository revisions", repository_validation.stderr)
        self.assertIn("path metadata does not match the repository", repository_validation.stderr)

    def test_git_commands_disable_writes_prompts_hooks_and_lazy_fetch(self) -> None:
        contract = importlib.import_module("_review_contract")
        completed = subprocess.CompletedProcess([], 0, stdout=b"ok\n", stderr=b"")
        injected_environment = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "alias.diff",
            "GIT_CONFIG_VALUE_0": "malicious",
            "GIT_EXTERNAL_DIFF": "malicious",
            "GIT_DIR": "/wrong/repository",
        }
        with mock.patch.dict(contract.os.environ, injected_environment), mock.patch.object(
            contract.subprocess, "run", return_value=completed
        ) as run_git:
            self.assertEqual(contract.git_output(self.repository, ["status"]), b"ok\n")

        command = run_git.call_args.args[0]
        environment = run_git.call_args.kwargs["env"]
        self.assertIn("--no-optional-locks", command)
        self.assertIn("--no-replace-objects", command)
        self.assertIn("core.fsmonitor=false", command)
        self.assertIn("core.hooksPath=/dev/null", command)
        self.assertIn("maintenance.auto=false", command)
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], "/dev/null")
        self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(environment["GIT_ALLOW_PROTOCOL"], "file")
        self.assertEqual(environment["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(environment["GCM_INTERACTIVE"], "Never")
        self.assertNotIn("GIT_CONFIG_COUNT", environment)
        self.assertNotIn("GIT_CONFIG_KEY_0", environment)
        self.assertNotIn("GIT_CONFIG_VALUE_0", environment)
        self.assertNotIn("GIT_EXTERNAL_DIFF", environment)
        self.assertNotIn("GIT_DIR", environment)
        self.assertIs(run_git.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_repository_state_detects_tracked_and_untracked_content_changes(self) -> None:
        contract = importlib.import_module("_review_contract")
        clean_state = contract.repository_state(self.repository)
        untracked = self.repository / "untracked.txt"
        untracked.write_text("first\n", encoding="utf-8")
        first_untracked_state = contract.repository_state(self.repository)
        untracked.write_text("second\n", encoding="utf-8")
        second_untracked_state = contract.repository_state(self.repository)
        (self.repository / "other.txt").write_text("tracked change\n", encoding="utf-8")
        tracked_state = contract.repository_state(self.repository)

        self.assertNotEqual(clean_state, first_untracked_state)
        self.assertNotEqual(first_untracked_state, second_untracked_state)
        self.assertNotEqual(second_untracked_state, tracked_state)

    def test_repository_state_detects_untracked_permission_changes(self) -> None:
        contract = importlib.import_module("_review_contract")
        untracked = self.repository / "untracked.sh"
        untracked.write_text("#!/bin/sh\n", encoding="utf-8")
        untracked.chmod(0o600)
        non_executable_state = contract.repository_state(self.repository)
        untracked.chmod(0o700)
        executable_state = contract.repository_state(self.repository)

        self.assertNotEqual(non_executable_state, executable_state)

    def test_preparation_rejects_repository_state_change(self) -> None:
        prepare_module = importlib.import_module("prepare_review")
        changed_bundle = self.root / "changed-bundle"
        with mock.patch.object(
            prepare_module, "repository_state", side_effect=["before", "after"]
        ):
            with self.assertRaisesRegex(
                prepare_module.PreparationError,
                "changed the repository or checkout state",
            ):
                prepare_module.prepare(
                    repository=self.repository,
                    base_revision=self.base,
                    head_revision=self.head,
                    output=changed_bundle,
                    repository_name="example/repository",
                    title="State test",
                    url="",
                    created_at="2026-09-01T12:00:00Z",
                )
        self.assertFalse(changed_bundle.exists())

    def test_repository_validation_reports_its_own_state_change(self) -> None:
        validator_module = importlib.import_module("validate_review")
        self.author_valid_book()
        with mock.patch.object(
            validator_module, "repository_state", side_effect=["before", "after"]
        ):
            errors = validator_module.validate_bundle(
                self.bundle,
                repository=self.repository,
                current_head=self.head,
                current_base=self.base,
            )
        self.assertIn(
            "repository: review validation changed the repository or checkout state",
            errors,
        )

    def test_current_pull_request_revisions_reject_a_stale_bundle(self) -> None:
        self.author_valid_book()
        current = self.validation(current_head=self.head, current_base=self.base)
        stale_head = self.validation(current_head=self.base, current_base=self.base)
        stale_base = self.validation(current_head=self.head, current_base=self.head)
        invalid_head = self.validation(current_head="HEAD", current_base=self.base)
        invalid_base = self.validation(current_head=self.head, current_base="BASE")
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertIn("current-head: does not match the frozen head", stale_head.stderr)
        self.assertIn("current-base: does not match the frozen base", stale_base.stderr)
        self.assertIn("40- or 64-character Git ID", invalid_head.stderr)
        self.assertIn("40- or 64-character Git ID", invalid_base.stderr)

    def test_repository_validation_requires_current_pull_request_revisions(self) -> None:
        self.author_valid_book()
        missing_both = self.validation(repository=True)
        missing_head = self.validation(repository=True, current_base=self.base)
        missing_base = self.validation(repository=True, current_head=self.head)
        current = self.validation(
            repository=True, current_head=self.head, current_base=self.base
        )

        self.assertIn("current-head: is required", missing_both.stderr)
        self.assertIn("current-base: is required", missing_both.stderr)
        self.assertIn("current-head: is required", missing_head.stderr)
        self.assertNotIn("current-base: is required", missing_head.stderr)
        self.assertIn("current-base: is required", missing_base.stderr)
        self.assertNotIn("current-head: is required", missing_base.stderr)
        self.assertEqual(current.returncode, 0, current.stderr)

    def test_current_revision_validation_rejects_non_string_values(self) -> None:
        validator_module = importlib.import_module("validate_review")
        run_document = self.load("run.json")
        validator = validator_module.Validator()

        validator_module._validate_current_revisions(
            run_document,
            [self.head],
            {"base": self.base},
            validator,
            required=True,
        )

        self.assertIn(
            "current-head: must be a lowercase 40- or 64-character Git ID",
            validator.errors,
        )
        self.assertIn(
            "current-base: must be a lowercase 40- or 64-character Git ID",
            validator.errors,
        )

    def test_finding_ids_use_lowercase_letters_digits_and_hyphens(self) -> None:
        self.author_valid_book()
        findings = self.load("findings.json")
        findings["findings"] = [self.finding("valid-finding-2")]
        self.save("findings.json", findings)
        self.assertEqual(self.validation().returncode, 0)

        for invalid_id in ("invalid_finding", "2-invalid"):
            with self.subTest(finding_id=invalid_id):
                findings["findings"] = [self.finding(invalid_id)]
                self.save("findings.json", findings)
                validation = self.validation()
                self.assertIn(
                    "only lowercase letters, digits, or hyphens",
                    validation.stderr,
                )

    def test_verified_findings_need_exact_changed_line_anchors(self) -> None:
        self.author_valid_book()
        findings = self.load("findings.json")
        findings["findings"] = [self.finding("verified-failure")]
        self.save("findings.json", findings)
        self.assertEqual(self.validation().returncode, 0)

        findings["findings"][0]["anchors"][0]["line"] = 9999
        self.save("findings.json", findings)
        validation = self.validation()
        self.assertIn("does not identify a line", validation.stderr)
        self.assertIn("needs a valid evidence anchor", validation.stderr)

    def test_verified_finding_can_anchor_to_a_metadata_unit_without_a_line(self) -> None:
        self.author_valid_book()
        findings = self.load("findings.json")
        finding = self.finding("metadata-failure")
        finding["anchors"] = [self.metadata_anchor()]
        findings["findings"] = [finding]
        self.save("findings.json", findings)

        validation = self.validation()

        self.assertEqual(validation.returncode, 0, validation.stderr)

    def test_hunk_and_metadata_anchors_have_distinct_exact_shapes(self) -> None:
        self.author_valid_book()
        findings = self.load("findings.json")
        hunk_finding = self.finding("hunk-without-line")
        hunk_anchor = self.changed_anchor()
        hunk_anchor.pop("side")
        hunk_anchor.pop("line")
        hunk_finding["anchors"] = [hunk_anchor]
        metadata_finding = self.finding("metadata-with-line")
        metadata_anchor = self.metadata_anchor()
        metadata_anchor.update({"side": "new", "line": 1})
        metadata_finding["anchors"] = [metadata_anchor]
        findings["findings"] = [hunk_finding, metadata_finding]
        self.save("findings.json", findings)

        validation = self.validation()

        self.assertIn("a hunk anchor needs side and line", validation.stderr)
        self.assertIn("a metadata anchor must omit side and line", validation.stderr)

    def test_malformed_findings_fail_without_a_traceback(self) -> None:
        self.author_valid_book()
        findings = self.load("findings.json")
        finding = self.finding("bad-types")
        finding["anchors"] = [{
            "fileId": [], "unitId": {}, "side": ["new"], "line": {"value": 1}
        }]
        findings["findings"] = [finding]
        self.save("findings.json", findings)

        validation = self.validation()

        self.assertNotEqual(validation.returncode, 0)
        self.assertIn("must be a string", validation.stderr)
        self.assertNotIn("Traceback", validation.stderr)

    def test_malformed_json_and_patch_digest_mismatch_are_rejected(self) -> None:
        self.author_valid_book()
        (self.bundle / "findings.json").write_text("{broken", encoding="utf-8")
        with (self.bundle / "diff.patch").open("ab") as stream:
            stream.write(b"unexpected\n")
        validation = self.validation()
        self.assertNotEqual(validation.returncode, 0)
        self.assertIn("invalid JSON", validation.stderr)
        self.assertIn("does not match diff.patch", validation.stderr)

    def test_required_input_symlinks_are_rejected(self) -> None:
        self.author_valid_book()
        target = self.root / "book-target.json"
        target.write_bytes((self.bundle / "book.json").read_bytes())
        (self.bundle / "book.json").unlink()
        (self.bundle / "book.json").symlink_to(target)
        validation = self.validation()
        self.assertIn("book.json: must not be a symbolic link", validation.stderr)

    def test_prepare_rejects_output_inside_repository_and_through_symlink(self) -> None:
        link = self.root / "repository-link"
        link.symlink_to(self.repository, target_is_directory=True)
        for output in (self.repository / "review-bundle", link / "review-bundle"):
            prepared = run(
                [
                    sys.executable, str(PREPARE), str(self.repository), self.base, self.head,
                    str(output), "--repository-name", "example/repository",
                ]
            )
            self.assertNotEqual(prepared.returncode, 0)
            self.assertIn("output must be outside the reviewed repository", prepared.stderr)
            self.assertFalse(output.exists())

    def test_prepare_cleans_staged_bundle_when_a_write_fails(self) -> None:
        prepare_module = importlib.import_module("prepare_review")
        failed_bundle = self.root / "failed-bundle"
        with mock.patch.object(
            prepare_module, "_write_json", side_effect=OSError("forced write failure")
        ):
            with self.assertRaisesRegex(
                prepare_module.PreparationError, "cannot publish review bundle"
            ):
                prepare_module.prepare(
                    repository=self.repository,
                    base_revision=self.base,
                    head_revision=self.head,
                    output=failed_bundle,
                    repository_name="example/repository",
                    title="Failure test",
                    url="",
                    created_at="2026-09-01T12:00:00Z",
                )
        self.assertFalse(failed_bundle.exists())
        self.assertEqual(list(self.root.glob(".failed-bundle.tmp-*")), [])

    def test_binary_and_metadata_only_changes_get_review_units(self) -> None:
        contract = importlib.import_module("_review_contract")
        binary_patch = (
            b"diff --git a/image.bin b/image.bin\n"
            b"index 1111111..2222222 100644\n"
            b"GIT binary patch\n"
            b"literal 1\nAc${Nk00001\n"
        )
        metadata_patch = (
            b"diff --git a/tool.sh b/tool.sh\n"
            b"old mode 100644\n"
            b"new mode 100755\n"
        )
        mixed_patch = (
            b"diff --git a/tool.sh b/tool.sh\n"
            b"old mode 100644\n"
            b"new mode 100755\n"
            b"index 1111111111111111111111111111111111111111..2222222222222222222222222222222222222222 100644\n"
            b"--- a/tool.sh\n"
            b"+++ b/tool.sh\n"
            b"@@ -1 +1 @@\n"
            b"-old\n"
            b"+new\n"
        )
        added_patch = (
            b"diff --git a/new.sh b/new.sh\n"
            b"new file mode 100755\n"
            b"index 0000000000000000000000000000000000000000..2222222222222222222222222222222222222222\n"
            b"--- /dev/null\n"
            b"+++ b/new.sh\n"
            b"@@ -0,0 +1 @@\n"
            b"+new\n"
        )
        binary = contract.make_file_record(
            contract.ChangedPath("modified", "image.bin", "image.bin"), binary_patch
        )
        metadata = contract.make_file_record(
            contract.ChangedPath("modified", "tool.sh", "tool.sh"), metadata_patch
        )
        mixed = contract.make_file_record(
            contract.ChangedPath("modified", "tool.sh", "tool.sh"), mixed_patch
        )
        added = contract.make_file_record(
            contract.ChangedPath("added", None, "new.sh"), added_patch
        )
        self.assertTrue(binary["isBinary"])
        self.assertEqual(binary["units"][0]["kind"], "metadata")
        self.assertEqual(binary["units"][0]["label"], "Binary change")
        self.assertFalse(metadata["isBinary"])
        self.assertEqual(metadata["units"][0]["label"], "File mode change")
        self.assertEqual([unit["kind"] for unit in mixed["units"]], ["hunk", "metadata"])
        self.assertEqual(mixed["units"][1]["label"], "File mode change")
        self.assertEqual([unit["kind"] for unit in added["units"]], ["hunk", "metadata"])

    def test_preparation_keeps_hunk_and_mode_units_for_one_file(self) -> None:
        sample = next(
            file_record
            for file_record in self.load("run.json")["files"]
            if file_record["path"] == "sample.txt"
        )
        self.assertEqual([unit["kind"] for unit in sample["units"]], ["hunk", "metadata"])
        self.assertEqual(sample["units"][1]["label"], "File mode change")

    def test_invalid_utf8_patch_text_uses_reversible_byte_escapes(self) -> None:
        contract = importlib.import_module("_review_contract")
        original = b"literal \\xFF valid \xe2\x82\xac invalid \xff nul \x00\n"
        escaped = contract._text(original)
        self.assertIn("literal \\x5CxFF", escaped)
        self.assertIn("valid \\xE2\\x82\\xAC", escaped)
        self.assertIn("invalid \\xFF", escaped)


if __name__ == "__main__":
    unittest.main()
