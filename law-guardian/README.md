# OCODE Law Guardian and Policy Compiler v0.2

Truth status: `IMPLEMENTED_AND_CI_TESTED__PINNED_CANONICAL_REGISTRY_ADAPTER__NOT_PRODUCTION_VALIDATED`

v0.2 connects the deterministic policy compiler to a provenance-recorded snapshot of the canonical APEX Core OS Universal Laws Registry and produces a formal, schema-validated record compatible with `apex-evidence-ledger`.

## Executable flow

```text
Canonical registry + contract + source manifest
→ registry/contract consistency validation
→ one-to-one canonical law mapping
→ context and risk classification
→ applicability filtering
→ duplicate-control compilation
→ conflict and evidence checks
→ Active Law Receipt
→ Evidence Ledger policy record
→ formal schema validation
```

## Canonical-source boundary

The Core OS source repository is private. The default runtime therefore uses pinned snapshots with canonical repository paths and source blob SHAs. It reports `PINNED_SNAPSHOT` or `STALE_SNAPSHOT`, keeps `drift_check_required=true`, and never describes a snapshot as live synchronization.

The adapter also accepts fresh local files or authenticated GitHub/API URLs. Cross-repository live access requires an authorized token supplied as `CORE_OS_GITHUB_TOKEN` or through the adapter options.

## Run

```bash
cd law-guardian
npm test
npm run demo:registry
```

Direct command:

```bash
node src/registry-cli.mjs \
  examples/prototype-context.json \
  policy-receipt-v0.2.json \
  core-os-policy-evidence-v0.1.json
```

The generated evidence record validates against:

```text
schemas/core-os-policy-evidence-record-v0.1.schema.json
```

The authoritative schema is maintained in `langeneggerotto-creator/apex-evidence-ledger` and is vendored here with source provenance for portable validation.

## Implemented safeguards

- Registry and contract law, dimension, status, and version drift are blocked.
- Every canonical law must have exactly one runtime policy mapping.
- Twenty-four canonical laws compile into a smaller set of user-facing controls while preserving source-law traceability.
- Constitutional protections cannot be removed to reduce burden.
- Missing truth evidence, unknown risk, or material conflicts can hold progression.
- Pinned and stale snapshots are visibly distinguished from authenticated or live sources.
- Evidence records preserve registry hashes, source blob references, unresolved gaps, human-review state, and truth boundaries.
- Formal schema validation fails closed before an evidence record is emitted as valid.

## Current limits

- The runtime policy map is a derived interpretation layer and requires periodic human review.
- A pinned snapshot does not prove the private Core OS repository has not changed.
- OCODE produces Evidence Ledger-compatible files but does not yet write through a live Evidence Ledger storage API.
- The compiler does not execute the selected controls.
- Burden and protection values remain configured estimates rather than calibrated measurements.
- No graphical Active Law Receipt interface exists yet.
- High-stakes legal, medical, financial, engineering, safety, and constitutional decisions still require qualified human review.

## Next build

`OCODE_LAW_GUARDIAN_v0.3_AUTHENTICATED_SYNC_AND_EVIDENCE_LEDGER_WRITER`

Planned scope: authenticated canonical drift checks, controlled Evidence Ledger write integration, idempotent receipt storage, and cross-repository provenance verification.
