# PR Storybook Narration

Use this guide for the deep review and all authored book text.

## Write Clear Text

Load and use `$write-clear-text` before you write a chapter. Apply ASD-STE100 to all book text, including headings, navigation labels, explanations, examples, transitions, and findings.

- Use common words and short sentences.
- Put one main idea in each sentence.
- State the actor and the action.
- Define a necessary technical term before you use it.
- Use the same term for the same thing.
- Split long cause-and-effect statements.

Do not copy poor source text into the narration. Quote exact source text only when its words are evidence.

### Sound like a knowledgeable guide

Write as a guide who speaks to the reader. Make the whole book feel like one conversation about the change. Open each chapter with the problem or review question that makes its evidence important. Connect each new section to the question that the prior section leaves open.

Give the reader an expectation before important evidence. After the evidence, say whether the code meets that expectation or makes the story more complex. Use short spoken transitions when they advance the reasoning. Phrases such as `Now follow one request`, `There is one catch`, and `That leaves one question` can make a technical story easier to follow.

Tell the reader what to look for before a `Diff`. After the `Diff`, explain why that detail matters. A sequence of evidence captions is not a conversation.

Ask a direct question only when the next passage answers it. Use first person only when the narrator gives the reader useful context. The narrator can explain why the story starts with one fact. The narrator can also show an expectation, doubt, surprise, decision, or change in understanding.

Do not use first person only to report routine review or writing work. Sentences such as `I see`, `I find`, and `I can use` read like work notes. If the first-person phrase adds no useful context, state the fact directly. Do not reuse a standard first-person opening across sections.

Vary sentence openings. Avoid a run of paragraphs that each start with the changed symbol or file. Preserve technical precision, but use the evidence to tell a causal story instead of listing code changes.

Do not join complete ideas with a colon, semicolon, or em dash. Write each idea as a separate sentence.

Use this pattern when the narrator must orient the reader.

> I should start with one rule. It makes the rest of this PR easier to understand. A fork needs two saved items from the same terminal checkpoint.

## Review Before You Author

Do not infer the story from filenames or the changed-file list.

1. Read the exact patch and identify the author claim.
2. Inspect the definitions, contracts, callers, and data flow that give the patch meaning.
3. Trace each material behavior from its input to its observable result.
4. Inspect tests and other evidence. State what each check proves and what it does not prove.
5. Check failure paths, compatibility limits, state changes, and security boundaries that apply to the change.
6. Verify each possible finding from the raw patch and necessary repository context.
7. Form the story only after the causal structure is clear.

A list of files, symbols, or hunk summaries is not a review story.

## Build A Layered Causal Story

Use one numbered MDX file for each chapter. Use one level-one heading for the chapter title. Level-one, level-two, and level-three headings can own review units. Give each heading unique visible text within its chapter.

Start with the smallest contract or fact that later behavior requires. Explain the prior behavior or failure route before the solution when the reader needs it to assess the change. Then explain each dependent action. End with integration, proof, and material risk when the change needs those stages. Do not force a fixed chapter count or fixed chapter names.

Keep one main review question in each chapter. Start a new chapter when that question changes. A new file or directory is not a reason to start a chapter.

Each section must help the reader answer these questions:

- What does this part of the change do?
- Why does it belong here in the causal story?
- Which exact evidence supports it?
- What must the reviewer decide or verify?

Answer these questions in natural prose. Integrate the review decision into that prose. Do not repeat labels such as intent, behavior, inference, consequence, decision, or question. Fixed fields and repeated labels cause repeated text.

Group evidence by one behavior, contract, or causal idea. Do not group it by directory. A section can join a definition, producer, consumer, and test from different files.

Give each review unit one chapter and heading owner in its evidence sidecar. Copy the exact visible heading text into `section`. Mark the unit as `displayed`, `supporting`, or `mechanical`. Coverage ownership is audit data. Do not show it as a metadata row in the book.

