# Batch 001 Contradictions

## CTR-001: Full Repository Context Versus Attention Dilution

- Axis: how much context a workbench should receive
- Claims: `CLM-004`, `CLM-006`
- Stakes: too little context misses contracts and conventions; a flat context dump hides changed code and increases fabricated claims.
- Type: contextual
- Disposition: resolved by separating repository access from prompt payload
- Basis: workbenches receive the verified change map and tool access. They retrieve focused context tied to a call path, invariant, contract, or configuration. The verifier reopens exact files.
- Remaining uncertainty: the best retrieval representation for TypeScript, Go, and Python needs real-use regression cases.

## CTR-002: AI-Led Review Preference Versus Anchoring

- Axis: when AI findings should appear
- Claims: `CLM-002`, `CLM-005`
- Stakes: early AI output can help orientation but can also pull attention toward low-severity or framed issues.
- Type: contextual
- Disposition: contextual
- Basis: keep workbenches blind to one another. If a human reviewer participates, preserve an initial independent human pass when feasible. A concise change map may appear early, but candidate findings do not.
- Remaining uncertainty: the workshop cannot control an external human workflow unless the user requests it.

## CTR-003: More Reviewers Versus Diminishing Returns

- Axis: workbench count
- Claims: `CLM-001`, `CLM-017`
- Stakes: too few passes miss failure classes; too many add correlated noise and synthesis errors.
- Type: contextual
- Disposition: resolved with adaptive breadth
- Basis: run a small mandatory baseline with distinct methods. Routing may add a UI, infrastructure, data-migration, concurrency, dependency, performance, or domain specialist, but it cannot remove the baseline. Track unique verified yield.
- Remaining uncertainty: the optimal count by change risk remains open.

## CTR-004: Checklists Versus Scenario-Based Reading

- Axis: how procedures guide reviewers
- Claims: `CLM-003`
- Stakes: generic lists invite shallow scanning, while no completion check can omit entire surfaces.
- Type: contextual
- Disposition: contextual
- Basis: scenario procedures drive discovery. A short coverage receipt records which surfaces ran or were not applicable after the analytical work.
- Remaining uncertainty: none for the first trial.

## CTR-005: Local Decomposition Versus Global Stack Behavior

- Axis: pull request stack review range
- Claims: `CLM-024`, `CLM-025`
- Stakes: only local review repeats upstream symptoms and misses interactions; only cumulative review loses the responsible change.
- Type: contextual
- Disposition: resolved with two views
- Basis: review every proved parent edge, preserve a root-to-tip ledger, then review the cumulative base-to-tip state and assign each issue to the first violating state.
- Remaining uncertainty: mixed or stale stack attribution stops until topology is repaired or authoritative metadata resolves it.

## CTR-006: Intent Metadata Helps Requirements Review But Can Bias Security Review

- Axis: use of pull request description and commit messages
- Claims: `CLM-005`
- Stakes: removing intent can miss requirement drift; accepting it can hide an adversarial security change.
- Type: contextual
- Disposition: resolved with two contexts
- Basis: behavior and contract review uses requirements after marking them as untrusted claims. Security gets a code-first metadata-redacted pass and an intent-aware comparison.
- Remaining uncertainty: whether metadata redaction helps non-security review remains an open research thread.

## CTR-007: Multi-Review Improves Recall But Leaves Noise

- Axis: report aggregation
- Claims: `CLM-018`, `CLM-019`
- Stakes: simple aggregation increases coverage and false-positive handling load.
- Type: contextual
- Disposition: resolved for trial with central falsification
- Basis: independent candidates feed a verifier that returns to raw code, seeks counterevidence, and executes focused checks. Agreement counts only when the workbenches add different evidence. Only verified candidates enter root-cause deduplication.
- Remaining uncertainty: direct evidence comparing a separate verifier with same-model self-critique is limited.

## CTR-008: Comment Every Concrete Issue Versus Protect Author Attention

- Axis: publication threshold
- Claims: `CLM-017`, `CLM-020`, `CLM-021`
- Stakes: publishing every plausible low issue harms trust; suppressing small real defects hides useful feedback.
- Type: product preference bounded by evidence
- Disposition: preference
- Basis: publish a low-priority issue only when it has a concrete trigger, consequence, evidence, changed-line anchor, and useful correction. Suppress style-only, mechanically enforced, speculative, and trivial comments.
- Remaining uncertainty: threshold calibration needs trial evidence.

## CTR-009: Worktree Isolation Versus Safe Execution

- Axis: target repository execution
- Claims: `CLM-010`, `CLM-011`
- Stakes: protecting the user's checkout does not prevent credential theft or host compromise.
- Type: resolved
- Disposition: resolved
- Basis: worktrees and copies provide disposable snapshots only. Every target command requires enforced isolation of the original checkout, Git administration, environment, credentials, metadata, service sockets, and network. If the boundary is unavailable, execution stops while static review continues.
- Remaining uncertainty: each harness exposes different controls, so the method defines required properties and demands recorded enforcement rather than naming one tool.

## CTR-010: Review Metrics Versus Released Quality

- Axis: evaluation evidence
- Claims: `CLM-017`, `CLM-022`
- Stakes: comment count, reviewer count, approval, or elapsed time can look healthy without finding material defects.
- Type: unresolved in general, bounded for workshop evaluation
- Disposition: contextual
- Basis: use seeded defects and explicit non-findings for the first evals. Score precision, recall, duplicates, false merges, anchors, evidence, and stack placement. Do not claim complete ground truth for real pull requests.
- Remaining uncertainty: real-world adaptive evaluation needs accepted and rejected comment outcomes over time.

## CTR-011: Shared Root Category Versus Independently Fixable Occurrences

- Axis: deduplication boundary
- Claims: `CLM-019`, `CLM-020`
- Stakes: broad grouping reduces noise but can hide an unfixed endpoint, taint path, or caller.
- Type: contextual
- Disposition: resolved by fix identity
- Basis: merge only when one minimal complete correction cures every reported path. Keep independently fixable occurrences separate, even when they share a rule, sink, or category. A reporting cluster may connect them without collapsing the comments.
- Remaining uncertainty: false merge rate needs the TypeScript fixtures and later real-use evidence.
