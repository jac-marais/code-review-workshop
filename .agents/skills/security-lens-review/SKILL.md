---
name: security-lens-review
description: Run a multi-lens security review of a codebase or code changes using parallel reviewer personas (Cynic, Skeptic, Nyaya, Confucian, Stoic) plus orchestrator synthesis. Use when the user asks for a security lens review, four-lens review, five-lens review, persona-based security review, disposition review, or a deep security audit of an architecture, security surface, PR, or diff that should go beyond a single-pass checklist.
---

# Security Lens Review

Orchestrate a security review through five independent reviewer lenses, then synthesize. Each lens asks an orthogonal question about the same scope. The value is: parallel independent passes, bounded evidence-cited findings, an anti-overreach guard, and a synthesis that ranks remediation.

Use this for depth on a security surface or a high-stakes change, where a single-pass checklist scan is not enough.

## Orchestrated workbench mode

Use this mode when [`review-code-change`](../review-code-change/SKILL.md) invokes this skill as the `security-and-privacy` workbench.

- Use the scope and evidence that the review lead supplies. Do not run a target command or write separate review artifacts.
- Run the existing five-lens procedure, then return candidates in the shape from [`candidate-and-output.md`](../review-code-change/references/candidate-and-output.md), plus cleared behavior, limits, evidence, and one `security-and-privacy` completion receipt.
- The review lead owns final verification, deduplication, and user-facing output. Zero candidates is valid.

The remaining workflow applies only to a direct security review.

## The lenses

| Lens | Role | Question | Prompt file |
|------|------|----------|-------------|
| Cynic | Ruthless subtractor | What is hollow? What can be removed? | [lenses/cynic.md](lenses/cynic.md) |
| Skeptic | Calibration engine | How confident are we? What is unverified? | [lenses/skeptic.md](lenses/skeptic.md) |
| Nyaya | Logic auditor | Is the reasoning chain valid? | [lenses/nyaya.md](lenses/nyaya.md) |
| Confucian | Naming & relations | Do names match reality? | [lenses/confucian.md](lenses/confucian.md) |
| Stoic | Failure rehearsal | What could go wrong? | [lenses/stoic.md](lenses/stoic.md) |

Read each lens file and include its contents verbatim in the subagent prompt. Do not paraphrase the lens rules.

## Workflow

### Phase 0: Scope (orchestrator)

Resolve what is under review:

- **System surface** (default when the user names an area: "auth layer", "security surface", "the architecture"): build an explicit file list of security-relevant code, including auth, session, consent, secrets handling, signing, upload/media paths, route guards, migrations, config, and security tests.
- **Branch changes**: diff against the merge-base with the default branch.
- **Uncommitted changes**: `git diff` of the working tree.

Write a self-contained **Scope Brief** that every subagent receives. Subagents inherit no chat context. Include: absolute repo path, review mode, file list or diff summary, in/out of scope, and domain context that changes stakes (e.g. "health data app", "server-authoritative SPA").

### Phase 1: Recon (optional)

For large system reviews only, launch one read-only `explore` subagent to map the surface: entrypoints, key files, claimed invariants from docs or decision logs. Use the result to sharpen the Scope Brief. Do not feed one lens's output to another. Skip recon for diffs under ~500 changed lines.

### Phase 2: Lens passes (always parallel)

Launch all five lens subagents in a single message:

- `subagent_type: explore` (use `generalPurpose` only if heavy diff parsing is required)
- `readonly: true`
- `run_in_background: false` unless the user asked for background

Each subagent prompt has this shape:

```text
Perform a security code review of <absolute repo path> through exactly one lens.

<Scope Brief>

<verbatim contents of the lens file>

Return markdown only, matching the lens output schema. Cite file:line and function for every finding. 2-5 findings. No generic advice.
```

Lenses must not see each other's output. If a subagent fails from a malformed invocation, fix and retry once; for any other failure retry once with the same prompt; if it fails again, proceed with the remaining lenses and note the gap in the README.

### Phase 3: Hamartia check (orchestrator)

Apply [templates/hamartia.md](templates/hamartia.md) to each lens output. Trim over-produced lenses to their top 3-4 findings and record the check outcome for the README.

### Phase 4: Spot-check (orchestrator)

A subagent summary is a claim, not evidence. Independently verify at least 2 findings per lens by reading the cited lines. Drop findings whose citations do not hold; downgrade findings whose severity was overstated. Record what was verified.

### Phase 5: Synthesis (orchestrator only, never delegate)

Write the synthesis using [templates/synthesis.md](templates/synthesis.md):

- Themes where 2+ lenses converge on the same risk from different angles
- Standalone severe single-lens findings, marked as such
- P0-P3 remediation order
- Explicit out-of-scope list

### Phase 6: Artifacts

Write the review to a dated folder under the ignored local work root:

```text
<workshop-root>/review-work/security-reviews/<YYYY-MM-DD>/
├── README.md        # from templates/readme.md
├── 01-cynic.md
├── 02-skeptic.md
├── 03-nyaya.md
├── 04-confucian.md
├── 05-stoic.md
└── synthesis.md
```

Resolve `<workshop-root>` from the repository that contains this skill. Do not write the review into the reviewed checkout.

### Phase 7: Chat summary

Report compactly, not the full report:

- One line per theme with convergence count (e.g. "3 lenses flagged the test-auth bypass")
- P0 items only, unless the user asks for the full dump
- Link to the artifact folder

Do not fix findings unless the user explicitly asks.

## Extending the lens set

To add a lens, add a file to `lenses/` with the same structure (question, refusals, focus, output schema) and launch it alongside the others. Nothing in this workflow assumes a fixed lens count. Mark lenses that do not come from the source paper as extensions, the way [lenses/stoic.md](lenses/stoic.md) does.

## Attribution

You are running a derived workflow. The core lens prompts, Hamartia self-check, and Reviewer ordering in this skill trace to one published study on AI-assisted code review.

### Source

- **Author:** Kaushal Bansal
- **Title:** *Philosophical Dispositions as Behavioral Constraints for AI-Assisted Code Review: An Empirical Study*
- **Link:** https://arxiv.org/abs/2605.23108
- **ID:** arXiv:2605.23108 (2026)

### What this skill uses from the paper

Bansal defines 10 dispositions and 8 role protocols in the full study. This skill implements the **Reviewer** role: Cynic, then Skeptic, then Nyāya, then Confucian. The prompt text for those four lenses matches Appendix A.

The **Stoic** lens is our extension. The paper names the Stoic disposition and its question ("What could go wrong?") but publishes no prompt for it, and the study's results do not cover it. We wrote the Stoic refusals and output schema ourselves; treat its findings with that in mind.

If you want Epicurean, Aristotelian, Daoist, Talmudic, Zen, or the other role protocols, read the paper. They are not included here.

### Tradition behind each lens

**Cynic.** Diogenes' Cynicism.

**Skeptic.** Pyrrhonist Skepticism.

**Nyāya.** Navya-Nyāya logic.

**Confucian.** Confucian relational ethics.

**Stoic.** Greek Stoicism; premeditatio malorum, the rehearsal of what could go wrong before committing.

**Hamartia.** The paper's self-check when a lens over-produces on a small diff (for example, more than 7 findings on under 300 lines). See [templates/hamartia.md](templates/hamartia.md) for the correction questions.
