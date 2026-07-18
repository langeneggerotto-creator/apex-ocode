# OCODE v0.5 — Second-Intent Dual-Adapter Generalization Proof

Truth status: `IMPLEMENTED_PENDING_CI__SECOND_INTENT_TWO_ADAPTERS__NOT_DEVICE_OR_PRODUCTION_VALIDATED`

This proof addresses the next highest OCODE vision barrier after the physical iPhone browser proof passed:

> Is the universal wrapper actually general across intents, or is it only a Dream Intake-specific generator?

## Second intent

```text
Create a phone-first Decision Clarity screen where a person can describe a decision, enter two options and one constraint, save the draft, review a structured Decision Card, correct the interpretation, select a current preference, and receive exactly one next question.
```

## Bounded pipeline

```text
Natural-language Decision Clarity intent
→ deterministic meaning validation
→ platform-neutral semantic contract
→ minimum active-law receipt
→ shared decision model
→ Expo/TypeScript adapter
→ self-contained mobile-web adapter
→ generated shared-model tests
→ source-manifest reconstruction
→ cross-adapter equivalence report
→ evidence and continuation package
```

## Verify

```bash
cd generalization-v0.5
npm run verify
```

## Generated proof

```text
proofs/decision-clarity-v0.5/
├── original-intent.txt
├── semantic-contract.json
├── active-law-receipt.json
├── shared/decision-clarity-model.ts
├── tests/decision-clarity.test.ts
├── adapters/expo-typescript/
│   ├── DecisionClarityScreen.tsx
│   └── decision-clarity-model.ts
├── adapters/mobile-web/index.html
├── reconstructed/expo-spec.json
├── reconstructed/mobile-web-spec.json
├── cross-adapter-equivalence-report.json
├── evidence-receipt.json
└── CONTINUATION.md
```

## What a passing result establishes

- A second materially distinct natural-language intent can be validated and compiled.
- The semantic contract contains no target-framework assumptions.
- Two independent adapters preserve the same fields, behaviors, contract identifier, and exactly-one-question rule.
- The shared decision model passes generated behavior tests.
- Both adapter sources reconstruct to equivalent bounded specifications.

## What it does not establish

- Arbitrary unrestricted natural-language understanding.
- Generalization to every application type or programming language.
- Physical iPhone operation of the second intent.
- Native Expo Go or native binary execution.
- Production security, privacy, deployment, support, or commercial readiness.

## Stop condition

Stop after one second intent, one screen, two adapters, one shared model test suite, one equivalence report, and one continuation package. Do not add a backend, live AI, authentication, payments, app-store deployment, production certification, or a third product screen.
