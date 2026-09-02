# Batch 001: Code Review Foundations

Status: converged
Started: 2026-07-13
Research cutoff: 2026-07-13

## Objective

Build enough evidence to choose the first review method and define its verification, deduplication, and evaluation rules.

## Corpus Snapshot

- Two local review protocols: Security Lens Review and Rules Review.
- Primary research on modern code review and AI-assisted code review.
- Official Git, GitHub, security, and engineering guidance.
- Recent benchmarks and failure studies for LLM code review.

## Inclusion Rules

- Primary studies, official standards, official tool documentation, and first-party engineering guidance.
- Secondary sources only when they locate primary evidence or document a practitioner convention not available elsewhere.
- Claims with a direct bearing on method, safety, output quality, or evaluation.

## Exclusion Rules

- Vendor rankings without inspectable methods.
- Generic code review checklists without a reasoned link to an in-scope job.
- Advice that creates a language-specific permanent workbench.
- Sources whose only contribution repeats a stronger source.

## Assignments

| Lane | Territory | Independence rule | Stopping condition |
| --- | --- | --- | --- |
| Review science | Human and AI review evidence | Use research papers and original engineering studies | Consequential review claims have support and counterevidence |
| Pull request operations | Git, GitHub, local execution, and stacks | Use official tool and platform documentation | The review range and comment anchor method are mechanically defined |
| Review coverage | Failure classes, security, quality, and synthesis | Use standards and independent practitioner guidance | A small language-neutral workbench map and scorecard candidates emerge |
| Method falsification | Counterexamples to provisional routing, retrieval, verification, deduplication, stack placement, execution, and evaluation rules | Challenge the provisional method with primary or official evidence without reading sibling lane reports | Every consequential provisional rule is kept, narrowed, replaced, or left as debt |
| Local protocols | The two owner-authored review protocols | Treat protocols as workflow requirements and prior practice, not domain proof | Borrow, revise, and reject decisions are explicit |

## Lane Outcomes

| Lane | Outcome | Yield |
| --- | --- | --- |
| Review science | completed | changed workbench independence, retrieval, test evidence, evaluation, and comment-threshold decisions |
| Pull request operations | completed | defined exact ranges, platform reconciliation, safe execution, comment anchors, and stack topology |
| Review coverage | failed after one retry | no usable report; overlap exists in the local protocols, NIST, OWASP, and falsification evidence; gap retained as `THR-006` |
| Method falsification | completed | corrected routing, verification, deduplication, stack placement, sandboxing, and repeated-trial rules |
| Local protocols | completed | preserved workflow goals while revising persona, voting, and broad root-grouping assumptions |

## Failed-Lane Coverage Map

This map does not claim that the failed coverage lane had no possible unique yield. It records why the current method can move to bounded trials without hiding the gap.

| Lost territory | Replacement evidence | Method records | Remaining limit |
| --- | --- | --- | --- |
| Failure classes | review-science lane, method-falsification counterexamples, Google review guidance, NIST SSDF | `CLM-001` through `CLM-011`, `CTR-001` through `CTR-004`, `CTR-007`, `CTR-009` | unique workbench yield remains trial debt |
| Security and privacy | local security protocol, NIST SSDF, OWASP prompt-injection and secure-review guidance, npm lifecycle documentation | `CLM-005`, `CLM-010`, `CLM-011`, `CLM-026`, `CTR-006`, `CTR-009` | runtime isolation must be proven by hostile canaries |
| Quality and maintainability | review-science studies, local robustness protocol, Google comment and test guidance | `CLM-003`, `CLM-006` through `CLM-008`, `CLM-017`, `CLM-021`, `CLM-022` | real pull requests need maintainer dispositions |
| Synthesis and deduplication | method-falsification lane, NIST root-cause guidance, SARIF location rules, multi-fault evidence | `CLM-018` through `CLM-020`, `CLM-025`, `CTR-007`, `CTR-011` | false merges and duplicate escape need public conformance and regression trials |

## Expected Outputs

- `research/ledger/sources/001-sources.md`
- `research/ledger/claims/001-claims.md`
- `research/ledger/contradictions/001-contradictions.md`
- `research/ledger/methods/001-review-method.md`
- `research/convergence/001-code-review-foundations.md`
- stable notes promoted to `library/notes/`

## Yield And Decision

Decision: converge.

Two independent external research lanes, one adversarial method-falsification lane, and the local-protocol lane changed consequential method choices. The coverage map bounds the failed lane without claiming it had no unique yield. The unresolved questions now depend on executable trials and real review outcomes. Promote the single pull request workflow, keep the stack workflow as a dependent draft, and retain the missing coverage lane as explicit debt.
