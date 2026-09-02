---
name: review-robust-rules
description: Evaluate plans, pull requests, or code diffs against the Rules for Robust Software and return all findings without applying fixes. Use when reviewing code changes, evaluating a plan, auditing a PR, or when the user asks for a robustness review.
---

# Review Against Robust Rules

Evaluate code changes against the **Rules for Robust Software** checklist. This skill works on any language or codebase.

## Orchestrated workbench mode

Use this mode when [`review-code-change`](../review-code-change/SKILL.md) invokes this skill as the `design-and-maintainability` workbench.

- Use the scope and evidence that the review lead supplies. Do not create a worktree, run a target command, or write a separate report.
- Apply the existing rules and checklist, then return candidates in the shape from [`candidate-and-output.md`](../review-code-change/references/candidate-and-output.md), plus cleared behavior, limits, evidence, and one `design-and-maintainability` completion receipt.
- The review lead owns final verification, deduplication, and user-facing output. Zero candidates is valid.

The remaining workflow applies only to a direct robustness review.

## Report output

All PR review reports must live under `<workshop-root>/review-work/pr-reviews/`. All review worktrees must live under `<workshop-root>/review-work/worktrees/`. Resolve `<workshop-root>` from the repository that contains this skill. Do not save these files in the reviewed checkout.

For PR reviews, write the report to `<workshop-root>/review-work/pr-reviews/{github_org}_{repo}_pr_{number}.md` using snake case. For example, a review of `example-org/example-repo` PR #86 must be written to `<workshop-root>/review-work/pr-reviews/example_org_example_repo_pr_86.md`.

For PR reviews, create the isolated review worktree under `<workshop-root>/review-work/worktrees/`, using a clear name such as `<repo>-pr-<number>`. For example, a review of `example-org/example-repo` PR #86 should use `<workshop-root>/review-work/worktrees/example-repo-pr-86/`. This keeps the report, review checkout, and temporary review artifacts in one ignored local work area.

For PR reviews, also read **[PRs.md](PRs.md)** for additional review guidelines covering security, naming, API contract drift, CI efficiency, cross-project patterns, and draft message formatting.

## Workflow

### Step 1: Gather the changes

Determine what you are reviewing:

| Input | How to gather |
|---|---|
| **PR / branch** | Fetch the live PR base and head from GitHub (see below), diff against the fetched remote base ref, then read the changed files |
| **Staged changes** | `git diff --cached` |
| **Unstaged changes** | `git diff` |
| **Plan document** | Read the plan file directly |
| **Specific files** | Read the files the user points to |

#### PR branch checkout

When reviewing a PR, you need the actual branch checked out so you can read the full files in context, not just the diff hunks.

1. **Record the current checkout state.** Run `git status`. Do not stash, discard, or otherwise change the user's work.
2. **Use a dedicated worktree.** Create it under `<workshop-root>/review-work/worktrees/<repo>-pr-<number>/`. Never check out the pull request in the user's working tree.
3. **Resolve the live PR refs from GitHub.** Use `gh pr view <number> --json baseRefName,headRefName,headRefOid` to get the base branch and exact PR head commit. Do **not** trust a local `main`/`master` or any existing local branch state for PR review.
4. **Fetch the live base branch before diffing.** Run `git fetch origin <baseRefName>` so `origin/<baseRefName>` reflects the current target branch on GitHub.
5. **Check out the exact incoming head.** Prefer `git fetch origin pull/<number>/head` and create the review worktree from `FETCH_HEAD`, or otherwise verify the checked-out commit matches `headRefOid`.
6. **Diff against the fetched remote base ref.** Use `git diff origin/<baseRefName>...HEAD` for the full diff. Never use `git diff <base>...HEAD` if `<base>` resolves to a local branch that may be stale.
7. **Validate the reviewed file set against GitHub.** Use `gh pr diff <number>` or `gh api repos/<org>/<repo>/pulls/<number>/files` as the source of truth for which files are actually in the PR. If your local diff shows files that are not in GitHub's PR file list, stop, refetch, and fix the review checkout before continuing.

Read every changed file **in full** so you have surrounding context, not just the diff hunks.

### Step 2: Read the rules and run the checklist

Before evaluating, read **both** reference files:

