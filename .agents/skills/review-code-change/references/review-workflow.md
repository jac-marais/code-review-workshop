# Review Workflow

## 1. Freeze Scope

Record repository identity, requested mode, user-checkout status, base and head OIDs, every best merge base, changed files, and commentable lines. For a pull request, also record the platform head, base, commits, checks, description, and every discussion surface.

Use [`capture_review_snapshot.py`](../scripts/capture_review_snapshot.py) for local Git facts. Platform facts remain separate and authoritative for commentability.

## 2. Decompose And Brief

Skip this step only when the whole change fits one reviewer's context. Above that, a single
workbench holding every file reviews all of them shallowly.

**Cluster by feature, not by directory.** A directory split cuts through features, because one
package usually serves several. Group files by the behavior they change. Verify mechanically
that every changed file lands in exactly one cluster, and record the check.

**Size extra cluster passes to risk.** Run all five mandatory workbenches once across the complete
change. A workbench divides its own lane by cluster inside that one pass. Never run every lane on
every cluster: in the archive, five lanes times six clusters spent 123M tokens to produce two
comments. Add a cluster-specific pass only for a one-way door, a trust boundary, a new public
contract, concurrent state, or another material risk.

**Write the fan-out plan before launch.** Record in `fan-out.json` one entry per agent: lane,
cluster or `all`, and for each extra pass the named risk that justifies it. The baseline is five
workbench agents. Each agent costs roughly 150K to 250K tokens before it reviews anything, and its
context is replayed on every later turn, so agent count is the main cost lever.

**Write per-lane questions for each cluster.** A workbench handed only its generic method
converges with its siblings. A workbench handed the specific questions its lane owns in this
cluster diverges productively. Name in each lane's brief which questions belong to siblings.

**Build one shared facts brief before any workbench runs.** Every workbench reads it instead of
re-deriving it, which is the difference between reviewing a large change and rediscovering the
repository five times per cluster. Include:

- every binary, how it is built, what it imports, and where activities, routes, jobs, and
  handlers register, because a change to code no binary reaches is a recurring and invisible
  defect that symbol-level grep cannot find;
- constants and contracts duplicated across languages or services, and how each is delivered;
- configuration and deployment values the changed code depends on;
- the frozen scope facts and the existing-discussion inventory;
- a section naming what is **not** established, so no workbench invents it.

**Settle shared open questions once.** When the brief marks a fact not established and two or more
lanes need it, settle it before launch with one check, or assign it to one named lane and tell the
other lanes to wait for the amended brief rather than re-derive it. In the archive, three lanes
independently proved the same schema equality the brief had left open.

**Keep the brief current, not cumulative.** When a fact is corrected, replace the old statement and
date the amendment. Do not leave the superseded paragraph beside its correction.

The lead owns the brief and can be wrong in it. Tell every workbench to contradict it loudly
rather than defer to it, then verify the contradiction, amend the brief in place, and date the
amendment. A wrong fact left standing reaches every later workbench at once.

## 3. Map The Change

Account for every changed file. Inspect complete logical content with bounded reads or exact tools. Record a file receipt even for generated, minified, binary, deleted, renamed, vendored, or unusually large content.

Map:

- behavior, entry points, requirements, callers, and public contracts;
- types, schemas, compatibility, and migrations;
- state, persistence, caches, queues, retries, cancellation, time, concurrency, and resources;
- permissions, trust boundaries, tenants, secrets, personal data, network, commands, and dependencies;
- configuration, CI, deployment, flags, observability, rollback, and generated output;
- tests, mocks, fixtures, browser routes, accessibility, and visible states.

Retrieve progressively along named call, data, contract, configuration, and deployment edges. Expand for public contracts, shared or global state, dynamic registration, reflection, trust boundaries, persistence, deletions, and runtime evidence that conflicts with the current model.

## 4. Validate Named Questions

Start with the smallest check that can prove or disprove a changed behavior. Compare base, head, and current-base integration states when needed to distinguish pre-existing, introduced, and integration failures.

The review lead plans checks. The validation executor runs them in the sandbox and returns command, tool version, environment, revision, exit code, scope, and observation.

## 5. Run Independent Workbenches

Each workbench receives a context pack and repository read access. It does not receive sibling
candidates. The pack contains:

