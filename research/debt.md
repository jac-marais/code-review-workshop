# Research Debt

## Open

- The efficiency rules from [batch 002](batches/002-review-efficiency.md) need a recall replay: rerun archived changes with known final findings, at least one large single change, one stack, and one multi-round series, and compare tokens and recall against the full protocol.
- Delta-mode dependency closure needs miss evidence from real re-reviews before it can skip unchanged clusters with confidence.
- Fix-based issue identity and deduplication need public conformance and regression examples and real-review dispositions.
- Progressive retrieval needs miss and false-positive evidence to tune its expansion triggers.
- Stack attribution needs a trial that distinguishes a valid upstream helper, a downstream activation, a repeated symptom, and an independently fixable later issue.
- Execution isolation needs harness-specific proof that target code cannot reach the original checkout, shared Git administration, host credentials, metadata, service sockets, or unapproved network destinations.
- Go and Python coverage will rely on method portability until later real-use evidence justifies separate regression cases.
- Existing-comment and anchor behavior outside GitHub remains untested.
- The standards-led coverage research lane returned no report after one retry. Rerun it only if trials expose a missing failure class.

## Closed

- Chose five mandatory language-neutral workbenches with triggered specialists.
- Kept all five workbenches after archive evidence showed each contributes unique kept findings; capped fan-out instead ([batch 002](batches/002-review-efficiency.md)).
- Chose progressive, question-led retrieval instead of diff-only or flat full-repository context.
- Chose fix-based deduplication with independently correctable findings kept separate.
- Chose first-failing-prefix plus fix ownership for stack placement.
- Chose disposable snapshots plus enforced sandboxing for every target command.
