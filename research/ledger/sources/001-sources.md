# Batch 001 Source Receipts

Retrieval date: 2026-07-13

`SRC-001` and `SRC-002` live in [`library/manifest.json`](../../../library/manifest.json). They are owner-authored local review protocols. The records below cover external evidence.

## Review Science And Practice

### SRC-003: Reducing Inspection Interval in Large-Scale Software Development

- Owner: Dewayne E. Perry, Adam A. Porter, and Lawrence G. Votta
- Class: peer-reviewed IEEE Transactions on Software Engineering paper
- Canonical reference: https://users.ece.utexas.edu/~perry/work/papers/DP-02-tse.pdf
- Locators: sections 3.2.1 through 3.2.4, PDF pages 3 through 4, printed pages 696 through 697
- Authority: controlled inspection studies and an 18-month live project
- Limits: older human inspection setting, not modern pull requests or LLM agents

### SRC-004: Internally Replicated Comparison Of Checklist And Perspective-Based Reading

- Owner: Oliver Laitenberger, Khaled El Emam, and Thomas G. Harbich
- Class: peer-reviewed IEEE Transactions on Software Engineering paper
- Canonical reference: https://publica.fraunhofer.de/entities/publication/ad72ecaa-e07f-4a34-9ed8-0042bc4ea9c0
- Locator: abstract and DOI 10.1109/32.922713
- Authority: three industrial studies with Bosch Telecom developers
- Limits: formal code-document inspection rather than agent-driven pull request review

### SRC-005: Characteristics Of Useful Code Reviews

- Owner: Amiangshu Bosu, Michaela Greiler, and Christian Bird
- Class: peer-reviewed industrial study
- Canonical reference: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bosu2015useful.pdf
- Locators: section VI.A.1, PDF pages 7 through 8; section VI.B.1, PDF page 9
- Authority: 1.5 million Microsoft review comments plus interviews
- Limits: usefulness includes author judgment and a learned classifier, not independently verified defect correctness

### SRC-006: Small CLs

- Owner: Google Engineering Practices
- Class: first-party engineering guidance
- Canonical reference: https://google.github.io/eng-practices/review/developer/small-cls.html
- Locators: sections "What is Small?" and "When are Large CLs Okay?"
- Authority: Google's documented review practice
- Limits: practitioner guidance from one organization, not an experimental threshold

### SRC-007: The Effects Of Change Decomposition On Code Review

- Owner: Marco Di Biase and coauthors
- Class: peer-reviewed controlled experiment
- Canonical reference: https://arxiv.org/pdf/1805.10978
- Locators: abstract and results summary, PDF page 1; DOI 10.7717/peerj-cs.193
- Authority: controlled comparison of tangled and decomposed changes
- Limits: 28 developers and one small Java system

### SRC-008: What Types Of Defects Are Really Discovered In Code Reviews?

- Owner: Mika V. Mäntylä and Casper Lassenius
- Class: peer-reviewed empirical study
- Canonical reference: https://aaltodoc.aalto.fi/bitstreams/cab054e8-0c06-47ab-8754-54bb09a0a6d3/download
- Locators: sections 3.2 and 4.1.2, PDF pages 5 through 6 and 9; conclusion on PDF page 13
- Authority: observed industrial and student reviews with defect classification
- Limits: nine industrial review sessions plus student studies

### SRC-009: Code Reviews Do Not Find Bugs

- Owner: Jacek Czerwonka, Michaela Greiler, and Jack Tilford
- Class: Microsoft industrial experience report
- Canonical reference: https://www.microsoft.com/en-us/research/wp-content/uploads/2015/05/PID3556473.pdf
- Locator: section II, PDF pages 1 through 2
- Authority: first-party account of review findings at Microsoft
- Limits: short experience report, not a causal study

### SRC-010: What To Look For In A Code Review

- Owner: Google Engineering Practices
- Class: first-party engineering guidance
- Canonical reference: https://google.github.io/eng-practices/review/reviewer/looking-for.html
- Locators: sections "Tests," "Every Line," "Context," and "Summary"
- Authority: documented review practice for design, behavior, tests, naming, comments, style, UI, and concurrency
- Limits: practitioner guidance from one organization

