# APEX OIC Gate Hub Autocommit Contract

Status: ACTIVE

Purpose: make GitHub sync a required gate for every future APEX OIC build when repository access is available.

## Autocommit Rule
A build is not considered complete until the Gate Hub writes the commit record or reports why it could not commit.

## Required Repositories
- Code/spec repository: langeneggerotto-creator/apex-ocode
- Evidence/proof repository: langeneggerotto-creator/apex-evidence-ledger

## Required Commit Outputs
For every future build, commit these records where applicable:

1. Build manifest
2. Source or app entry file
3. Spec or implementation notes
4. Deployment/status file
5. Verification summary
6. Artifact hash manifest
7. Evidence/proof entry

## Required Response Fields
Every future build response must report:

- GitHub Status
- Code Repo
- Evidence Repo
- Branch
- Commit SHA values
- Files written
- Evidence ledger status
- Blocked items
- Next GitHub action

## Boundary
This contract does not mean GitHub commits can happen outside an active authorized session unless a separate GitHub Action, scheduled job, or external runner is configured. Inside active ChatGPT build sessions, the assistant must perform the GitHub write step automatically after generating build artifacts.

## Current Anchor
- Sync repair: APEX_OIC_GitHub_Sync_Repair_v1_2_1
- Current build: APEX_OIC_Hosted_Prototype_Activation_v1_2
