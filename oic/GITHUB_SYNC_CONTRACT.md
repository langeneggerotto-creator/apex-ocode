# APEX OIC GitHub Sync Contract

Status: ACTIVE

This repository is the code/spec record for APEX OIC builds.

## Current Vision Target
Finish the console/dashboard and fix the UI test loop so the platform can move toward infinite zoom and control functions.

## Mandatory Build Doctrine
Every future OIC build should use this chain:

1. O-Code first
2. .OOO native object when the build has object state
3. .OIC deployable container when the build is packaged
4. HTML/runtime adapter only as the viewing or execution layer
5. Simulated UI testing before manual user testing
6. SWOT test commentary for simulator findings
7. GitHub sync status in every build response

## Required Response Fields

- GitHub Status
- Code Repo
- Evidence Repo
- Branch
- Commit SHA
- Files written
- Evidence ledger status
- Next GitHub action

## Repository Roles

- Code and specs: langeneggerotto-creator/apex-ocode
- Evidence and proof entries: langeneggerotto-creator/apex-evidence-ledger

Binary packages may be tracked by filename, size, and SHA-256 hash when direct binary upload is not used.

## Current Anchors

- Hosted activation: APEX_OIC_Hosted_Prototype_Activation_v1_2
- GateHub runner: APEX_OIC_GateHub_Autocommit_Runner_v1_2_2
- SWOT replay: APEX_OIC_SWOT_Visual_Replay_Video_Exporter_v1_2_5_1

## Boundary
Do not claim GitHub sync unless a commit SHA is returned. Do not claim mobile/hosted success without evidence.
