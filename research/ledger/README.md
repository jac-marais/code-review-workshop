# Research Ledger

The ledger stores provisional research records. A convergence report must approve a finding before it becomes operating guidance.

## Record IDs

- Sources: `SRC-###`
- Claims: `CLM-###`
- Contradictions: `CTR-###`
- Methods: `MTH-###`
- Threads: `THR-###`

Semantic changes create a new record that supersedes the old one. Editorial fixes may update a revision field.

## Required Fields

### Source

ID, title, owner, source class, version or date, URL, exact locator, authority, use limits, retrieval date, and local note path.

### Claim

ID, one atomic statement, claim kind, scope, supporting and challenging source IDs, explicit or inferred derivation, certainty, status, and method effect.

### Contradiction

ID, disputed axis, claim IDs, stakes, type, disposition, resolution basis, and remaining uncertainty.

### Method

ID, job, trigger, inputs, ordered procedure, outputs, supporting claims, applicability, failure modes, validation plan, and maturity.

### Thread

ID, question, why it matters, triggering evidence, gap type, expected information gain, next action, state, and resolution references.