## Use Evidence In The Story

Place each useful `Diff` after its assigned heading, where the prose needs the evidence. For a hunk, use a ranged reference and select the smallest consecutive range that proves the point. A hunk excerpt must contain a changed line and no more than 24 total lines. Omit unrelated comments and docstrings. Keep them only when their exact text is part of the review evidence. For a metadata unit, use a bare reference with no range.

Match each claim to the displayed excerpt. Do not claim that a path, caller, error, or test changed when the excerpt does not show it. Weaken the claim, add the exact excerpt, or remove the claim.

Use a normal fenced code block only for a small input, output, data shape, or illustrative example. Do not copy changed source into a fence. State that an example is illustrative when a reader could mistake it for repository evidence.

Do not add a generic `Example`, `Evidence`, `Code`, or `What changed` heading. Use a specific story heading only when the reader needs one.

Do not send the reader to a separate raw-diff view. A visible evidence link must open the exact pull request file and line that it names. Do not show a raw evidence ID, hunk header, confidence value, or provenance row as a citation.

Keep these claims distinct when the distinction matters:

- Author intent is what the author or pull request says should happen.
- Observed behavior is what the code or a completed check shows.
- An inference is a conclusion from stated evidence.
- A verified finding is a defect that the review lead confirmed from raw evidence.

Use a plain label only when the reader could confuse two claim types. Prefer a natural sentence that makes the distinction clear. Do not repeat one claim under several labels.

## Put Findings At Their Cause

Place `<Finding id="..." />` where the defect cause becomes visible. A hunk anchor must name its side and changed line, and that line must occur in a nearby `Diff` excerpt. Only a metadata unit can use a unit-level anchor. That unit must be owned by the same section.

An active verified finding must include:

- the changed line or review unit that causes the defect;
- the trigger;
- the user or system impact;
- the necessary supporting evidence;
- the smallest complete fix direction; and
- severity and confidence as separate facts.

Show severity. Show confidence only when it changes how the reviewer must treat the finding. Do not hide a verified finding for a later reveal or collect findings on a separate page.

## Remove Redundancy

After all chapters are complete, audit the whole book as one text. This audit is required. A chapter-by-chapter check is not sufficient.

For each sentence, ask whether another sentence already states the same material idea. Keep the clearest statement at the first useful point. Delete the rest.

Also remove:

- a heading that repeats its first sentence;
- a question that repeats its section title;
- a transition that restates the prior section;
- an explanation that only paraphrases visible code;
- a test summary that repeats the behavior claim; and
- a finding summary that repeats its trigger or impact.

Then run the complete `$write-clear-text` check again. Do not declare the book complete until both audits pass.

## Final Narration Gate

Reject the book when any condition is true:

- The story follows file order without a causal reason.
- A material behavior or dependency is missing.
- A necessary domain term appears before its definition.
- A chapter contains more than one main review question.
- A unit has no owner or has more than one owner.
- An important claim has no exact evidence.
- A claim is stronger than its displayed excerpt.
- A hunk excerpt has more than 24 lines or includes an unrelated comment or docstring.
- A displayed excerpt does not help the reader assess its section.
- Two passages state the same material idea.
- A generic heading adds no meaning.
- The prose reads as disconnected evidence captions instead of one guided conversation.
- A finding is not beside the evidence for its cause.
- First person reports routine work instead of giving the reader useful context.
- A repeated first-person opening makes the story feel like a template.
- A colon, semicolon, or em dash joins complete ideas.
- The text does not pass `$write-clear-text` and the whole-book redundancy audit.

Before completion, delegate one narrowly scoped subagent to read every MDX chapter as one book and apply this gate. Its only task is to answer the gate questions and quote exact passages for failures. It must not re-review the code or expand the scope. Allow three review passes in total, which gives the author two opportunities to fix reported problems. If the third pass still reports a problem, record the remaining objection, stop retrying, and proceed.
