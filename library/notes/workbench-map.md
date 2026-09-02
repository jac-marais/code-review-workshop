# Workbench Map

Run every baseline workbench for every change. A router may add specialists but cannot remove the baseline.

| Workbench | Failure model | Required evidence |
| --- | --- | --- |
| Behavior and contracts | The change violates a user, caller, schema, API, compatibility, or ownership contract. | Entry-point trace, callers and callees, types or schemas, requirements treated as claims, and concrete counterexample. |
| State and failure | The happy path hides a bad state transition, race, partial effect, retry, timeout, resource, or dependency-failure path. | State trace, failure injection or counterexample, focused execution where safe, and recovery behavior. |
| Security and privacy | Untrusted input, authority, tenant, secret, personal data, dependency, or abuse boundary is crossed incorrectly. | Code-first source-to-sink or trust-boundary trace, then an intent-aware challenge with threat and history context. |
| Design and maintainability | The change creates duplicated decisions, hidden states, parallel update duties, misleading boundaries, or concrete long-term failure risk. | Rules for Robust Software, repository conventions, call sites, types, ownership boundaries, and a named maintenance consequence. |
| Evidence and integration | Tests, CI, generated output, config, deployment, migration, rollback, or browser behavior fails to establish the authored result. | Test mutation question, command scope, CI trigger trace, artifact comparison, integration state, and real-browser evidence when relevant. |

Triggered specialists cover distinct methods such as accessibility and visual behavior, concurrency, persistence and migration, dependency and supply chain, performance and resources, protocol compatibility, and domain rules.

A specialist is justified by a surface in the change map and a distinct evidence obligation. A renamed reviewer with the same scope and reasoning is not another workbench.
