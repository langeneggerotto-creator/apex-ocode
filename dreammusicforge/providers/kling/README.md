# DreamMusicForge Kling Production Compiler v0.1

This package is the provider-specific compilation boundary for Kling.

It consumes already-approved DreamMusicForge production state:

- Production Strategy decision
- Transition Requirements
- Renderer Capability Profile
- KlingCreativeContract derived from canonical Production Twin / Film Genome state

It emits a `KlingExecutionPackage` containing:

- provider mode
- bounded duration
- deterministic prompt text
- negative continuity constraints
- required reference manifest
- candidate count
- acceptance gates
- external master-audio requirement
- external lip-sync requirement when Kling cannot own it
- fallback plan inherited from Production Strategy

## Canonical boundary

Kling does not define film truth. DreamMusicForge does.

The compiler never mutates Film Genome or Production Twin state. It only translates already-approved canonical state into a provider-executable package.

## Fail-closed rules

The compiler rejects:

- mismatched transition IDs
- non-Kling capability profiles
- direct renders longer than the declared renderer limit
- controlled continuations without start-frame support or a verified start frame
- invalid creative contracts
- invalid reference manifests

## Current limitations

- This version emits an execution package; it does not submit jobs to Kling.
- Capability values remain supplied by the external Capability Atlas.
- No API credential handling is included.
- No automatic reference upload is included.
- No render-result verification is included here; verification belongs downstream.
- No tests are claimed as executed in connector-only development until independently run.