### SRC-011: Test-Driven Code Review

- Owner: Davide Spadini and coauthors
- Class: peer-reviewed ICSE 2019 controlled study
- Canonical reference: https://research.tudelft.nl/en/publications/test-driven-code-review-an-empirical-study/
- Locator: abstract; DOI 10.1109/ICSE.2019.00110
- Authority: experiment with 93 developers
- Limits: controlled tasks do not establish one universal file-reading order

### SRC-012: Impact Of Modern Code Review Practices On Software Quality

- Owner: Shane McIntosh and coauthors
- Class: peer-reviewed repository-mining study
- Canonical reference: https://sailresearch.github.io/sail-website/data/pdfs/EMSE_AnEmpiricalStudyOfTheImpactOfModernCodeReviewPracticesOnSoftwareQuality.pdf
- Locators: research summary on PDF page 3; conclusions on PDF pages 39 through 40
- Authority: longitudinal analysis of Qt, VTK, and ITK
- Limits: observational measures with difficult linkage and correlated predictors

### SRC-013: Do Code Review Measures Explain Post-Release Defects?

- Owner: Mauricio Krutauz and coauthors
- Class: reproduction and replication study
- Canonical reference: https://arxiv.org/pdf/2005.09217
- Locators: sections 3.4, 4.4, and 6.1, PDF pages 15, 23, and 28
- Authority: reproduction plus Chrome replication of review-quality measures
- Limits: repository-mining study with construct and linkage limits

### SRC-014: Deep Learning-based Code Reviews, A Double-Edged Sword

- Owner: Michele Tufano and coauthors
- Class: controlled professional study
- Canonical reference: https://personal.us.es/amarlop/wp-content/uploads/2024/12/Deep-Learning-based-Code-Reviews-A-Paradigm-Shift-or-a-Double-Edged-Sword.pdf
- Locators: abstract and findings on PDF pages 1 through 2; recommendations and threats on PDF pages 9 through 10
- Authority: 29 professional developers across 72 Java and Python reviews
- Limits: small programs, injected issues, and a likely underpowered sample

### SRC-015: AI-Assisted Assessment Of Coding Practices In Modern Code Review

- Owner: Google researchers
- Class: peer-reviewed industrial deployment study
- Canonical reference: https://homes.cs.washington.edu/~rjust/publ/code_review_automation_aiware_2024.pdf
- Locators: sections 4.3 and 4.4, PDF page 6
- Authority: real AutoCommenter deployment and independent usefulness ratings
- Limits: documented coding practices rather than broad behavioral defect detection

### SRC-016: CR-Bench

- Owner: Kristen Pereira and coauthors
- Class: 2026 code review agent evaluation preprint and workshop paper
- Canonical reference: https://arxiv.org/pdf/2603.11078
- Locator: section 7.2, table 4, PDF page 9
- Authority: independent agent benchmark that tracks recall, usefulness, and signal-to-noise
- Limits: 174 Python-oriented tasks, four agent setups, and LLM-assisted classification

### SRC-017: An Insight Into Security Code Review With LLMs

- Owner: Yu and coauthors
- Class: empirical preprint
- Canonical reference: https://arxiv.org/pdf/2401.16310
- Locators: dataset and design on PDF pages 2 through 3; results on PDF pages 12 through 16; application discussion on PDF pages 22 through 24
- Authority: 534 files from OpenStack and Qt reviews with manual curation
- Limits: human-found defects, Python and C/C++ concentration, and changing model versions

### SRC-018: Measuring And Exploiting Contextual Bias In LLM-Assisted Security Code Review

- Owner: Dimitris Mitropoulos, Nikolaos Alexopoulos, Georgios Alexopoulos, and Diomidis Spinellis
- Class: 2026 empirical preprint
- Canonical reference: https://arxiv.org/pdf/2603.18740
- Locators: sections 3.1 and 3.2, PDF pages 4 through 5; section 4.3, PDF page 9
- Authority: controlled study on 250 CVE patch pairs plus 17 real configured review pipelines
- Limits: real-pipeline study targets Claude Code and a small CVE set

