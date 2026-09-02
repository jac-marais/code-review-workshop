# Robustness Checklist: Detailed Evaluation Guide

Work through each rule in order. For every rule, follow the detection steps, then record any violations.

---

## Rule 0: One decision, one place

**Principle:** Every decision (business rule, constant, configuration, transformation) should live in exactly one location.

### Detection steps

1. **Scan for scattered conditionals.** Look for `if`/`switch` statements that branch on the same flag, discriminator, or state value in multiple places. This is the most common Rule 0 violation. When a new variant is added, every scattered conditional must be found and updated. Miss one and you have a bug. The fix is typically a data-driven lookup (`Record`, `Map`, config object) or a discriminated union with exhaustive matching. Also look for:
   - The same calculation or formula appearing in multiple places
   - Identical validation rules applied in different files or functions

2. **Check for magic values.** Look for hardcoded strings, numbers, or configuration values that appear more than once. Each should be a named constant or config entry.

3. **Look for parallel update obligations.** If changing one piece of code means you *must* also change another piece to keep things correct, that's a Rule 0 violation. Common patterns:
   - A type/enum defined in one place but manually checked in another without exhaustive matching
   - A mapping (e.g., status codes → messages) duplicated across files
   - A field added to a data structure but requiring manual updates in serialization, validation, and display code

### Severity guide

- **Major:** Duplicated logic where a future change to one copy but not the other would cause a bug or data leak (e.g., duplicated permission checks, duplicated price calculations).
- **Medium:** Duplicated constants or config values that increase the risk of drift.
- **Low:** Minor textual duplication that is unlikely to cause functional issues.

---

## Rule 1: Data for state, functions for processes

**Principle:** Use plain data structures to represent state. Use functions to transition between states. Don't let methods mutate internal object state in ways that leave uncertainty about what fields are set.

### Detection steps

1. **Look for classes/objects that mutate `this`/`self`.** Specifically, methods that assign new properties or change existing ones on the instance. Ask:
   - After calling this method, can the caller be sure which fields are set?
   - Could calling methods in a different order produce an object in an invalid state?

2. **Check for "maybe set" fields.** Look for optional properties on a class/struct that only get assigned inside certain methods. This forces every consumer to check "was this method called yet?"

3. **Identify state transitions that should be explicit.** If an object represents something with distinct phases (anonymous → authenticated, draft → published, pending → approved), each phase should ideally be a separate type or clearly distinguished state, not optional fields on one big type.

4. **Look for cleanup methods (logout, reset, clear).** If a cleanup method must manually unset each field that was set by other methods, that's fragile. A new field added later can easily be forgotten.

### Severity guide

- **Major:** Mutable state where forgetting a field in a cleanup/reset method would leak sensitive data (e.g., user credentials, PII, auth tokens) or produce an invalid state that causes runtime errors.
- **Medium:** Mutable state patterns that are confusing or error-prone but unlikely to cause a security issue.
- **Low:** Stylistic preference (e.g., using a class with simple getters where a plain object would suffice).

---

## Rule 2: Group code by what it does, not what it is

**Principle:** Organize code around behavior/capability rather than domain models. A change to one business rule should ideally touch only one module.

### Detection steps

1. **Check for "God objects."** A single class/module that handles tax calculation, payment processing, invoice generation, email sending, etc. If a class has methods spanning multiple unrelated business concerns, it violates this rule.

2. **Trace a hypothetical change.** Pick one business rule relevant to the changed code (e.g., "tax rate changes") and ask: how many files/modules would need to change? If the answer is more than one or two, the code may be grouped by noun instead of verb.

3. **Look at file/module names.** Names like `OrderService`, `UserManager`, `ProductHelper` that accumulate unrelated methods over time are a smell. Names like `TaxCalculator`, `PaymentValidator`, `InvoiceGenerator` suggest verb-oriented grouping.

### Severity guide

- **Major:** Rarely major on its own. Only major if the poor grouping directly causes a bug (e.g., a tax rule is split across three files and the change only updated two of them).
- **Medium:** A class or module is accumulating responsibilities from different business domains, making future changes risky.
- **Low:** Naming or file structure suggestions that would improve clarity but don't affect correctness.

