# DreamMusicForge Repair Compiler v0.1

The Repair Compiler converts a rejected or unresolved Render Verification report into a bounded minimal-change repair contract.

## Canonical rule

Repair may not rewrite film truth. Every passing metric is preserved. Only failed or unresolved dimensions may change, and every change must be explicit.

## Supported actions

- REGENERATE
- RELIP_SYNC
- REPLACE_LAYER
- SHORTEN_SHOT
- EDITORIAL_CONCEALMENT
- REDESIGN_TASK
- MANUAL_REVIEW

## Routing

- identity/costume/world failure -> regenerate with stronger references
- lip-sync failure -> preserve picture and route to dedicated lip-sync
- continuity failure -> least-invasive editorial concealment
- duration/technical failure -> trim or re-segment
- layer/composite failure -> replace failed layer only
- unknown critical failure -> return to Production Strategy for redesign
- unresolved evidence without failure -> manual review

Accepted candidates cannot produce repair contracts.
