# PR Storybook Bundle Contract

Read this file before you create, edit, build, or validate a PR Storybook bundle.

## Boundary

Keep the frozen evidence, review claims, authoring source, and static output separate.

```text
bundle/
├── diff.patch
├── run.json
├── findings.json
├── book.json
├── chapters/
│   ├── 01-<chapter>.mdx
│   ├── 01-<chapter>.evidence.json
│   └── ...
└── site/
    ├── index.html
    ├── standalone.html
    ├── 01-<chapter>.html
    └── assets/
        └── book.css
```

- `diff.patch` is canonical evidence.
- `run.json` contains computed facts for the exact patch.
- `findings.json` contains finding records and their review states.
- `book.json` binds the book to the frozen run.
- Numbered MDX files contain the story.
- Matching evidence sidecars contain coverage ownership and display disposition.
- `site/` is derived output. Never edit it as the narrative source.
- `site/standalone.html` contains every chapter and all required CSS. It must not require another local or remote file.

The bundle must not contain reviewer notes, viewed marks, progress, scores, or browser state.

## Stable Identity

- `runId` is the SHA-256 digest of canonical `run.json` content without `runId` and `createdAt`.
- `fileId` includes the run-independent file status, old path, new path, and exact file patch digest.
- `unitId` includes the file identity, range data, and exact review-unit bytes.
- Finding IDs are stable authored IDs that match `^[a-z][a-z0-9-]*$`.
- A numbered chapter filename is the chapter ID and sets its order.

Create a new run when the patch changes. Do not rewrite the old run.

## `run.json`

`run.json` uses schema version `1`.

It records:

- the `runId` and UTC creation time;
- repository and pull request identity, when available;
- base, head, and merge-base revisions;
- the SHA-256 digest of `diff.patch`;
- ordered file facts and review units; and
- file, unit, addition, and deletion totals.

A file records its stable ID, old and new paths, status, binary state, patch digest, line totals, and units.

A text hunk is one review unit. It records its header, old and new ranges, and ordered lines. Each line records its kind, old line, new line, and text.

A binary or metadata-only change must also create one review unit. Do not omit it because it has no text hunk. Its unit must retain the exact file status and frozen patch evidence that the validator needs.

## `book.json`

`book.json` uses schema version `1`. Its exact fields are:

- `schemaVersion`: integer `1`;
- `runId`: the exact ID from `run.json`; and
- `title`: the non-empty book title.

Repository and pull request facts stay in `run.json`. Do not copy them into `book.json`.

## Numbered MDX Chapters

Use one numbered `.mdx` file for each chapter. The matching `.evidence.json` file must use the same filename stem. An array or extra order field must not override filename order.

The first level-one heading supplies the chapter title and navigation label. A level-one, level-two, or level-three heading can own review units. Each heading must have unique visible text within its chapter. The matching evidence sidecar copies this exact visible text into `section`. Do not use a generated heading ID.

Write normal Markdown and fenced code. A fence can show a small input, output, data shape, or illustrative example. Do not copy changed source into a fence. Use a `Diff` reference for changed source.

Only these two MDX components are valid:

```mdx
<Diff ref="unit:<64-lowercase-hex>@<zero-based-offset>:<count-from-1-to-24>" />

<Diff ref="unit:<64-lowercase-hex>" />

<Finding id="stable-finding-id" />
```

A ranged `Diff` reference is valid only for a hunk unit. It selects from 1 to 24 consecutive lines. The selection must be inside the unit and must contain an added or deleted line. It must not include an unrelated comment or docstring.

A bare `Diff` reference is valid only for a metadata unit. It displays the frozen metadata evidence for that unit. It has no offset or count and does not need a changed line.

The build obtains the path, status, ranges, line numbers, text, and metadata from `run.json`. Do not copy this data into the MDX.

`Finding` places one verified finding in the story. The finding record remains the source for its title, severity, summary, trigger, impact, anchors, evidence, and fix.

The MDX validator must reject imports, exports, expressions, raw HTML, images, inline JSX, unknown nodes, unknown components, child content in `Diff` or `Finding`, non-literal attributes, and extra attributes. It must also reject fenced-code metadata. A finding ID must match `^[a-z][a-z0-9-]*$`. An authored link can use only an in-page fragment or an absolute HTTPS URL. Repository content must enter the page only as escaped frozen data. The renderer must show each Unicode direction control as visible escaped text instead of applying its direction.

## Evidence Sidecars

Each chapter has one sidecar with this shape:

```json
{
  "schemaVersion": 1,
  "runId": "sha256:<64-lowercase-hex>",
  "chapter": "01-contract",
  "coverage": [
    {
      "unitId": "unit:<64-lowercase-hex>",
      "section": "Define the contract",
      "disposition": "displayed"
    },
    {
      "unitId": "unit:<64-lowercase-hex>",
      "section": "Define the contract",
      "disposition": "supporting",
      "reason": "This caller confirms the same contract."
    },
    {
      "unitId": "unit:<64-lowercase-hex>",
      "section": "Define the contract",
      "disposition": "mechanical",
      "reason": "The lock file records the dependency update."
    }
  ]
}
```

