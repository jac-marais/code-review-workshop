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
change. Add cluster-specific passes only for a one-way door, a trust boundary, a new public
contract, concurrent state, or another material risk.

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

Each workbench receives the complete frozen scope, the shared facts brief, its per-lane cluster
questions, relevant raw code, repository read access, and validation evidence. It does not
receive sibling candidates.

Workbenches can run in rounds. The lead can share corrected facts and new validation evidence in a later round, but it must not share sibling candidates. After discovery, the lead combines all candidates into one ledger, verifies them from raw evidence, and performs global deduplication.

### Behavior And Contracts

Trace entry points through callers, callees, types, schemas, public APIs, compatibility, and requirements treated as claims. Seek concrete broken behavior and ownership errors.

### State And Failure

Trace state transitions, partial effects, races, time, retries, cancellation, resource limits, dependency failures, recovery, and observability. Challenge happy-path tests with counterexamples.

### Security And Privacy

Use [`Security Lens Review`](../../security-lens-review/SKILL.md) as this workbench. First run a code-first pass without author identity, social proof, praise, or persuasive pull request text. Then use intent, history, threats, and existing comments to challenge that pass. Its coordinator returns security candidates to the review lead and does not produce a separate user-facing report.

### Design And Maintainability

Use [`Robust Rules Review`](../../review-robust-rules/SKILL.md) as this workbench. It applies Rule 0 through Rule 5 and the cross-cutting checks, then returns robustness candidates to the review lead. It does not produce a separate user-facing report.

### Evidence And Integration

Inspect whether tests fail when behavior breaks, CI still triggers, generated output matches its source, configuration and deployment agree, migrations and rollback work, and changed user flows hold in a real browser.

## 6. Record Completion

Each workbench returns its scope, evidence, candidate issues, cleared behavior, limits, and completion state. Robust Rules Review uses the `design-and-maintainability` completion slug. Security Lens Review uses the `security-and-privacy` completion slug. Missing or partial mandatory workbench output makes the whole review incomplete.