- the frozen scope facts and the changed-file inventory with line ranges per cluster;
- the shared facts brief;
- its per-lane cluster questions, and which questions belong to siblings;
- validation evidence gathered so far;
- the workbench contract: the Evidence Rules from [`SKILL.md`](../SKILL.md#evidence-rules), the
  candidate shape from [`candidate-and-output.md`](candidate-and-output.md#candidate-issue), the
  completion slug, and the rule that it modifies nothing and runs no target command.

Start a workbench from the pack. It does not re-read the workshop `AGENTS.md`, this skill, or these
references, and it does not re-map the repository. A linked lane skill reads only its own rule or
lens files. Retrieve code along named edges from the pack's questions. Re-derive a briefed fact
only to contradict it.

Workbenches can run in rounds. The lead can share corrected facts and new validation evidence in a later round, but it must not share sibling candidates. After discovery, the lead verifies each established fact it relies on and folds it into the brief. It then records every candidate in the candidate ledger, verifies each from raw evidence, and performs global deduplication.

### Behavior And Contracts

Trace entry points through callers, callees, types, schemas, public APIs, compatibility, and requirements treated as claims. Seek concrete broken behavior and ownership errors.

### State And Failure

Trace state transitions, partial effects, races, time, retries, cancellation, resource limits, dependency failures, recovery, and observability. Challenge happy-path tests with counterexamples.

### Security And Privacy

Use [`Security Lens Review`](../../security-lens-review/SKILL.md) as this workbench. First run a code-first pass without author identity, social proof, praise, or persuasive pull request text. Then use intent, history, threats, and existing comments to challenge that pass. By default this is one combined-lens pass; the skill names the triggers that escalate to five parallel lenses. Its coordinator returns security candidates to the review lead.

### Design And Maintainability

Use [`Robust Rules Review`](../../review-robust-rules/SKILL.md) as this workbench. It applies Rule 0 through Rule 5 and the cross-cutting checks, then returns robustness candidates to the review lead.

### Evidence And Integration

Inspect whether tests fail when behavior breaks, CI still triggers, generated output matches its source, configuration and deployment agree, migrations and rollback work, and changed user flows hold in a real browser.

## 6. Record Completion

Each workbench returns its scope, evidence, candidate issues, cleared behavior, limits, an **established facts** list of new repository facts it proved with locators, and its completion receipt. It does not re-list the changed-file inventory; the lead owns the per-file receipts. Missing or partial mandatory workbench output makes the whole review incomplete.

## 7. Re-Review After New Commits

Use delta mode when a completed review of the same pull request or branch exists under
`review-work/pr-reviews/` at an older head. In the archive, later rounds cost as much as first
reviews although 87% to 92% of their files had not changed. They still found real defects: of 34
later-round findings, 13 were in fix code and 14 were counterexamples the fix did not cover. So
delta mode narrows the code read, not the questions asked.

Write `delta-scope.json` before any workbench runs. It records the prior review ID, the prior and
new heads, and these scope parts:

1. **Interdiff.** Every file and hunk the author changed between the prior head and the new head,
   with base movement separated out as in
   [`git-and-platform.md`](git-and-platform.md#when-the-change-moves). After a rebase or force
   push, pair the commits with `git range-diff`.
2. **Dependency closure.** Callers, callees, contracts, configuration, registrations, and tests
   reached by a changed symbol along the edges the shared facts brief names. When the closure
   cannot be proven, because of dynamic registration, reflection, or generated code, widen to the
   affected cluster.
3. **Prior findings.** The anchor and causal path of every prior output comment and suppression,
   whether or not the author claims a fix.
4. **Prior counterexamples.** Every prior reproduction or probe that tested a finding. Rerun it
   against the new head through the validation executor.

Reuse a prior `cleared` entry when no file in its locator or evidence falls inside the interdiff or
the dependency closure. Cite the prior review ID in its evidence. Reopen every other cleared entry.
Reuse the prior shared facts brief and amend it for the interdiff instead of rebuilding it.

Run every mandatory workbench once over the delta scope, with the prior findings and their fix
claims as lane questions. Classify each fix as that reference describes. Record a completion receipt for every file in the full changed-file
inventory: reviewed files from the delta work, and untouched files citing the prior review ID.

Fall back to a full review when no prior result exists, the prior review was `incomplete`, the
prior head is not an ancestor of the new head and `range-diff` cannot pair the commits, or the
interdiff touches more than half of the changed files.
