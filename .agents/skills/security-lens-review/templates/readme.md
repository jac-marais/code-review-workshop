# [Repo] Security Lens Review, [YYYY-MM-DD]

Structured five-lens review of [scope description]. Scope is [the current codebase | branch diff | uncommitted changes].

## Method

Each lens applies a different question independently. Findings are specific to a file, line, and function. They are not generic best-practice advice.

| Lens | Question | File |
|------|----------|------|
| Cynic | What is hollow? What can be removed? | [01-cynic.md](./01-cynic.md) |
| Skeptic | How confident are we? What is unverified? | [02-skeptic.md](./02-skeptic.md) |
| Nyaya | Is the reasoning chain valid? | [03-nyaya.md](./03-nyaya.md) |
| Confucian | Do names match reality? | [04-confucian.md](./04-confucian.md) |
| Stoic | What could go wrong? | [05-stoic.md](./05-stoic.md) |

Cross-lens themes and remediation order: [synthesis.md](./synthesis.md).

## Scope

**In scope**

- [paths / diff summary]

**Out of scope**

- [excluded surfaces, e.g. third-party library internals, live infra dashboards]

## Executive summary

[2-5 sentences: what is sound, then the numbered top risks.]

## Hamartia self-check

[Record whether any lens over-produced and what was trimmed. See skill templates/hamartia.md.]

## Spot-check verification

[Which findings the orchestrator independently verified against cited lines, and any that were dropped or downgraded.]

## Review agents

Findings compiled from five parallel reviews (Cynic, Skeptic, Nyaya, Confucian, Stoic dispositions).
