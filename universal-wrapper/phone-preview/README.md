# OCODE Dream Intake Expo Phone Preview v0.3.1

Truth status: `IMPLEMENTED__CI_NATIVE_EXPORT_REQUIRED__PHYSICAL_IPHONE_PREVIEW_PENDING`

This project takes the exact one-screen Dream Intake founder proof and places it inside a minimal Expo SDK 54 application suitable for Expo Go preview on a current physical iPhone during the SDK 57 transition period.

## Scope

```text
One existing Dream Intake screen
→ minimal Expo application shell
→ strict TypeScript check
→ domain and persistence tests
→ iOS JavaScript export
→ Android JavaScript export
→ phone-preview handoff
```

No second screen, backend, live AI API, authentication, payment, app-store release, additional adapter, or production infrastructure is included.

## Verify the project

```bash
npm install
npm run verify
```

The verification sequence runs:

1. Expo Doctor;
2. TypeScript checking;
3. five domain and persistence tests;
4. Expo iOS export;
5. Expo Android export;
6. bundle presence and SHA-256 verification.

## Open on a physical iPhone

1. Install Expo Go from the iOS App Store.
2. Open this directory on a computer connected to the same Wi-Fi network as the iPhone.
3. Run `npm install` once.
4. Run `npm run phone`.
5. Scan the displayed QR code with the iPhone camera and open it in Expo Go.
6. Complete the checklist in `PHONE_PREVIEW.md`.

When LAN discovery is blocked, run `npm run phone:tunnel` instead.

## Evidence boundary

A successful CI export proves that Metro generated platform-targeted JavaScript and asset bundles. It does not prove:

- native `.ipa` or `.apk` compilation;
- installation or launch on a physical phone;
- touch behavior or visual correctness on Otto's iPhone;
- durable AsyncStorage behavior after closing and reopening Expo Go;
- production security, privacy, availability, or support;
- permanent selection of Expo as the Dream Builder architecture.

Physical-phone status must remain `PENDING` until the checklist is executed and evidence is recorded.