The sidecar has no prose claim, path, range, copied code, or finding text.

- `runId` must equal `run.json`.
- `chapter` must equal the filename stem.
- `section` must equal the complete visible text of one level-one, level-two, or level-three heading in that chapter.
- Heading text must be unique within one chapter.
- `displayed` means that at least one `Diff` after the assigned heading selects this unit. It has no `reason` field.
- `supporting` means that the unit supports the section but has no displayed excerpt. It requires one short `reason`.
- `mechanical` means that the unit has no separate material behavior and has no displayed excerpt. It requires one short `reason`.

Each review unit from `run.json` must occur in exactly one coverage record. It must not occur under two headings or chapters. A displayed unit can supply more than one excerpt. Each excerpt must occur after its assigned heading.

This contract separates review coverage from displayed evidence. A `supporting` or `mechanical` record is not proof that the reader saw the unit. Do not use these dispositions to hide a material behavior or risk.

Binary, metadata-only, generated, lock, and mechanical units still need owners. Do not invent pseudo-code for them. Use a bare `Diff` reference when the reader needs to see a metadata unit. Discuss other material non-text changes in their owned sections and provide an exact pull request link when the platform supports one.

## `findings.json`

`findings.json` uses schema version `2`. Its exact top-level fields are `schemaVersion`, `runId`, and `findings`.

A finding records:

- a stable `id`;
- `status`: `verified`, `reported`, `resolved`, `duplicate`, or `rejected`;
- `severity`: `P0`, `P1`, `P2`, or `P3`;
- `confidence`: `high`, `medium`, or `low`;
- `title`, `summary`, `trigger`, `impact`, and `fix`;
- its generator or reviewer `source`;
- zero or more exact `anchors`;
- supporting `evidence`; and
- an optional external discussion URL.

A finding anchor always records a valid `fileId` and `unitId`. An anchor for a hunk unit must also record `side` and `line`. These two fields must occur together. The anchor must identify an added line on the new side or a deleted line on the old side. Only a metadata unit can omit `side` and `line` and use a unit-level anchor.

A verified finding must have at least one valid changed-line hunk anchor or metadata-unit anchor. Its one `Finding` marker must occur in the section that owns its anchor unit. A hunk anchor must occur in a displayed `Diff` excerpt in that section. A metadata-unit anchor does not require a line excerpt. Show severity. Keep confidence in the record. Show confidence only when it changes how the human must treat the finding.

Do not show reported, resolved, duplicate, or rejected records as active defect claims.

## Preparation And Validation

Preparation must write the exact raw patch, compute its digest, create `run.json`, create an empty findings document, and create a minimal `book.json`. It can create an empty chapter directory. It must not invent the story. Preparation and repository-aware validation must compare repository state before and after their work. They must fail if they change it.

Final validation must use a read-only repository copy. It must recompute the revisions, merge base, raw patch, patch digest, ordered path inventory, and review-unit identities. For a pull request, the caller must get the current base and head from the platform and supply both to repository-aware validation. The validator must compare them with the frozen base and head. A mismatch in either revision makes the bundle stale. A validation run without a repository proves only internal bundle integrity. It does not prove pull request freshness.

The repository-aware validator and the renderer are separate required gates. The renderer must run repository-aware validation again before it replaces `site/`. A stale pull request bundle can remain as historical output. It must not be the current output.

The validator must reject:

- a patch digest, run ID, base, head, merge-base, or subject mismatch;
- an unknown field at a defined JSON boundary;
- a missing or duplicate numbered chapter pair;
- an unsafe or invalid MDX node;
- an invalid, unknown, empty, or out-of-range `Diff` reference;
- a ranged `Diff` reference for a non-hunk unit;
- a bare `Diff` reference for a non-metadata unit;
- a hunk `Diff` excerpt with more than 24 lines;
- an exact `Diff` reference that occurs more than once;
- a displayed hunk excerpt without a changed line;
- an unknown, repeated, or unverified `Finding` reference;
- a finding ID that does not match `^[a-z][a-z0-9-]*$`;
- a hunk finding anchor without a valid `side` and changed `line`;
- a unit-level finding anchor for a non-metadata unit;
- a verified finding without a valid hunk or metadata-unit anchor;
- a verified finding outside the section that owns its anchor unit;
- a hunk finding anchor outside a displayed excerpt in that section;
- a missing, unknown, or multiply owned review unit;
- an unknown or duplicate visible heading owner;
- a `section` value that does not equal its visible heading text;
- a `displayed` unit with no displayed excerpt;
- a displayed excerpt that occurs before its assigned heading;
- a `supporting` or `mechanical` unit with a displayed excerpt;
- a missing or invalid disposition reason;
- an authored link that is not a fragment or an absolute HTTPS URL; or
- a stale platform base or head.

The workflow must also reject an inventory-only story, repeated prose, and unsupported claims. A JSON schema cannot prove narrative quality.

## Safe Failure

Do not build the authored site when repository-aware validation fails. Replace no valid prior output.

The only permitted failure output is a static fallback page that shows:

- a clear validation error; and
- the exact escaped contents of `diff.patch`.

The raw patch is a safety fallback. It is not a normal PR Storybook view.
