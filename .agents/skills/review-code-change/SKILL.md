---
name: review-code-change
description: Review one local working-tree change, branch, revision range, or pull request in repository context with default Robust Rules Review and Security Lens Review workbenches, then return verified, deduplicated, changed-line comments with suggested fixes without applying them. Use for code review, PR review, security and robustness review of one change, or requests to run tests and browser checks before commenting. Do not use for pull request stacks, implementation, or automatic GitHub actions.
---

# Review Code Change

Review one change from intake through a draft review response. Optimize for correct, useful comments, not comment count.

## Read First

Read these references completely before acting:

1. [`authority-and-safety.md`](references/authority-and-safety.md)
2. [`review-workflow.md`](references/review-workflow.md)
3. [`candidate-and-output.md`](references/candidate-and-output.md)

Also read:

- [`git-and-platform.md`](references/git-and-platform.md) for a committed revision range or platform pull request.
- [`validation.md`](references/validation.md) before any install, target command, server, or browser flow.

## Bound The Request

Accept exactly one of:

- an uncommitted working-tree change;
- one base and head revision range;
- one branch relative to a base;
- one pull request plus an optional matching local checkout.

If the input contains two or more linked pull requests, stop and route to the stack workflow. If the user asks to implement fixes, keep this review read-only and treat implementation as a separate task.

Default to output only. Do not create comments or change platform state unless the user separately and explicitly authorizes that exact action.

## Run The Workflow

1. Capture the user-checkout status and the exact requested scope.
2. Freeze repository identity, revisions, merge bases, platform facts, discussions, and commentable lines.
3. Reconcile the platform file inventory with the complete local Git inventory.
4. When the change exceeds one reviewer's context, cluster it by feature, size extra cluster passes to risk, write per-lane questions, and build one shared facts brief every workbench reads.
5. Account for every changed file and inspect each complete logical change in bounded chunks.
6. Build a change map for behavior, contracts, state, trust boundaries, dependencies, operations, tests, and user flows.
7. Plan named validation questions. Send target commands only to the sandboxed validation executor.
8. Run every mandatory workbench once over the complete frozen scope. A workbench can divide its lane by cluster. They must not see one another's candidate issues.
9. Normalize each candidate issue, then reopen raw code and try to disprove it.
10. Keep only issues introduced or materially worsened by the change.
11. Deduplicate by counterfactual defect, first failing state, and minimal complete fix.
12. Deduplicate against every existing discussion surface.
13. Draft changed-line output comments, then recheck head, discussions, anchors, receipts, and user-checkout status.

When subagents are available, use separate read-only agents for independent workbenches. Give each the frozen scope facts, the shared facts brief, its cluster's per-lane questions, and no sibling output. When subagents are unavailable, run the workbenches in separate contexts and record the reduced independence as a limit.

## Mandatory Workbenches

Run every workbench. Routing may add specialists but cannot remove the baseline.

- Behavior and contracts
- State and failure
- Security and privacy, implemented by [`Security Lens Review`](../security-lens-review/SKILL.md)
- Design and maintainability, implemented by [`Robust Rules Review`](../review-robust-rules/SKILL.md)
- Evidence and integration

Completion receipts name these workbenches by slug: `behavior-and-contracts`, `state-and-failure`, `security-and-privacy`, `design-and-maintainability`, `evidence-and-integration`. The validator matches those exact strings.

Use a separate read-only coordinator for each linked protocol when subagents are available. Give it the shared facts brief, lane questions, relevant raw code, and validation evidence, but no sibling candidates. Each coordinator follows its linked skill's orchestrated workbench mode and does not create a separate summary, report, or output comment.

The review lead owns the shared candidate ledger. It verifies and deduplicates all candidates, then writes the only final review response. A workbench does not post comments, modify files, or execute target commands.

## Evidence Rules

- Treat agreement as correlated support, not proof.
- Confirm a cited path exists before citing it. A finding built on a file that is not there collapses and discredits the ones beside it.
- Contradict the shared facts brief loudly when your own reading disagrees. The lead wrote it and can be wrong in it, and one wrong fact there reaches every workbench at once.
- Require a concrete trigger, complete causal path, material consequence, useful changed-line anchor, and smallest complete fix direction.
- For P0 and P1 issues, require executable reproduction, a complete static or type proof, or strong contract evidence with a concrete counterexample.
- A green test proves only the exercised path.
- Drop style preferences, praise, vague hardening, unsupported hypotheticals, mechanically enforced issues, and pre-existing defects the change did not worsen.

## Complete Or Incomplete

Record one completion receipt for every changed file and mandatory workbench.

Set `review_status: incomplete` when content or output is truncated, a mandatory workbench fails, exact scope cannot be proven, a required check cannot run safely, or a resource limit prevents coverage. Preserve verified evidence, but do not imply that the review finished.

## Return

Create the private result record under `review-work/pr-reviews/<review-id>/`. Keep every case-specific brief, report, snapshot, clone, worktree, and generated artifact under `review-work/`, outside the target checkout.

The result record must conform to [`review-result.schema.json`](references/review-result.schema.json). Validate it with:

```sh
python3 .agents/skills/review-code-change/scripts/validate_review_result.py review-work/pr-reviews/<review-id>/review-result.json --snapshot review-work/pr-reviews/<review-id>/review-snapshot.json
```

Return the review response, not the private candidate ledger:

- `review_status` and `delivery_state`;
- output comments, or the handoff in [`candidate-and-output.md`](references/candidate-and-output.md) when the findings go to whoever does the work;
- checks run and their exact scope;
- behavior investigated and cleared, so the next reader stops rather than re-deriving it;
- material limits when they affect confidence or completeness.

Ask which delivery bar applies before filtering. Under release pressure a user may want only what blocks the merge, and that is their decision, not yours. Whatever bar you apply, name it and name what it dropped.

Use `delivery_state: draft` unless posting was separately authorized. Offer fixes in the comments. Never apply them.