### SRC-019: Human-AI Synergy In Agentic Code Review

- Owner: Li and coauthors
- Class: 2026 repository-mining preprint
- Canonical reference: https://arxiv.org/abs/2603.15911
- Locators: RQ1 through RQ3, especially sections III-B and III-C
- Authority: 278,790 inline conversations across 300 GitHub projects
- Limits: bot identity, authorship, adoption, and quality changes are inferred from repository traces

### SRC-020: Rethinking Code Review Workflows With LLM Assistance

- Owner: Fannar Steinn Aðalsteinsson and coauthors
- Class: 2025 field-study preprint
- Canonical reference: https://arxiv.org/pdf/2505.16339
- Locators: abstract, section IV methodology, and section V results
- Authority: developer interviews and field experiment at WirelessCar
- Limits: seven initial interviews and ten field participants at one company; measures experience, not defect superiority

### SRC-021: How To Write Code Review Comments

- Owner: Google Engineering Practices
- Class: first-party engineering guidance
- Canonical reference: https://google.github.io/eng-practices/review/reviewer/comments.html
- Locators: sections "Courtesy," "Explain Why," "Giving Guidance," and "Label Comment Severity"
- Authority: documented guidance for clear and useful comments
- Limits: practitioner guidance, not an empirical correctness measure

### SRC-022: Modern Code Review, A Case Study At Google

- Owner: Caitlin Sadowski, Emma Söderberg, Luke Church, Michal Sipko, and Alberto Bacchelli
- Class: peer-reviewed ICSE SEIP 2018 industrial case study
- Canonical reference: https://research.google/pubs/modern-code-review-a-case-study-at-google/
- Locators: abstract; paper sections 5 through 8
- Authority: 12 interviews, 44 survey respondents, and logs for 9 million reviewed changes
- Limits: exploratory study within one large engineering organization

## Pull Request And Validation Operations

### SRC-023: Comparing Branches In Pull Requests

- Owner: GitHub Docs
- Class: official platform documentation
- Canonical reference: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-comparing-branches-in-pull-requests
- Locators: "Three-dot and two-dot Git diff comparisons," "About three-dot comparison on GitHub," and "Reasons diffs will not display"
- Authority: GitHub pull request diff behavior and display limits
- Limits: platform behavior, not local repository completeness

### SRC-024: git-diff

- Owner: Git project
- Class: official Git documentation
- Canonical reference: https://git-scm.com/docs/git-diff
- Locators: synopsis and description for `git diff A...B`; options `--find-renames`, `--find-copies`, `-l<num>`, and `--submodule`
- Authority: local diff and heuristic rename behavior
- Limits: does not define GitHub commentability

### SRC-025: git-merge-base

- Owner: Git project
- Class: official Git documentation
- Canonical reference: https://git-scm.com/docs/git-merge-base
- Locators: "Description," "Operation Modes," `--all`, `--is-ancestor`, and criss-cross merge discussion
- Authority: ancestry and best-common-ancestor semantics
- Limits: repository history may be shallow or incomplete

### SRC-026: Pull Request Files REST Endpoint

- Owner: GitHub REST API Docs
- Class: official platform API documentation
- Canonical reference: https://docs.github.com/en/rest/pulls/pulls
- Locator: "List pull requests files"
- Authority: changed-file API fields and 3,000-file cap
- Limits: API inventory may not cover hidden or excess local changes

### SRC-027: Customizing Changed File Display

- Owner: GitHub Docs
- Class: official platform documentation
- Canonical reference: https://docs.github.com/en/repositories/working-with-files/managing-files/customizing-how-changed-files-appear-on-github
- Locator: `linguist-generated`
- Authority: generated-file display behavior
- Limits: hidden display does not define whether a generated contract matters

### SRC-028: git-worktree

