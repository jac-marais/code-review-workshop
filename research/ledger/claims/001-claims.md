# Batch 001 Claim Ledger

Status values: `accepted`, `bounded`, `rejected`, or `open`.

## Review Topology

### CLM-001: Use A Small Set Of Distinct Scenario-Based Workbenches

- Statement: Distinct review scenarios produce more useful diversity than several generic reviewer prompts, while additional interchangeable reviewers show diminishing returns. Routing may add specialists but must not remove the mandatory baseline.
- Kind: empirical finding plus design inference
- Scope: candidate discovery
- Support: `SRC-003`, `SRC-004`, `SRC-045`, `SRC-047`
- Challenge: `SRC-045` has author-only matching; the best modern workbench set has not been established experimentally.
- Derivation: source-explicit for human perspective-based reading and multi-review variability; inferred for the exact workshop design
- Certainty: medium
- Status: accepted with a public conformance unique-yield gate
- Method effect: run the mandatory baseline on every change, then add change-triggered specialists. Independence requires a different method or evidence obligation, not a different persona name.

### CLM-002: Keep Discovery Independent Until Candidate Reports Exist

- Statement: Workbenches should not see one another's findings during discovery because independent analysis improves coverage and avoids anchoring.
- Kind: empirical finding plus design inference
- Scope: orchestration
- Support: `SRC-003`, `SRC-014`, `SRC-045`, `SRC-047`
- Challenge: direct evidence on LLM workbench isolation is limited.
- Derivation: inferred from human meetingless inspection, anchoring, and model-run variability
- Certainty: medium
- Status: accepted
- Method effect: synthesis starts only after every discovery report is frozen.

### CLM-003: A Generic Checklist Is Not A Workbench Method

- Statement: A useful workbench needs a failure model, retrieval plan, procedure, evidence target, exclusions, and self-calibration rule; a category label or generic checklist is insufficient.
- Kind: empirical finding plus workshop design choice
- Scope: workbench definition
- Support: `SRC-003`, `SRC-004`, `SRC-045`
- Challenge: older inspection studies do not prove that every modern agent checklist fails.
- Derivation: source-explicit for scenario methods versus generic checklists; inferred for the required workbench fields
- Certainty: medium
- Status: accepted
- Method effect: each workbench specification defines how it reasons, not only what topics it names.

## Context And Intent

### CLM-004: Repository Access Helps, Flattened Context Can Hurt

- Statement: Reviewers need repository context and project conventions, but feeding broad flat context into every model can reduce detection and increase fabricated details.
- Kind: contextual contradiction resolved by method
- Scope: retrieval
- Support: `SRC-005`, `SRC-017`, `SRC-020`, `SRC-046`, `SRC-047`
- Challenge: `SRC-046` is a recent preprint with a Python-heavy sample and one context representation.
- Derivation: source-explicit
- Certainty: medium-high
- Status: accepted
- Method effect: give workbenches repository tools and a focused scope brief. Let them retrieve progressively along named call, data, contract, configuration, and deployment edges. Force wider search for public contracts, shared state, dynamic registration, trust boundaries, deletions, and conflicting runtime evidence. Do not dump the repository into the prompt.

### CLM-005: Separate Code-First And Intent-Aware Review

- Statement: Pull request prose and commit metadata help reconstruct requirements but can bias security judgments, so code-first discovery should not receive persuasive metadata.
- Kind: empirical finding plus design inference
- Scope: security and intent
- Support: `SRC-018`, `SRC-020`
- Challenge: the real-pipeline bias study covers 17 CVEs and Claude Code configurations.
- Derivation: source-explicit for bias and metadata-redaction effect; inferred for the two-context workshop method
- Certainty: medium-high for security review, open for other workbenches
- Status: accepted for security and high-risk trust-boundary passes
- Method effect: run a metadata-redacted code-first security pass and a separate intent-aware behavior pass. Reconcile differences during verification.

### CLM-006: Repository Familiarity Changes Comment Usefulness

- Statement: Review claims about conventions, ownership, or design need surrounding code and history because first-time reviewers produce less useful comments.
- Kind: empirical finding
- Scope: project-specific claims
- Support: `SRC-005`, `SRC-020`, `SRC-047`
- Challenge: usefulness is not identical to defect correctness.
- Derivation: source-explicit for the usefulness association; inferred for the requirement to inspect surrounding code and history
- Certainty: medium
- Status: accepted
- Method effect: search local patterns and history before claiming a project rule. Abstain when the repository does not establish the convention.

