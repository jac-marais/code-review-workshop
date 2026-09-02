# PR Review Guidelines

## Checking out the PR branch

Accurate line numbers and code quotes require reading the actual files on the PR branch, not just the diff. Before reviewing:

1. **Find the local repo.** Check the current working directory and known workspace roots. If the repo is not found, ask the user for its location. Do not clone a fresh copy if it already exists locally.
2. **Resolve the live PR refs from GitHub.** Use `gh pr view <number> --json baseRefName,headRefName,headRefOid` and treat those values as authoritative. Do not assume the local `main`/`master` branch is current.
3. **Fetch the live target branch.** Run `git fetch origin <baseRefName>` so `origin/<baseRefName>` matches GitHub's current target branch.
4. **Fetch and check out the incoming head commit.** Prefer `git fetch origin pull/<number>/head` and check out `FETCH_HEAD` in the review worktree, or otherwise verify the checked-out commit equals `headRefOid`.
5. **Diff against the fetched remote base ref.** Use `git diff origin/<baseRefName>...HEAD`, not `git diff main...HEAD` or any other local branch name that may be stale.
6. **Validate the file set against GitHub before reviewing.** Use `gh pr diff <number>` or `gh api repos/<org>/<repo>/pulls/<number>/files` as the source of truth for which files belong to the PR. If your local diff contains extra files, stop and fix the checkout before continuing.
7. **Read changed files in full** from the branch, not just the diff hunks. You need surrounding context to verify line numbers and understand the code.

For PR reviews, the checkout worktree must be created under `<workshop-root>/review-work/worktrees/`, using a clear name such as `<repo>-pr-<number>`. Do not place review worktrees in the reviewed checkout or any other location.

## Comment anchors and code quotes

Treat the quoted code span as the source of truth for the eventual GitHub review comment anchor.

### Primary anchor

Every PR finding must include exactly one **Anchor** block:

- The `Anchor` path is the file where you would attach the inline GitHub review comment.
- The quoted code under `Anchor` is the exact line or contiguous line range to anchor to.
- Include the target line(s) plus one line of context above and below.
- Use exact line numbers from the PR branch, not estimates from the diff.

Format:

````text
**Anchor:** `path/to/file.go`

```go
// functionName, lines 121-123:
hasSourceCode := input.SourceCode != nil && input.SourceCode.FileID != ""
if hasSourceCode && input.AgentBaseVersion != nil && *input.AgentBaseVersion != "" {
    resolved := resolveAgentBaseImage(s.agentBaseImage, *input.AgentBaseVersion)
```
````

### Findings with multiple locations

GitHub cannot attach one inline comment to multiple files or to non-contiguous ranges. When a finding spans multiple locations:

- Choose exactly one **Anchor** block.
- Pick the most actionable location, usually where the fix should happen.
- Put any other quoted snippets under **Supporting evidence**.
- Never mark more than one snippet as an anchor.

Format:

````text
**Anchor:** `src/components/Widget.tsx`

```tsx
// Widget, lines 42-44:
const [expanded, setExpanded] = useState(false);
...
```

**Supporting evidence:** `src/components/Widget.test.tsx`

```tsx
// Widget test, lines 88-90:
expect(groups).toHaveLength(2);
expect(groups[0]).toEqual(...);
```
````

This keeps the report aligned with how GitHub review comments actually work: one inline anchor, with optional supporting citations elsewhere.

## What to check

1. **Robustness rules**: Run the standard checklist (rules.md + checklist.md).
2. **Security**: Hardcoded secrets, tokens, credentials, or sensitive IDs in plaintext. Flag these regardless of whether they were inherited from prior code.
3. **Naming**: Do names in the code match the vocabulary of the UI and domain? Leaking internal naming (e.g., "server" when the UI says "tool") into tests or public APIs causes confusion.
4. **API contract drift**: If mock data or test fixtures duplicate types from production code, check whether they import the real types or hand-write their own. Hand-written copies drift silently.
5. **CI efficiency**: Are expensive jobs (E2E, builds) gated behind cheaper ones (lint, typecheck, unit tests)? Parallel is faster on the happy path but wastes resources on failure.
6. **Test coverage gaps**: Are there only happy-path tests? Error paths, edge cases, and boundary conditions at the integration level are where E2E tests add the most value.
7. **Duplication across feature areas**: If two feature areas (e.g., agents and tools) have near-identical components, check whether the production code itself is duplicated. If it is, note that the tests faithfully mirror that duplication and the fix belongs upstream in the components, not in the test layer.
8. **Cross-project patterns**: If the org has other projects with established testing patterns, compare and note where the PR aligns or diverges. Call out what the PR does better as well as what it could adopt.

## Report output

All PR review reports must be saved under `<workshop-root>/review-work/pr-reviews/`. Name the report file `{github_org}_{repo}_pr_{number}.md` in snake case. For example, `example-org/example-repo` PR #86 becomes `<workshop-root>/review-work/pr-reviews/example_org_example_repo_pr_86.md`. Do not place PR review reports in the reviewed checkout or any other location.

## Draft messages

For each finding (Medium and Low), include a `draft message` block: a ready-to-post PR comment written in a friendly, direct tone using full sentences. Place the draft message at the **end** of each finding section, after the analysis and suggested fix.

Write the draft message so it works as a comment on the chosen **Anchor** location:

- Speak directly to the code at the anchor.
- Mention other files or snippets only as supporting evidence.
- If the finding spans multiple files, do not write the draft as though GitHub can anchor it to all of them at once.

Write the draft message so it reads naturally, as if a person wrote it, while preserving its original meaning and intellectual level. Follow every rule below:

1. Never use em dashes or en dashes. Use a comma, period, or semicolon instead. Do not leave any dash characters in the message.
2. Do not use emojis.
3. Use everyday vocabulary and active voice. Prefer short sentences. Split long sentences.
4. Replace inflated or corporate wording with plain wording. For example, use `use` instead of `utilize`, and `improve` instead of `enhance`.
5. Avoid formal cliches and buzzwords such as `accurate`, `adapt`, `advanced`, `align`, `amplify`, `analyze`, `architect`, `automate`, `benchmark`, `core`, `comprehensive`, `creative`, and `cross functional`.
6. Keep all technical terms, names, dates, statistics, and existing formatting such as Markdown, lists, and headings.

Format:

````text
#### N. [Category] Title

**Anchor:** `file:line`

```language
Quoted anchor snippet
```

**Supporting evidence:** `file:line` (optional)

```language
Quoted supporting snippet
```

**What:** Description of the issue.

**Why it matters:** One sentence on the risk.

**Suggested fix:** Concrete suggestion.

```draft message
The ready-to-post PR comment goes here. Written in full sentences, friendly but direct. Cite specific files and code when relevant.
```
````

## Tone

- Acknowledge good work where you see it. Lead with what's done well before raising concerns.
- Be specific: cite files, line numbers, and code. Do not give generic advice.
- Do not excuse issues because they were "inherited" from prior code. The issue stands on its own.
- If you're not sure something is a real problem, don't flag it. No false positives.
