# Candidate Verification And Output

## Candidate Issue

Normalize every workbench claim into:

- candidate ID and workbench;
- exact head SHA, path, side, line, and symbol;
- violated invariant or contract;
- trigger and preconditions;
- current behavior and causal chain;
- affected users, data, systems, or maintainers;
- evidence and locator;
- validation attempted and result;
- counterevidence and assumptions;
- smallest complete fix direction;
- provisional priority and confidence.

Zero candidates is valid.

Robust Rules Review and Security Lens Review use the same candidate shape as every other workbench. They do not create separate summaries, reports, or output comments.

## Verification

The review lead returns to raw code for every candidate issue:

1. Confirm the exact revision, symbol, and changed-line anchor.
2. Trace the complete code, configuration, data, and deployment path.
3. Search for guards, conventions, and counterexamples.
4. Confirm the change introduced or materially worsened the issue.
5. Run the smallest safe check that settles uncertainty.
6. Confirm that the proposed fix is complete and belongs at the anchor.
7. Drop, narrow, or restate unsupported claims.

Agreement raises confidence only when workbenches add different evidence. Several workbenches reaching one conclusion from the same starting scope is one observation, not several.

When verification contradicts a finding you already delivered, lead with the correction before any new finding. Someone may be part-way through fixing it.

## Deduplication

Merge verified candidate issues only when all are true:

- same counterfactual defect;
- same first failing change;
- one minimal complete fix cures every path;
- one comment preserves every important trigger, impact, and location.

Keep independently fixable occurrences separate even when they share a category, rule, sink, file, or wording. A stable issue identity uses invariant, causal symbol or configuration, failure mechanism, trust or behavior scope, first failing state, and minimal fix. Exclude line number and wording.

Fetch and compare issue comments, review bodies, inline comments, threads, replies, resolved state, and outdated state. Suppress an existing unresolved issue. Mark a still-present resolved or outdated issue as persistent or regressed in the private record. Do not create a new top-level duplicate.

Record each suppressed duplicate in `suppressions` with a stable issue identity, changed-line anchor, existing thread identifier, and reason. This record is private evidence that the duplicate was found and intentionally withheld. Never include a suppression in `output_comments`.

## Cleared Behavior

Record in `cleared` every behavior a workbench investigated and found sound, and every candidate verification disproved. Give each the behavior examined, where it lives, and the evidence that settled it.

This is the review's other product. A reader who knows the ordering guard holds, the two identity paths agree, and the database tests do run in CI stops there instead of re-deriving all three. Without a home in the record, that work survives only in prose and the next reviewer repeats it.

Keep it to behavior someone would reasonably suspect. A list of everything that happens to work is noise.

## Priorities

- P0: immediate broad compromise, destructive data loss, or a similarly catastrophic failure.
- P1: high-impact failure with realistic preconditions, such as tenant escape, authorization bypass, corrupt state, or a broken critical path.
- P2: material but bounded behavior, contract, reliability, or maintenance failure.
- P3: small real defect with a concrete consequence and useful correction.

## Output Comment

The review lead writes output only after it has combined every workbench result into one candidate ledger, verified the retained candidates, and completed global deduplication. The final response does not separate findings by discovery protocol unless that provenance helps explain distinct evidence.

Use one causal changed-line anchor. Never attach a real issue to unrelated changed code.

Write:

1. Priority and short title.
2. Current behavior.
3. Concrete trigger and consequence.
4. Evidence.
5. Smallest complete fix direction.
6. Material assumptions or limits.

Comment on code, not the author. Offer an exact patch only when repository evidence supports it. Default to a draft response and create no platform action.

## Handoff

Output comments suit a reviewer reading one issue at a time. Someone about to do the work needs one document instead, ordered by what they do next. Produce it as a single fenced block they can copy whole.

Ask for the delivery bar before filtering, because it is the user's call and it changes what belongs. State the bar you applied and how many candidates it dropped. Silent filtering reads as completeness.

```
Header      repository, branch, base and head, path convention
Filter      the bar applied, and the raw candidate count behind it
Headline    P0 and P1 counts, and which previously delivered findings
            verification has since closed, narrowed, or withdrawn
Findings    grouped by what the reader does next, not by severity:
              lands badly in production, so fix or accept knowingly
              resolve before merge, a decision rather than a code change
              cheap insurance, small fixes with real downside if skipped
            each one: anchor, whether it is verified or still reported,
            the defect, the realistic trigger, the smallest fix direction
Excluded    what the bar dropped, named, so the filter is auditable
Cleared     from the cleared record, so nobody re-derives it
```

Two findings at one priority can need entirely different responses, which is why the grouping is by action. Mark every finding verified or reported, because a reader who cannot tell will either trust an unverified claim or re-check a settled one.
