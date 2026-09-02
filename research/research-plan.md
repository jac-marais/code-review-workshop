# Research Plan

Research cutoff: 2026-07-13
Current batch: [`001-code-review-foundations`](batches/001-code-review-foundations.md)

## Question

What method lets a harness-neutral agent review one pull request or a pull request stack deeply, run relevant code, combine independent workbenches, and return a small set of verified comments without changing the user checkout?

## Evidence Territories

1. Human code review science and practice: purposes, useful review scope, defect detection, comment quality, and reviewer limits.
2. AI-assisted review: context selection, false positives, false negatives, confirmation bias, independent passes, aggregation, and verification.
3. Pull request operations: merge-base correctness, local checkout facts, diff semantics, changed-line anchors, existing comments, and stack attribution.
4. Review coverage: language-neutral failure classes, security standards, reliability, data, contracts, tests, operations, performance, and user-facing behavior.
5. Synthesis and evaluation: issue identity, root-cause deduplication, severity, confidence, output contracts, scorecards, and public conformance and regression trials.

## Return Contract

Each lane returns:

- source receipts with exact locators and authority limits;
- atomic claims that could change the method, boundary, safety policy, or evaluation;
- counterexamples, contradictions, and negative results;
- method candidates with triggers, inputs, steps, outputs, and failure modes;
- unresolved questions with a clear reason they matter.

## Wave Sequence

### Wave 1: Broad independent survey

Run independent lanes for review science, pull request operations, and review coverage. Use different source pools. The lead agent separately studies the two local review protocols and current official guidance.

### Wave 2: Targeted falsification

Start only for consequential claims that remain weak or disputed after wave 1. At least one lane must use a source outside the first wave's citation network.

### Convergence

Normalize the evidence into sources, claims, contradictions, and method candidates. Select one thin single pull request review method only if it has an output contract, scorecard, and TypeScript trial plan. Keep stack review as an unnumbered dependency draft until the single pull request method works.

## Stop Rule

Stop the research milestone when:

- the priority review job has a source-backed candidate method;
- important conflicts about context, reviewer independence, verification, and comment volume have a recorded disposition;
- the method defines how it maps, executes, reviews, verifies, deduplicates, anchors, and reports;
- a TypeScript single pull request trial and a TypeScript stacked pull request trial can test the method;
- another research batch has no named uncertainty it is likely to reduce.

Research completion does not make the workshop operable. The selected workbench still needs a mounted skill and public conformance and regression trial.
