# Synthesis And Comment Rules

## Candidate Before Comment

Each workbench returns structured candidate issues with exact revision, path, anchor, symbol, invariant, trigger, causal chain, impact, evidence, validation, counterevidence, assumptions, fix direction, first failing state, priority, confidence, and provenance.

The review lead verifies every candidate issue from raw code. Candidate issues enter deduplication only after they survive falsification.

## Deduplication Boundary

Merge only when all of these are true:

- the counterfactual defect is the same;
- the issue first becomes true in the same change or stack prefix;
- one minimal complete fix cures every path;
- one comment preserves every important trigger, impact, and location.

Keep independently fixable occurrences separate, even when they share a category, rule, file, sink, or wording. One cause with several manifestations uses one primary anchor and cites the other manifestations as supporting evidence.

Check all existing issue comments, review bodies, inline comments, threads, replies, resolved state, and outdated state before creating a new top-level comment. Recheck after synthesis.

## Output Comment

A comment states:

1. Priority and a short title.
2. Current behavior.
3. Concrete trigger and consequence.
4. Evidence that establishes the issue.
5. Smallest complete fix direction.
6. Material assumptions or validation limits.

Do not publish style preferences, praise, generic hardening, unsupported hypotheticals, mechanically enforced issues, pre-existing issues that the change did not worsen, or real issues attached to unrelated lines.