## Execution And Evidence

### CLM-007: Static Review And Executable Validation Are Complementary

- Statement: Review, automated analysis, and executable testing find different failures and should inform one another.
- Kind: standard plus practitioner evidence
- Scope: validation
- Support: `SRC-010`, `SRC-044`
- Challenge: neither source defines which checks a specific repository can run.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: build a change-specific validation plan after mapping the change, then share verified results with relevant workbenches.

### CLM-008: Green Tests Do Not Prove The Change

- Statement: A reviewer must inspect changed tests, ask whether they would fail for broken behavior, and record exactly which behavior ran.
- Kind: practitioner evidence
- Scope: test evidence
- Support: `SRC-010`, `SRC-011`
- Challenge: no single test-reading order works for every change.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: the evidence workbench checks test validity and execution coverage, not only command exit codes.

### CLM-009: Compare Base, Head, And Integration States When Material

- Statement: Running checks only at the pull request head cannot distinguish pre-existing failures or current-base integration failures.
- Kind: operational inference
- Scope: local execution
- Support: `SRC-023`, `SRC-024`, `SRC-025`, `SRC-038`
- Challenge: three-state execution can be wasteful for a small, isolated change.
- Derivation: synthesizer inference from diff and CI semantics
- Certainty: high
- Status: accepted with a materiality trigger
- Method effect: start with focused head validation. Add base comparison for failures and current-base merge validation for integration-sensitive changes.

### CLM-010: A Worktree Protects Files, Not The Host

- Statement: Detached worktrees keep validation out of the user's checkout but do not sandbox executed code, credentials, hooks, network, or repository administration.
- Kind: operational fact
- Scope: execution safety
- Support: `SRC-028`, `SRC-040`, `SRC-044`
- Challenge: a sandbox name does not prove specific mount, credential, metadata, or network controls.
- Derivation: source-explicit for worktree and CI risk, inferred for the execution policy
- Certainty: high
- Status: accepted
- Method effect: use worktrees or copies only for disposable snapshots. Run every target command inside an enforced boundary that protects the original checkout, Git administration, host credentials, metadata, service sockets, and network.

### CLM-011: Immutable Installs Detect Drift But Still Execute Code

- Statement: Immutable package installs prevent silent lockfile repair, but lifecycle scripts remain executable review surface.
- Kind: operational fact
- Scope: dependency validation
- Support: `SRC-035`, `SRC-036`, `SRC-040`
- Challenge: repositories may require tool-specific setup outside standard package managers.
- Derivation: source-explicit plus security inference
- Certainty: high
- Status: accepted
- Method effect: detect the package manager, inspect lifecycle scripts as reconnaissance, use frozen install mode, and enforce the execution boundary before installing.

## Review Target And GitHub Output

### CLM-012: Platform And Local Git Views Are Both Required

- Statement: GitHub metadata and the platform diff define the review target and valid anchors, while local Git supplies full inventory, history, rename analysis, submodule detail, and executable context.
- Kind: operational synthesis
- Scope: intake and anchoring
- Support: `SRC-023`, `SRC-024`, `SRC-026`, `SRC-027`, `SRC-031`
- Challenge: local and platform inventories can legitimately disagree.
- Derivation: synthesizer inference from official behavior
- Certainty: high
- Status: accepted
- Method effect: freeze both views, reconcile mismatches, and never treat either as complete by itself.

### CLM-013: Verify Exact OIDs And Every Best Merge Base

- Statement: A pull request review must use the platform base and head OIDs and detect multiple best merge bases before claiming an exact range.
- Kind: operational fact
- Scope: revision verification
- Support: `SRC-023`, `SRC-024`, `SRC-025`, `SRC-030`
- Challenge: a local-only uncommitted change has no platform OIDs.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: fetch exact objects, deepen shallow history when needed, run `merge-base --all`, and use a separate local-change intake path.

### CLM-014: Fetch Every GitHub Discussion Surface Before Deduplication