---

## Rule 3: Repetition is okay, but not encouraged

**Principle:** Don't abstract until you have 3+ genuine instances of the same pattern. Premature abstraction creates junk-drawer functions with growing option bags.

### Detection steps

1. **Look for new abstractions.** Was a new utility function, helper, or wrapper introduced in the change? If so, check:
   - Does it serve 3 or more distinct call sites?
   - Or is it wrapping a single use case that just *might* be reused later?

2. **Check for option-bag functions.** Look for functions that accept a config/options object with multiple boolean flags controlling different behaviors. This is often a sign that unrelated behaviors were merged into one function too early.

3. **Look for "just in case" generalization.** Extra parameters, generic types, or abstraction layers that aren't used by any current caller. If the generality isn't needed today, it's premature.

4. **Check if existing abstractions grew.** If the change adds a new flag or option to an existing utility function, check whether the function is becoming a junk drawer. Would it be cleaner to just write the logic inline at the call site?

### Severity guide

- **Major:** A premature abstraction that actively causes incorrect behavior (rare, but possible when a shared function handles cases differently and a new case doesn't fit).
- **Medium:** A new abstraction that only has 1-2 uses, or an existing abstraction that's growing config flags without clear benefit.
- **Low:** Minor suggestions about when to extract vs. inline.

---

## Rule 4: Use type-safe structures

**Principle:** Use the language's type system to make invalid states unrepresentable. The compiler should catch errors before runtime.

### Detection steps

1. **Look for optional fields that are conditionally required.** If field A is required when field B has a certain value, these should be modeled as a discriminated union (TypeScript), sealed class (Kotlin), enum with associated values (Swift/Rust), etc., not optional fields on a flat type.

2. **Check for boolean-based branching on types.** A `success: boolean` field paired with optional `data?` and `error?` fields is a classic anti-pattern. After checking `success`, the type system should guarantee which fields exist.

3. **Look for stringly-typed data.** Status fields, type discriminators, or action names stored as `string` instead of a union type or enum. These bypass compile-time checking.

4. **Check for `any`, `unknown`, or raw `object` usage.** Are these used where a more specific type could be applied? (Note: `unknown` at an API boundary with subsequent parsing is fine; that's Rule 5.)

5. **Check for runtime type checks that the type system could handle.** Code like `if (typeof x.foo !== 'undefined')` often indicates the type isn't precise enough.

### Severity guide

- **Major:** Invalid states are representable and could cause a runtime crash, data corruption, or security issue (e.g., accessing `.data` when `success` is `false`).
- **Medium:** Types are imprecise but the code handles it safely through runtime checks. The risk is that a future change could skip a check.
- **Low:** Minor type improvements that would add clarity but don't affect safety (e.g., using a string literal union instead of `string` for a non-critical field).

---

## Rule 5: Validate at boundaries, trust internally

**Principle:** Validate external input (API responses, user input, file reads, environment variables) once at the system boundary. Inside the boundary, trust the types.

### Detection steps

1. **Check boundary entry points.** For any new API route, form handler, file reader, or external data consumer in the change:
   - Is there schema validation (e.g., Zod, joi, pydantic, serde) at the point where external data enters the system?
   - Or is the raw data passed through and checked piecemeal deeper in the call stack?

2. **Look for defensive checks deep inside business logic.** If internal functions check `if (!items || !Array.isArray(items))` or `if (typeof x !== 'string')` on data that should already be validated, that's a sign the boundary validation is missing or not trusted.

3. **Check for redundant validation.** The same field validated in the API handler, then again in the service layer, then again in the repository. Once at the boundary is enough.

4. **Look for raw `any` or unvalidated JSON flowing inward.** If `response.json()` or `JSON.parse()` results are used directly without parsing through a schema, that's a boundary validation gap.

### Severity guide

- **Major:** External data enters the system completely unvalidated and is used in a security-sensitive context (database query, auth decision, file path construction).
- **Medium:** Boundary validation exists but is incomplete (e.g., validates shape but not value constraints), or internal code has excessive defensive checks that obscure intent.
- **Low:** Stylistic suggestions about where to place validation or reducing redundant internal checks.
