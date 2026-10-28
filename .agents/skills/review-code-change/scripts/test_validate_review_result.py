#!/usr/bin/env python3
"""Tests for review-result validation."""

from __future__ import annotations

import unittest

from validate_review_result import WORKBENCHES, validate, validate_ledger


def valid_result() -> dict:
    receipts = [
        {"kind": "workbench", "name": name, "state": "complete"}
        for name in sorted(WORKBENCHES)
    ]
    receipts.append({"kind": "changed_file", "name": "source.ts", "state": "complete"})
    return {
        "review_status": "complete",
        "delivery_state": "draft",
        "external_posting_authorized": False,
        "output_comments": [
            {
                "issue_id": "cache-tenant-boundary",
                "priority": "P1",
                "path": "source.ts",
                "side": "RIGHT",
                "line": 2,
                "body": "[P1] Include the tenant in this cache key.",
            }
        ],
        "suppressions": [],
        "cleared": [],
        "checks": [],
        "blocking_limits": [],
        "completion_receipts": receipts,
    }


SNAPSHOT = {
    "changed_files": [
        {
            "path": "source.ts",
            "old_path": None,
            "left_ranges": [[2, 2]],
            "right_ranges": [[2, 3]],
        }
    ]
}


class ValidateReviewResultTests(unittest.TestCase):
    def test_accepts_complete_draft(self) -> None:
        self.assertEqual(validate(valid_result(), SNAPSHOT), [])

    def test_rejects_incomplete_receipt_in_complete_result(self) -> None:
        result = valid_result()
        result["completion_receipts"][0] = {
            **result["completion_receipts"][0],
            "state": "incomplete",
            "limit": "truncated",
        }
        self.assertTrue(validate(result, SNAPSHOT))

    def test_rejects_post_without_authority(self) -> None:
        result = valid_result()
        result["delivery_state"] = "posted"
        self.assertIn(
            "posted delivery requires external posting authority",
            validate(result, SNAPSHOT),
        )

    def test_rejects_non_changed_anchor(self) -> None:
        result = valid_result()
        result["output_comments"][0]["line"] = 8
        self.assertTrue(any("not anchored" in item for item in validate(result, SNAPSHOT)))

    def test_accepts_anchored_existing_thread_suppression(self) -> None:
        result = valid_result()
        result["suppressions"] = [
            {
                "issue_id": "existing-zero-balance",
                "path": "source.ts",
                "side": "RIGHT",
                "line": 3,
                "existing_thread_id": "thread-1",
                "reason": "An unresolved thread already reports this issue.",
            }
        ]
        self.assertEqual(validate(result, SNAPSHOT), [])

    def test_accepts_cleared_entry(self) -> None:
        result = valid_result()
        result["cleared"] = [
            {
                "behavior": "Checkpoint ids order the newest-wins lookup as text.",
                "locator": "source.ts",
                "evidence": "The ids are UUIDv6, so text order is chronological.",
                "from_candidate": "ordering-guard-unsound",
            }
        ]
        self.assertEqual(validate(result, SNAPSHOT), [])

    def test_rejects_cleared_entry_without_evidence(self) -> None:
        result = valid_result()
        result["cleared"] = [{"behavior": "Something", "locator": "source.ts"}]
        self.assertTrue(
            any("cleared[0] is missing required fields" in item for item in validate(result, SNAPSHOT))
        )

    def test_rejects_duplicate_issue_across_comment_and_suppression(self) -> None:
        result = valid_result()
        result["suppressions"] = [
            {
                "issue_id": "cache-tenant-boundary",
                "path": "source.ts",
                "side": "RIGHT",
                "line": 3,
                "existing_thread_id": "thread-1",
                "reason": "An unresolved thread already reports this issue.",
            }
        ]
        self.assertTrue(any("duplicate issue_id" in item for item in validate(result, SNAPSHOT)))


def valid_ledger() -> list[dict]:
    return [
        {
            "candidate_id": "state-1",
            "workbench": "state-and-failure",
            "title": "Cache key omits the tenant",
            "disposition": "kept",
            "issue_id": "cache-tenant-boundary",
            "reason": "Reproduced a cross-tenant read.",
        },
        {
            "candidate_id": "security-1",
            "workbench": "security-and-privacy",
            "title": "Tenant missing from cache key",
            "disposition": "merged",
            "issue_id": "cache-tenant-boundary",
            "reason": "Same defect and fix as state-1.",
        },
        {
            "candidate_id": "design-1",
            "workbench": "design-and-maintainability",
            "title": "Helper name is vague",
            "disposition": "below_bar",
            "reason": "Style preference with no concrete consequence.",
        },
    ]


class ValidateCandidateLedgerTests(unittest.TestCase):
    def test_accepts_kept_merged_and_dropped_candidates(self) -> None:
        self.assertEqual(validate_ledger(valid_ledger(), valid_result()), [])

    def test_rejects_output_comment_without_ledger_candidate(self) -> None:
        ledger = [record for record in valid_ledger() if record["disposition"] == "below_bar"]
        self.assertTrue(
            any("no kept or merged ledger candidate" in item for item in validate_ledger(ledger, valid_result()))
        )

    def test_rejects_kept_candidate_naming_unknown_comment(self) -> None:
        ledger = valid_ledger()
        ledger[0]["issue_id"] = "missing-comment"
        self.assertTrue(
            any("does not name an output comment" in item for item in validate_ledger(ledger, valid_result()))
        )

    def test_rejects_unknown_disposition_and_duplicate_id(self) -> None:
        ledger = valid_ledger()
        ledger[2]["disposition"] = "ignored"
        ledger[1]["candidate_id"] = "state-1"
        errors = validate_ledger(ledger, valid_result())
        self.assertTrue(any("disposition is invalid" in item for item in errors))
        self.assertTrue(any("candidate_id is duplicated" in item for item in errors))

    def test_requires_existing_discussion_candidate_for_suppression(self) -> None:
        result = valid_result()
        result["suppressions"] = [
            {
                "issue_id": "existing-zero-balance",
                "path": "source.ts",
                "side": "RIGHT",
                "line": 3,
                "existing_thread_id": "thread-1",
                "reason": "An unresolved thread already reports this issue.",
            }
        ]
        self.assertTrue(
            any("no existing_discussion ledger candidate" in item for item in validate_ledger(valid_ledger(), result))
        )
        ledger = valid_ledger() + [
            {
                "candidate_id": "behavior-1",
                "workbench": "behavior-and-contracts",
                "title": "Zero balance renders as empty",
                "disposition": "existing_discussion",
                "issue_id": "existing-zero-balance",
                "reason": "Thread 1 already reports it.",
            }
        ]
        self.assertEqual(validate_ledger(ledger, result), [])


if __name__ == "__main__":
    unittest.main()
