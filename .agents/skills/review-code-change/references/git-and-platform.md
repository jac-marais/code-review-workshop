# Git And Platform Intake

## Local Facts

Resolve exact objects. Do not substitute stale local branch tips for platform OIDs.

```sh
git cat-file -e "$base_oid^{commit}"
git cat-file -e "$head_oid^{commit}"
git merge-base --all "$base_oid" "$head_oid"
```

More than one best merge base blocks an exact single-range claim unless the platform provides an authoritative resolution.

Use three-dot pull request semantics: diff the merge base against the head. Keep the platform view for commentable lines and the local view for complete inventory, history, renames, copies, submodules, and execution.

Reconcile platform and local inventories. Explain generated-file hiding, file-count limits, binaries, submodules, rename thresholds, and stale snapshots.

## Pull Request Snapshot

Record:

- repository and pull request identity;
- base and head refs and exact OIDs;
- commits, changed files, checks, draft state, and mergeability;
- issue comments, review bodies, inline comments, every review thread and reply, resolved state, and outdated state;
- platform changed-line anchors;
- description and linked requirements as non-authoritative intent claims.

Paginate every collection. If the platform adapter cannot retrieve a discussion surface or complete changed-file inventory, record the gap.

## Anchors

Use the current head SHA. Use `RIGHT` for additions and context on the new file and `LEFT` for deletions. Use line and side fields, not deprecated diff positions.

Immediately before output or posting, refetch the head, diff, and discussions. A moved head invalidates affected anchors and behavior evidence.

## Working-Tree Changes

Record staged, unstaged, and untracked state separately. State the untracked-file policy. A user checkout can contain unrelated changes; never clean, stash, reset, or overwrite them.

Resolve every read of a committed range through the object store, `git show <oid>:<path>`, not the file on disk. Someone may be editing the checkout while you review, including an agent already acting on your findings, and reading a modified file silently substitutes their work for the revision you froze.

## When The Change Moves

A long review outlives the branch. When the head advances, recompute the merge base rather than reusing the old one, capture a fresh snapshot, and reconcile the new inventory against the old. State the new base and head everywhere the old ones appeared, because stale anchors point at lines that have shifted.

Separate commits that arrived from the base branch from commits that belong to the change. A merge pulls other people's work into your diff; diffing against the recomputed merge base keeps it out. Name the merged work explicitly so no reviewer spends effort on it.

Commits that fix your own earlier findings are new unreviewed code in the areas you already judged riskiest, so review them as their own scope. For each fix, establish which of four it is: it closes the defect; it is present but wrong, so the defect survives while the code looks addressed; it is incomplete, closing one call site and missing a sibling; or it is correct but introduces a worse failure. Then ask whether a test now fails when the fix is reverted. "Correct and complete" is a real result worth recording.

## Stack Exclusion

This skill handles one review range. If two or more linked pull requests appear, stop and route to the stack workflow. Do not flatten the stack into one diff or guess first-failing-prefix placement.