- Owner: Git project
- Class: official Git documentation
- Canonical reference: https://git-scm.com/docs/git-worktree
- Locators: description; `--detach`; `remove`; `--force`
- Authority: linked-worktree creation and removal behavior
- Limits: a worktree isolates files, not credentials, network, hooks, or host access

### SRC-029: git-status

- Owner: Git project
- Class: official Git documentation
- Canonical reference: https://git-scm.com/docs/git-status
- Locators: "Porcelain Format Version 1" and "Porcelain Format Version 2"
- Authority: script-stable worktree status
- Limits: status does not prove external process side effects are absent

### SRC-030: Checking Out Pull Requests

- Owner: GitHub CLI and GitHub Docs
- Class: official tool and platform documentation
- Canonical references: https://cli.github.com/manual/gh_pr_checkout and https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/checking-out-pull-requests-locally
- Locators: `gh pr checkout --detach` and `refs/pull/ID/head`
- Authority: fetching and checking out pull request heads, including fork pull requests
- Limits: local checkout still needs repository and SHA verification

### SRC-031: Pull Request Review Comments REST API

- Owner: GitHub REST API Docs
- Class: official platform API documentation
- Canonical reference: https://docs.github.com/en/rest/pulls/comments
- Locators: "Create a review comment for a pull request," `commit_id`, `line`, `side`, `start_line`, and `start_side`
- Authority: current inline comment anchor contract
- Limits: review comments are only one GitHub discussion surface

### SRC-032: Issue Comments REST API

- Owner: GitHub REST API Docs
- Class: official platform API documentation
- Canonical reference: https://docs.github.com/en/rest/issues/comments
- Locator: pull request issue comments
- Authority: general pull request conversation retrieval
- Limits: excludes inline review threads and review bodies

### SRC-033: Pull Request Reviews REST API

- Owner: GitHub REST API Docs
- Class: official platform API documentation
- Canonical reference: https://docs.github.com/en/rest/pulls/reviews
- Locators: "Create a review for a pull request" and "Submit a review for a pull request"
- Authority: review bodies, pending reviews, and grouped inline comments
- Limits: thread resolution details need GraphQL

### SRC-034: Pull Request Review Threads GraphQL API

- Owner: GitHub GraphQL API Docs
- Class: official platform API documentation
- Canonical reference: https://docs.github.com/en/graphql/reference/pulls
- Locators: `PullRequest.reviewThreads` and `PullRequestReviewThread`
- Authority: thread resolution, outdated state, paths, sides, lines, and replies
- Limits: paginated retrieval is required for completeness

### SRC-035: Reviewing Dependency Changes

- Owner: GitHub Docs
- Class: official platform documentation
- Canonical reference: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/reviewing-dependency-changes-in-a-pull-request
- Locator: final note in "Reviewing dependencies in a pull request"
- Authority: dependency review behavior and parser limits
- Limits: does not replace manifest, lockfile, lifecycle-script, or source review

### SRC-036: Immutable JavaScript Package Installs

- Owners: npm, pnpm, and Yarn
- Class: official package-manager documentation
- Canonical references: https://docs.npmjs.com/cli/v8/commands/npm-ci/, https://pnpm.io/cli/install, and https://yarnpkg.com/cli/install
- Locators: npm `ci` description; pnpm `--frozen-lockfile`; Yarn `--immutable`
- Authority: install behavior that detects lockfile drift
- Limits: an immutable install can still execute untrusted lifecycle scripts

### SRC-037: Playwright Web Server And Tracing

- Owner: Playwright Docs
- Class: official browser-testing documentation
- Canonical references: https://playwright.dev/docs/test-webserver and https://playwright.dev/docs/best-practices
- Locators: web server configuration and "Debugging on CI"
- Authority: starting a local application and capturing browser traces
- Limits: a trace shows exercised paths only

### SRC-038: GitHub Actions Workflow Syntax

- Owner: GitHub Docs
- Class: official platform documentation
- Canonical reference: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Locators: `on.<push|pull_request>.paths` and "Git diff comparisons"
- Authority: event, filter, and 3,000-file path-filter behavior
- Limits: a green check does not show that the intended workflow still triggered

