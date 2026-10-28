# Batch 002: Review Efficiency

Status: converged
Started: 2026-10-28
Research cutoff: 2026-10-28

## Objective

Find which parts of the review workflow spend tokens and time on repeated work, and which changes can cut that spend without lowering review quality. Whether findings were correct or acted on is out of scope.

## Corpus Snapshot

- The maintainer's local review archive under the git-ignored `review-work/pr-reviews/`, with 115 run directories.
- Local agent transcripts from Claude Code and Codex for 47 of those runs: 144 agent sessions with per-response usage.
- Saved per-workbench reports for 15 runs: 507 candidate units in 128 reports.
- Five multi-round series, totaling 27 rounds.

The archive and transcripts are private and are not distributed. The analysis scripts and full reports stay with them.

## Method

- Token accounting: deduplicated per-response usage, split into fresh input, cache-read input, and output. Each response was assigned to one workflow phase by its declared lane or its tool calls. File reads were matched across lanes to estimate duplicate content.
- Redundancy: an analyst clustered candidates by counterfactual defect, region, and fix, then matched them to final comments. Duplicate identity, lane attribution, and round lineage are judgments, not measurements.

## Findings

| Finding | Evidence | Kind |
| --- | --- | --- |
| Replayed context dominates cost | 96% of 813M input tokens are cache reads. Duplicate file reads across lanes add about 1.1M tokens, and explicit skill reads add about 1.1M. | measured |
| Agent count drives cost | Each agent's first five responses cost 150K to 250K tokens. Five-lane runs cost 20M to 120M tokens. Single-agent gates cost 2M to 10M. | measured |
| Lane-by-cluster cross products are the worst case | One run used five lanes on six or more clusters: 25 agents, 123M tokens, 223 candidates, 2 final comments. | measured |
| Lanes are not redundant | Pairwise overlap tops out at 11% to 12% Jaccard. 61% of attributable kept findings came from one lane. Every mandatory lane has unique kept findings. Two of three kept P1s came from one lane. | judged |
| Later rounds repeat whole reviews | One eight-round series cost 6M to 9M tokens per round, and about 1.3% of that was explicit delta work. 87% to 92% of later-round files were unchanged. | measured, with judged attribution |
| Later rounds still find real defects | Of 34 later-round findings, 13 were in fix code, 14 were residual counterexamples, and 7 were new. No unchanged defect was re-raised. | judged |
| Lanes re-derive briefed or open facts | 8 briefed facts were restated in 20 reports. Three lanes proved the same open schema fact. Lanes also corrected the brief 5 times. | judged sample |
| Nested security lenses repeat work | Five lenses converged on one defect in one review and found none across 242 files in another, repeating the file inventory 968 times. | measured |
| The candidate funnel is lost | Results keep final comments, not candidates, so rejection reasons cannot be counted. | measured |

## Decisions

- Keep all five mandatory lanes. Do not require agreement between lanes.
- Cap fan-out at five workbench agents. An extra cluster pass needs a named risk in `fan-out.json`.
- Start each workbench from a lead-built context pack, without re-reading workshop instructions or re-mapping the repository.
- Settle open facts that several lanes share before launch. Workbenches return established facts, which the lead folds into the brief.
- Re-review later heads in delta mode: interdiff, dependency closure, prior findings, and rerun prior counterexamples.
- Run security as one combined-lens pass by default, and escalate to five lenses on named triggers.
- Record every candidate and its disposition in `candidate-ledger.jsonl`, checked by the validator.

## Limits

- These are observational counts from one maintainer's archive, not randomized ablations. Quality retention under the new rules is untested.
- 228M tokens could not be assigned to a phase. Missing transcripts are missing spend, not zero.
- Duplicate-candidate matching is analyst judgment and can merge or split defects incorrectly.
