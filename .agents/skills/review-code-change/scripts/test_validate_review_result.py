#!/usr/bin/env python3
"""Tests for review-result validation."""

from __future__ import annotations

import unittest

from validate_review_result import WORKBENCHES, validate


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


if __name__ == "__main__":
    unittest.main()