### SRC-039: Secure Use Of GitHub Actions

- Owner: GitHub Docs
- Class: official security guidance
- Canonical reference: https://docs.github.com/en/actions/reference/security/secure-use
- Locators: "Use credentials that are minimally scoped" and "Pin actions to a full-length commit SHA"
- Authority: GitHub Actions token and dependency hardening guidance
- Limits: project-specific threat models still matter

### SRC-040: Secure Use Of pull_request_target

- Owner: GitHub Docs
- Class: official security guidance
- Canonical reference: https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- Locators: "The risks" and "Deciding whether to use"
- Authority: risks of running pull request code with write tokens or secrets
- Limits: focuses on GitHub Actions, while local review execution has similar but not identical risks

### SRC-041: Graphite CLI Quick Start

- Owner: Graphite Docs
- Class: official stacked-pull-request tool documentation
- Canonical reference: https://graphite.com/docs/cli-quick-start
- Locators: "Stacking a second pull request" and "Addressing reviewer feedback"
- Authority: parent-based stack behavior and restacking
- Limits: describes Graphite stacks only

### SRC-042: Sapling Stack

- Owner: Sapling Docs
- Class: official stacked-change tool documentation
- Canonical reference: https://sapling-scm.com/docs/git/sapling-stack/
- Locator: caution under `sl pr submit --stack`
- Authority: overlapping trunk-based pull request behavior
- Limits: describes Sapling stack mode only

### SRC-043: git-range-diff

- Owner: Git project
- Class: official Git documentation
- Canonical reference: https://git-scm.com/docs/git-range-diff
- Locators: "Description" and "Output Stability"
- Authority: human comparison of two patch-series versions
- Limits: output is not stable for machine parsing

## Security And AI Review Method Sources

### SRC-044: NIST Secure Software Development Framework 1.1

- Owner: National Institute of Standards and Technology
- Class: final public standard, NIST SP 800-218
- Canonical reference: https://doi.org/10.6028/NIST.SP.800-218
- Locators: table 1, PW.7.1, PW.7.2, PW.8.1, PW.8.2, and RV.3.1
- Authority: outcome-based secure software development practices
- Limits: organization-level framework, not a pull request review algorithm

### SRC-045: Philosophical Dispositions As Behavioral Constraints For AI-Assisted Code Review

- Owner: Kaushal Bansal
- Class: 2026 empirical preprint
- Canonical reference: https://arxiv.org/abs/2605.23108
- Locators: sections III-D, IV-A, V-B.4, VI, VII, and appendix A
- Authority: 50-pull-request study of four distinct review dispositions with a generic-prompt baseline
- Limits: one primary model, author-only matching, no independent rater, and a three-pull-request cross-model check

### SRC-046: SWE-PRBench

- Owner: Deepak Kumar
- Class: 2026 evaluation preprint
- Canonical reference: https://arxiv.org/abs/2603.26130
- Locators: abstract; sections 6.3, 6.4, and 8; tables 8 through 10
- Authority: 350 annotated pull requests and context-configuration comparisons across eight models
- Limits: results use a 100-pull-request sample, are Python-heavy, and rely on LLM judges with moderate cross-judge agreement

### SRC-047: SWR-Bench

- Owner: Zhengran Zeng and coauthors
- Class: 2026 FSE paper
- Canonical reference: https://arxiv.org/abs/2509.01494
- Locators: table 7; sections RQ3, 5, and 6; figures 7 through 9
- Authority: 1,000 manually verified pull requests, multiple review tools and models, and multi-review aggregation experiments
- Limits: ground truth comes from historical change actions and evaluation includes model-based components

## Falsification Sources

### SRC-048: Experimental Evaluation Of Independence In Multi-Version Programming

- Owner: John C. Knight and Nancy G. Leveson
- Class: peer-reviewed fault-tolerance experiment
- Canonical reference: https://people.cs.rutgers.edu/~uli/cs673/papers/EvaluationMultiVersionProgramming86.pdf
- Locators: abstract and section 8, PDF pages 19 through 20
- Authority: one million tests across 27 independently written implementations
- Limits: multi-version programming is an analogy for correlated workbench errors, not direct LLM evidence