- Statement: Inline review comments, general issue comments, review bodies, review threads, replies, resolved state, and outdated state are separate data and must all be considered.
- Kind: platform fact
- Scope: existing-comment deduplication
- Support: `SRC-031`, `SRC-032`, `SRC-033`, `SRC-034`
- Challenge: non-GitHub workflows expose different discussion models.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: use a platform adapter when available, or record that existing-comment deduplication is incomplete.

### CLM-015: Revalidate Head And Anchors Immediately Before Output

- Statement: A head push can invalidate execution evidence and line anchors, so the reviewer must refetch the head and discussions before final output or posting.
- Kind: platform fact plus race guard
- Scope: publication
- Support: `SRC-031`, `SRC-033`, `SRC-034`
- Challenge: a local-only review has no platform race.
- Derivation: source-explicit for SHA anchoring, inferred for the final race check
- Certainty: high
- Status: accepted
- Method effect: stale evidence stops publication until affected checks and anchors rerun.

### CLM-016: Inline Comments Need A Causal Changed-Line Anchor

- Statement: A real issue without a useful changed-line anchor should not be attached to unrelated code merely to make it publishable.
- Kind: platform constraint plus product choice
- Scope: comment output
- Support: `SRC-031`, `SRC-021`
- Challenge: some platforms allow file-level comments or general review bodies.
- Derivation: source-explicit for line and side; owner preference for inline comments
- Certainty: high
- Status: accepted
- Method effect: keep unanchorable issues in a limitation or summary record, not the inline comment set.

## Synthesis, Precision, And Comments

### CLM-017: Raw Finding Count Is A Harmful Success Metric

- Statement: Current AI review systems trade recall against false positives and low-value output, so comment count cannot measure quality.
- Kind: empirical finding
- Scope: evaluation
- Support: `SRC-015`, `SRC-016`, `SRC-017`, `SRC-019`, `SRC-046`, `SRC-047`
- Challenge: benchmark precision and usefulness definitions differ.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: score verified recall, precision, signal-to-noise, duplicate escape, actionability, and high-severity misses together.

### CLM-018: Aggregate Candidates, Then Adversarially Verify Them

- Statement: Independent reports can improve recall, but aggregation alone leaves a false-positive problem and must feed a separate falsification gate.
- Kind: empirical finding plus design inference
- Scope: synthesis
- Support: `SRC-016`, `SRC-045`, `SRC-047`
- Challenge: direct trials of a separate verifier versus same-model aggregation remain limited.
- Derivation: source-explicit for aggregation gains and residual precision problem; inferred for verifier design
- Certainty: medium
- Status: accepted for trial
- Method effect: the synthesizer normalizes candidates. A verifier returns to raw code and tries to disprove each candidate before deduplication and comment drafting. Workbench agreement matters only when it adds different evidence. High-impact findings need executable, complete static or type, or strong contract proof. Fresh-context agreement can corroborate but cannot replace that proof.

### CLM-019: Deduplicate By Invariant, Cause, And Failure Path

- Statement: Candidates describe the same issue only when they share the counterfactual defect, first failing state, trigger or failure mechanism, and one minimal complete fix that cures every reported path.
- Kind: workshop design inference
- Scope: deduplication
- Support: `SRC-044`, `SRC-045`, `SRC-047`, plus local protocols `SRC-001` and `SRC-002`
- Challenge: false merges can hide distinct defects and need explicit evaluation.
- Derivation: synthesizer inference
- Certainty: medium
- Status: accepted for trial
- Method effect: line number and wording are excluded from stable issue identity. Independently fixable occurrences remain separate even when they share a rule, sink, or category. The scorecard tracks duplicate escape and false merge rates.

### CLM-020: One Cause With Several Manifestations Produces One Primary Comment

- Statement: When several workbenches or files expose one root cause and one minimal fix cures every path, publish one comment where the fix belongs and cite other manifestations as evidence.
- Kind: workshop product choice
- Scope: comment synthesis
- Support: `SRC-044`, local protocols `SRC-001` and `SRC-002`
- Challenge: one apparent cause can conceal different fixes or trust boundaries.
- Derivation: owner preference plus root-cause practice
- Certainty: medium
- Status: accepted for trial
- Method effect: the verifier must reject a merge when trigger, failure mechanism, or fix direction differs.

### CLM-021: Fix Directions Need Repository Evidence

