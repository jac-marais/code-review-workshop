# PR Storybook Interface

## Static Chapter Pages

Build one static HTML page for each MDX chapter. Use one shared local style file. Also build `standalone.html` with every chapter and the complete style sheet in one file. Compile and render MDX only at build time. Do not ship a client framework, MDX evaluator, syntax highlighter, or remote asset.

Use these defaults:

- dark theme only;
- ordered chapter navigation on the left;
- one active chapter in the main reading area;
- compact unified diffs in the story flow; and
- direct pull request links for exact changed evidence.

The first chapter is the normal entry point. Each chapter page must work as a direct local file and without a server.

The standalone page is a distribution artifact for restricted iframe and snippet tools. Keep all chapters visible in story order. Use unique in-page chapter and heading IDs. Use fragment links for chapter navigation and finding evidence when local evidence is available. Do not add a view switch or other runtime control.

## Reading Flow

Show the chapter title and authored MDX blocks in source order. Use headings, spacing, and rules to show structure. Do not put normal prose, diffs, examples, or findings in cards.

The left navigation shows all numbered chapters in story order. Mark the active chapter with `aria-current="page"`. On a narrow screen, replace the fixed left area with one clear native chapter control. When a reader selects a chapter, move focus to the chapter heading after navigation.

Let prose use the available reading width. Let code use more width than prose when needed. Keep the page calm and dense enough for review work.

## Unified Diff Evidence

Render one compact unified excerpt for each ranged hunk `Diff`. Keep the file path, line numbers, and change markers visible. Use text and shape as well as color for additions and deletions.

Render one compact evidence block for each bare metadata `Diff`. Show the file path, file status, and necessary frozen metadata. Do not invent code, line numbers, or change markers.

Generate the excerpt only from `run.json`. Never trust copied path, code, range, or line data from MDX. Escape all repository text.

Give each displayed hunk excerpt a direct link to the exact platform file and changed line when the subject has a pull request URL. Give each displayed metadata block a direct link to its exact platform file target. Make each link immutable when the platform supports an immutable target. Use the frozen head for new-side lines. Use the frozen merge base for old-side lines. The link label must describe its file and target. Do not show raw unit IDs or raw hunk headers to the reader.

Do not add split view, before-and-after tabs, diff modes, or a separate raw-diff page.

## Examples And Findings

Render a fenced example in the normal reading flow. Use its language for local build-time syntax styling. Do not add a generic example title or wrapper card.

Render each verified finding at its `Finding` marker. Keep it beside its causal evidence. Show a clear finding label, severity, trigger, impact, and fix direction. A hunk finding link must open its exact immutable platform line when the platform supports it. Use the frozen head for a new-side anchor and the frozen merge base for an old-side anchor. A metadata-unit finding has no line, so link it to the exact immutable platform file or unit target.

Do not add a findings summary page, reveal control, or delayed finding state.

## Omitted Features

Do not add:

- cards or nested panels for normal content;
- change statistics or summary counters;
- reviewer notes;
- viewed marks;
- progress tracking, scores, or completion badges;
- local browser storage;
- raw coverage, provenance, or metadata rows;
- finding reveal controls;
- multiple modes, tabs, or tours;
- a raw-diff navigation view; or
- generic example headers.

These features add noise or repeat information. Their absence is part of the interface contract.

## Accessibility And Safety

- Use semantic `nav`, `main`, headings, links, code, and native controls.
- Keep the heading order equal to the MDX source order. Keep visible heading text unique within each chapter.
- Give each control and evidence link a clear accessible name.
- Keep a visible focus indicator.
- Keep the reading order correct when styles do not load.
- Meet WCAG AA contrast for text, controls, and focus.
- Do not use color as the only status or diff signal.
- Render untrusted content as DOM text. Do not assign it as HTML.
- Render each Unicode direction control as visible escaped text, such as `\u202E`. Do not let it change the page direction.
- Permit only in-page fragments and absolute HTTPS URLs in authored links.
- Load no remote code, font, image, or data resource.
- Write all output outside the reviewed checkout, Git directory, and common Git directory.

If repository-aware validation fails, do not render the authored book. Show only the safe fallback page with the clear error and exact escaped raw patch.

## Required Checks

For a pull request, get the current base and head from the platform. Pass both to repository-aware validation and the renderer. Both commands must succeed before browser checks. A mismatch in either revision makes the book stale. Then complete these checks:

1. Desktop: Check the left navigation, reading width, unified diffs, findings, and direct evidence links.
2. Narrow: Check the chapter control, reading order, code overflow, and finding placement.
3. Keyboard: Reach and operate all navigation and links. Check focus order and visible focus.
4. Console: Confirm that the page has no errors or blocked resource requests.
5. Accessibility: Check landmarks, heading order, control names, contrast, and non-color status labels.
6. Static output: Open each chapter and `standalone.html` directly from `site/` without a server. Confirm that the standalone page loads no required external resource.

Repository-aware validation and the renderer must pass before these checks. An offline integrity check does not prove Git provenance or pull request freshness. A stale pull request book is historical output, not current output.
