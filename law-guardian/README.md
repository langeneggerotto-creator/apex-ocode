# OCODE Law Guardian and Policy Compiler v0.1

Truth status: `IMPLEMENTED_AND_LOCALLY_TESTED__LIMITED_VERTICAL_SLICE__NOT_PRODUCTION_VALIDATED`

This module is the first executable vertical slice of OCODE's law-economy function. It converts a large law inventory and a task context into a compact, human-visible Active Law Receipt.

## Implemented flow

```text
Task context
→ context and risk classification
→ law normalization
→ applicability filtering
→ duplicate-control merging
→ conflict detection
→ evidence and blocker evaluation
→ burden/protection estimate
→ simplification recommendations
→ Active Law Receipt
```

## Implemented safeguards

- Constitutional and mandatory protections cannot be dropped merely because they are burdensome.
- A binding nonmandatory rule without a named failure mode is downgraded to advisory.
- Expired temporary rules are not activated.
- Duplicate laws compile into one control group while preserving source traceability.
- Material law conflicts trigger human review.
- `UNKNOWN` risk is not treated as ready.
- Missing evidence for constitutional or universal mandatory laws blocks progression.
- Every receipt preserves human appeal, hold, and stop authority.

## Run

```bash
cd law-guardian
npm test
npm run demo
npm run demo:high-risk
```

The CLI accepts a law inventory JSON file and a task-context JSON file:

```bash
node src/cli.mjs examples/laws.json examples/prototype-context.json receipt.json
```

Exit codes:

- `0`: proceed or proceed with controls
- `3`: hold for human review
- `1`: invalid input or runtime failure
- `2`: invalid CLI usage

## Current limits

- Applicability is deterministic and rule-based; no semantic AI classifier is included yet.
- Burden and protection values are supplied estimates, not measured outcomes.
- The module does not execute the compiled controls.
- It does not yet read the canonical Core OS registry automatically.
- It does not yet write to the APEX Evidence Ledger.
- It does not yet include a user interface.
- Legal, regulatory, safety, and constitutional classifications still require governed human review.

## Next build

`OCODE_LAW_GUARDIAN_v0.2_REGISTRY_ADAPTER_AND_EVIDENCE_RECEIPT`

Planned scope: load canonical laws from the Core OS registry, emit a schema-validated compliance receipt, and write an evidence-compatible record for `apex-evidence-ledger`.