- Statement: Suggested fixes should describe the smallest sensible direction and avoid authoritative patches unless repository conventions and validation support the exact edit.
- Kind: empirical finding plus product choice
- Scope: comment drafting
- Support: `SRC-019`, `SRC-021`
- Challenge: exact patches can be useful for simple mechanical fixes.
- Derivation: source-explicit for low AI suggestion adoption and intent mismatch; owner chose offer-only behavior
- Certainty: medium-high
- Status: accepted
- Method effect: comments explain the correction first. Include a patch snippet only when it removes ambiguity and has been checked against the repository.

### CLM-022: Automated Review Assists, It Does Not Approve

- Statement: Current evidence does not support using an AI review as sole merge approval, especially for security, business logic, and project-specific behavior.
- Kind: empirical limit and safety policy
- Scope: release authority
- Support: `SRC-016`, `SRC-017`, `SRC-018`, `SRC-019`, `SRC-046`, `SRC-047`
- Challenge: narrow documented-rule checks can reach useful production quality after suppression.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: the workshop returns comments and limits. It never approves, requests changes, or merges unless a separate explicit workflow authorizes that action.

## Stack Review

### CLM-023: Detect Stack Topology From Metadata And Ancestry

- Statement: Parent-based and overlapping trunk-based stacks expose different platform diffs, so the reviewer must prove topology instead of assuming one model.
- Kind: tool behavior plus design inference
- Scope: stacked pull requests
- Support: `SRC-025`, `SRC-041`, `SRC-042`
- Challenge: stale, mixed, or DAG-shaped stacks may not admit a clean linear decomposition.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: classify dependent, overlapping, mixed or stale, or DAG topology. Stop exact per-pull-request attribution when ancestry and metadata disagree.

### CLM-024: Review Stacks Locally And Globally

- Statement: Per-parent review improves local coherence and placement, while a base-to-tip review finds cross-pull-request integration failures.
- Kind: empirical finding plus design inference
- Scope: stacked pull requests
- Support: `SRC-007`, `SRC-023`, `SRC-024`, `SRC-041`, `SRC-042`
- Challenge: decomposition did not increase defect count in the controlled study.
- Derivation: source-explicit for decomposition precision, inferred for dual stack review
- Certainty: medium
- Status: accepted for trial
- Method effect: review every proved edge, carry a compact verified ledger root to tip, then run a cumulative integration pass.

### CLM-025: Place A Stack Finding By First-Failing Prefix And Fix Ownership

- Statement: A final stack finding belongs on the first cumulative prefix where the relevant invariant becomes false, anchored where the smallest complete fix belongs.
- Kind: workshop design inference
- Scope: stack attribution
- Support: `SRC-024`, `SRC-025`, `SRC-041`, `SRC-042`, `SRC-043`
- Challenge: an upstream primitive can become unsafe only after a downstream caller completes the path.
- Derivation: synthesizer inference
- Certainty: medium
- Status: accepted for trial
- Method effect: compare cumulative states. Attribute to the downstream pull request when that change completes the unsafe path, even if it calls an upstream primitive. Recheck the pinned stack graph and SHAs before output.

### CLM-026: All Repository Material Is Untrusted Data

- Statement: Metadata redaction does not remove prompt injection because instructions may appear in code comments, docs, tests, logs, tool output, and commit data.
- Kind: security guidance
- Scope: agent authority
- Support: `SRC-049`, local protocols `SRC-001` and `SRC-002`
- Challenge: read-only access reduces impact but does not prevent reasoning manipulation.
- Derivation: source-explicit
- Certainty: high
- Status: accepted
- Method effect: fixed workshop authority outranks repository text. Discovery workbenches use read-only tools and structured outputs. Only an explicitly authorized publisher may create external comments.

### CLM-027: Evaluation Needs Repeated Runs And Stated Scope

- Statement: Two TypeScript fixtures can prove thin-slice operability but cannot validate broad language support, and nondeterministic agent runs require a stability measure.
- Kind: evaluation standard plus design inference
- Scope: workshop validation
- Support: `SRC-046`, `SRC-057`
- Challenge: repeated runs increase evidence volume without creating broader test diversity.
- Derivation: source-explicit for generalization and nondeterminism, inferred for trial count
- Certainty: high
- Status: accepted
- Method effect: run each public conformance and regression trial at least three times, score run-to-run stability, and record Go, Python, framework, and real-pull-request validation as debt.