1. **[rules.md](rules.md)**: the full Rules for Robust Software with principles, examples, and rationale for each rule. Read this first to internalize the intent behind each rule.
2. **[checklist.md](checklist.md)**: the detailed detection steps and severity guide for each rule.

Then work through each rule in order (Rule 0 → Rule 5). For every rule:

1. Refer to `rules.md` to understand the principle and its "why."
2. Follow the detection steps described in `checklist.md`.
3. Record any violations you find.
4. Classify each violation's severity (see Step 3).

### Step 3: Classify severity

| Severity | Criteria | Action |
|---|---|---|
| **Major** | Likely bug, data leak, or invalid state that will cause production issues. Violates Rule 0, 1, or 4 in a way that creates an impossible-to-catch-at-compile-time defect. | **Report**: explain the issue and suggest a fix. |
| **Medium** | Structural concern that increases maintenance cost or makes future bugs more likely. Typically violates Rule 2, 3, or 5 in a way that won't cause an immediate defect but degrades quality. | **Report**: explain the issue and suggest a fix. |
| **Low** | Stylistic or minor organizational suggestion. The code works and is safe, but could be cleaner. | **Report**: mention briefly, no pressure. |

### Step 4: Act on findings

All findings, including Major, Medium, and Low findings, go into the report only. Do not apply fixes. The user decides what to address.

### Step 5: Present the report

For PR reviews, follow the anchor format in **[PRs.md](PRs.md)**:

- Every finding must include exactly one **Anchor** block.
- The quoted code under that anchor is the intended GitHub inline-comment anchor.
- If a finding references multiple files or non-contiguous spans, choose one anchor and list the rest as supporting evidence.
- Every violation/finding must include a blockquote line immediately after its heading in this exact format: `> Rule {num}: {short title}`.

Use these canonical short titles:

- `Rule 0`: `One Decision, One Place`
- `Rule 1`: `Data for State, Functions for Processes`
- `Rule 2`: `Group Code by What It Does`
- `Rule 3`: `Repetition Is Okay, but Not Encouraged`
- `Rule 4`: `Use Type-Safe Structures`
- `Rule 5`: `Validate at Boundaries, Trust Internally`

Use the template below for severity sections and finding content. Each finding ends with a `draft message` block: a ready-to-post comment in a friendly, direct tone using full sentences.

```
## Robustness Review

### Critical (Major)

#### N. [Rule N] Title

> Rule N: Short Title

**Anchor:** `file:line` or function name

Quoted anchor snippet

**Supporting evidence:** `file:line` (optional)

Quoted supporting snippet

**What:** Description of the concern.

**Why it matters:** One sentence on the risk.

**Suggested fix:** Concrete suggestion.

```draft message
Ready-to-post PR comment. Friendly, direct, full sentences. Cite specific files and code.
```

### Needs Discussion (Medium)

#### N. [Rule N] Title

> Rule N: Short Title

**Anchor:** `file:line` or function name

Quoted anchor snippet

**Supporting evidence:** `file:line` (optional)

Quoted supporting snippet

**What:** Description of the concern.

**Why it matters:** One sentence on the risk.

**Suggested fix:** Concrete suggestion.

```draft message
Ready-to-post PR comment. Friendly, direct, full sentences. Cite specific files and code.
```

### Optional Improvements (Low)

#### N. [Rule N] Title

> Rule N: Short Title

**Anchor:** `file:line`

Quoted anchor snippet

**Supporting evidence:** `file:line` (optional)

Quoted supporting snippet

**What:** Brief suggestion.

```draft message
Ready-to-post PR comment.
```
```

If a severity bucket is empty, omit that section. If everything passes, say:

> All changes pass the robustness checklist. No issues found.

## Important guidelines

- **Be concrete.** Always cite the specific file, function, or line.
- **No false positives.** If you're unsure whether something is a violation, lean toward "not a violation." Only flag what you can clearly justify.
- **Respect intent.** A one-off inline expression is not a Rule 3 violation. Only flag premature abstraction when there is actual evidence of a junk-drawer function/class.
- **Language-agnostic.** The checklist examples use JavaScript/TypeScript, but the principles apply to any language. Adapt detection steps to the language at hand (e.g., pattern matching in Rust, sealed classes in Kotlin, dataclasses in Python).
