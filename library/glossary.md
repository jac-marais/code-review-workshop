# Workshop Glossary

Use these terms in operating guidance and runtime artifacts.

| Term | Meaning |
| --- | --- |
| Workshop | This repository, including its research, library, review workflows, workbenches, tools, scorecards, and evidence. |
| Review workflow | The end-to-end process for one local change, one pull request, or a pull request stack. It coordinates intake, validation, workbenches, verification, deduplication, and output. |
| Workbench | One independent, read-only discovery method with a named failure model and evidence duty. A workbench cannot execute target code or create external effects. |
| Workbench run | One execution of a workbench against a frozen review snapshot. Avoid the vague term `review pass`. |
| Validation executor | The only review component allowed to run target commands. It executes inside the enforced sandbox and returns structured evidence to workbenches and the review lead. |
| Review lead | The coordinator that freezes scope, verifies candidate issues from raw evidence, deduplicates verified issues, and drafts output comments. It does not treat workbench agreement as proof. |
| Review snapshot | The frozen repository, revision, platform, discussion, stack, and user-checkout status facts that define the review. |
| Candidate issue | A structured but unverified defect claim from a workbench. It is never shown as a final comment until it survives verification. |
| Verified issue | A candidate issue that the review lead verified from raw code and evidence. Reserve `finding` for empirical and research findings. |
| Issue identity | The stable defect, first failing state, and minimal-fix facts used to compare verified issues and existing feedback. It excludes wording and line number. |
| Output comment | A GitHub-ready draft derived from one verified issue. Returning it does not create an external platform action. |
| Posted comment | A comment created on a review platform. Posting always requires separate, explicit user authority. Reserve `post` and `publish` for this external action. |
| Suppression | A verified issue withheld from output because the same issue already exists in review feedback or no useful changed-line anchor exists. |
| Validation | Running or inspecting the target system to establish behavior, such as tests, static tools, builds, or browser flows. |
| Verification | Trying to disprove one candidate issue from raw code, contracts, configuration, history, and validation evidence. |
| Reviewed repository | The logical project and revisions under review. |
| User checkout | The requester's existing working tree. The review workflow never edits it. |
| Validation copy | A disposable copy of reviewed content used inside the execution sandbox. It has separate Git administration and no write path to the user checkout. |
| Execution sandbox | An enforced process, filesystem, credential, metadata, service, and network boundary. A worktree, clone, trust label, or clean status is not an execution sandbox. |
