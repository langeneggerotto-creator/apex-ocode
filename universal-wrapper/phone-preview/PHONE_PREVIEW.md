# Physical iPhone Preview Checklist

Build: `OCODE_UNIVERSAL_WRAPPER_v0.3.1_EXPO_BUNDLE_AND_PHONE_PREVIEW_HANDOFF`

Preview status begins as: `NOT_EXECUTED`

## Required environment

- Physical iPhone with Expo Go installed.
- Computer running this repository project.
- iPhone and computer on the same Wi-Fi network, or Expo tunnel mode.
- No production customer data or private information.

## Preview steps

1. Start the project with `npm run phone`.
2. Scan the QR code with the iPhone camera.
3. Confirm Expo Go opens the OCODE Dream Intake Preview.
4. Enter: `I want to own a business that gives me more freedom.`
5. Tap **Save and review my Dream Card**.
6. Confirm the Dream Card displays the exact original words.
7. Confirm a current interpretation appears.
8. Confirm exactly one next question appears.
9. Enter this correction: `I want time freedom through a sustainable owner-controlled business.`
10. Tap **Apply my correction**.
11. Confirm the original words remain unchanged.
12. Confirm the current interpretation changes.
13. Confirm the preserved-corrections count becomes `1`.
14. Close and reopen the project in Expo Go.
15. Confirm the saved dream draft is restored.

## Evidence record

```text
PHONE:
IOS VERSION:
EXPO GO VERSION:
DATE AND TIME:
COMMIT SHA:
CONNECTION MODE: LAN | TUNNEL

APP OPENED: PASS | FAIL
DREAM ENTRY: PASS | FAIL
DRAFT SAVE: PASS | FAIL
DREAM CARD DISPLAY: PASS | FAIL
ORIGINAL WORDS PRESERVED: PASS | FAIL
CORRECTION APPLIED: PASS | FAIL
EXACTLY ONE QUESTION: PASS | FAIL
DRAFT RESTORED AFTER REOPEN: PASS | FAIL
VISUAL OR INTERACTION DEFECTS:
SCREENSHOT OR RECORDING LOCATION:

OVERALL RESULT: PASS | FAIL | PARTIAL
RETEST REQUIRED: YES | NO
```

## Promotion rule

The physical-phone proof may be promoted to `PASS` only when every required behavior above passes on the actual phone and the evidence record identifies the tested commit.

A bundle-export pass alone must not be described as a phone-preview pass.
