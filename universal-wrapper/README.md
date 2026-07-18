# OCODE Universal Wrapper v0.3 — Founder Proof Vertical Slice

Truth status: `IMPLEMENTED_AND_AUTOMATED_TESTS_PASS__ONE_ADAPTER_ONLY__DEVICE_PREVIEW_PENDING`

This package proves one bounded OCODE round trip:

```text
Natural-language intent
→ platform-neutral semantic contract
→ dreamer/environment profile
→ route-fit decision
→ minimum law activation
→ Expo/TypeScript source generation
→ automated model and persistence tests
→ controlled code-to-specification reconstruction
→ evidence and continuation package
```

## Exact command

```bash
cd universal-wrapper
node bin/ocode.mjs build examples/dream-intake.intent.txt --adapter expo-typescript --out proofs/dream-intake-v0.3
```

After an npm link, the equivalent command is:

```bash
ocode build examples/dream-intake.intent.txt --adapter expo-typescript --out proofs/dream-intake-v0.3
```

## Verify the founder proof

```bash
npm test
```

No production credentials, backend, live AI API, customer data, store account, or physical-device access is required.

## What the founder proof establishes

- One natural-language instruction generates the complete required artifact package.
- The semantic contract contains no target-language or target-framework assumptions.
- One replaceable adapter generates a phone-first React Native screen, pure model, and persistence adapter.
- The pure TypeScript model and persistence behavior run through automated Node tests.
- A controlled manifest-assisted reverse pass reconstructs and checks all five critical behaviors.
- Claims clearly distinguish generated source, Node-tested behavior, structural screen validation, device runtime, and production operation.
- `CONTINUATION.md` gives another compatible builder the regeneration command, proof boundary, stop condition, and next decision.

## Bounded Expo phone-preview proof

The selected next proof is implemented under:

```text
universal-wrapper/phone-preview/
```

It reuses the same single Dream Intake behavior and adds only:

- a minimal Expo SDK 54 application shell;
- strict TypeScript checking;
- Expo Doctor verification;
- iOS and Android JavaScript bundle exports;
- a physical-iPhone validation checklist.

Run its automated verification from `universal-wrapper/phone-preview/`:

```bash
npm install
npm run verify
```

Open the same screen in Expo Go with:

```bash
npm run phone
```

The physical-phone result remains pending until `PHONE_PREVIEW.md` is executed against an identified commit.

## What is not yet established

- Launch and interaction on Otto's physical iPhone.
- Native `.ipa` or `.apk` compilation.
- App Store or Google Play release.
- Production security, privacy, identity, backend, payments, or support.
- Arbitrary code understanding.
- Cross-language universality.
- Permanent selection of Expo as Dream Builder architecture.

## Stop condition

The founder proof and phone-preview extension remain limited to one screen, one adapter, one generated test suite, one reconstruction, one bundle-verification path, and one continuation package. Additional screens, adapters, infrastructure, or deployment are separate decisions requiring path re-ranking.
