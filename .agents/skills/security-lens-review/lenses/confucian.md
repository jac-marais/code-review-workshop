# Lens 4: Confucian (Naming & Relations)

Ask: "Do names match reality? What is the relational impact?"

## Refusals

- Refuse to let mismatched names persist
- Refuse to evaluate a name in isolation from its callers and operators

## Focus

Names that mislead developers or operators about security boundaries: env vars that sound safer than they are, client guards named like server guards, two mechanisms sharing one name, one mechanism split across two names. Check: does renaming break callers? What do callers assume versus what actually happens?

## Output schema

Produce 2-5 specific findings on names that mislead about security boundaries. Each finding must reference specific code (file, line, function). Do NOT produce generic advice.

For each finding return markdown with:

- Name
- What it suggests
- What it actually does
- Relational risk (what callers/operators wrongly assume)
- Rename or fix recommendation
