# Claude Code Master Build Prompt — APEX OCode

You are building OCode from this GitHub repository.

Your mission is to implement the complete target platform, but only through the bite roadmap. Do not attempt the entire platform in one run.

## Startup sequence

1. Read `/CLAUDE.md`.
2. Run `python scripts/ocode_spec_gate.py`.
3. Read `ocode-platform-spec/FULL_PLATFORM_SPEC.md`.
4. Read `ocode-platform-spec/BITE_ROADMAP.md`.
5. Select only the first eligible incomplete bite.
6. Inspect the current repository and map existing capabilities to the selected bite.
7. Write a detailed plan including files, contracts, migrations, risks, tests, evidence, and rollback.
8. Implement, test, verify, package, and evidence only that bite.
9. Stop after the bite is sealed.

## Required output for each bite

- Bounded implementation plan
- Architecture changes and ADRs
- Source changes
- Data and API migrations
- Unit, contract, integration, browser, CLI, negative, and security tests as applicable
- Security review
- Install or deployment proof
- Rollback proof
- Evidence manifest
- Truth-label updates
- Residual risks and known gaps
- Next eligible bite, without starting it

## Decision rules

- Prefer small reviewable changes.
- Fail closed.
- Preserve repository ownership and portability.
- Never bypass workspace trust.
- Never pass raw secrets to a model.
- Never execute repository-controlled hooks by default.
- Never expose control-plane networks to untrusted sandboxes.
- Never infer production readiness from local tests.
- Never weaken a gate to obtain a pass.
- Never claim completion without exact commands and evidence paths.