### SRC-049: LLM Prompt Injection Prevention Cheat Sheet

- Owner: OWASP
- Class: official community security guidance
- Canonical reference: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- Locators: "Remote/Indirect Prompt Injection" and "Model-Based Guardrails"
- Authority: threat sources and defense limits for LLM applications
- Limits: guidance is broader than code review and evolves over time

### SRC-050: JavaScript And TypeScript Data Flow In CodeQL

- Owner: GitHub CodeQL Docs
- Class: official static-analysis documentation
- Canonical reference: https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-javascript-and-typescript/
- Locators: local-flow limitations and "Global data flow"
- Authority: documented precision and reach tradeoff for local and global data flow
- Limits: CodeQL behavior does not prove an LLM retrieval method

### SRC-051: Tricorder

- Owner: Google researchers
- Class: peer-reviewed industrial static-analysis system paper
- Canonical reference: https://research.google.com/pubs/archive/43322.pdf
- Locators: section III.A, pages 1 through 2; section III.D, page 2; section IV.C, page 5
- Authority: production evidence on false-positive control, changed-line placement, actionability, and adoption
- Limits: Google's environment and analyzers differ from open-ended agent review

### SRC-052: SARIF 2.1.0

- Owner: OASIS
- Class: technical standard
- Canonical reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
- Locator: section 3.27.12, `locations`
- Authority: result-location grouping rule based on whether every location must change for correction
- Limits: static-analysis result representation, not a complete semantic deduplication method

### SRC-053: Improving Spectrum-Based Localization Of Multiple Faults

- Owner: Callaghan and Fischer
- Class: fault-localization research preprint
- Canonical reference: https://arxiv.org/abs/2306.09892
- Locators: abstract and masked-fault discussion in the method section
- Authority: evidence that multiple faults can mask one another
- Limits: analogy to review clustering rather than direct review evidence

### SRC-054: Best Practices For Reviewing Stacked Pull Requests

- Owner: Graphite Docs
- Class: official stacked-pull-request tool guidance
- Canonical reference: https://www.graphite.com/docs/best-practices-for-reviewing-stacks
- Locator: best-practice items 1 through 4
- Authority: bottom-up independent review with upstack context
- Limits: Graphite's parent-based stack model

### SRC-055: Gerrit Hazardous Rebases

- Owner: Gerrit Documentation
- Class: official review-tool documentation
- Canonical reference: https://gerrit-review.googlesource.com/Documentation/user-review-ui.html
- Locator: "Hazardous Rebases"
- Authority: documented empty-diff hazard after squash and rebase
- Limits: Gerrit-specific interface and history presentation

### SRC-056: Secure Code Review Cheat Sheet

- Owner: OWASP
- Class: official community security guidance
- Canonical reference: https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html
- Locators: "Preparation," "Manual Analysis Techniques," and "Automated Tool Integration"
- Authority: architecture, requirements, threat-model, trust-boundary, path-tracing, and tool-triage guidance
- Limits: broad guidance rather than a tested pull request workflow

### SRC-057: NIST AI 800-3

- Owner: National Institute of Standards and Technology
- Class: official AI evaluation guidance
- Canonical reference: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-3.pdf
- Locators: sections 2.1 and 3.1, PDF pages 2 through 7
- Authority: fixed-benchmark versus generalized accuracy, nondeterminism, and uncertainty
- Limits: general AI evaluation guidance, not code-review-specific thresholds

### SRC-058: npm Lifecycle Scripts

- Owner: npm Docs
- Class: official package-manager documentation
- Canonical references: https://docs.npmjs.com/cli/using-npm/scripts/ and https://docs.npmjs.com/cli/install/
- Locators: "Life Cycle Operation Order," `npm ci`, `npm install`, and `ignore-scripts`
- Authority: install-time code execution behavior
- Limits: other package managers and repository scripts need their own inspection
