# APEX OCode Full Platform Specification

This directory is the canonical product and engineering contract Claude Code must use to evolve this repository into a complete, production-grade development platform.

OCode is not merely an editor, terminal, chatbot, Git client, or deployment tool. It is the governed operating layer joining repositories, code intelligence, terminals, tasks, tests, debugging, source control, AI agents, sandboxes, secrets, previews, deployment, monitoring, evidence, rollback, collaboration, and administration.

## Build model

OCode must be delivered through independently testable bites:

`select one bite → plan → implement → test → inspect → verify → package → evidence → release`

The objective is to prevent oversized changes, stalled environments, false completion claims, and unrecoverable work.

## Start here

1. Read `../CLAUDE.md`.
2. Read `FULL_PLATFORM_SPEC.md`.
3. Read `BITE_ROADMAP.md`.
4. Read `SECURITY_DEPLOYMENT.md`.
5. Read `CLAUDE_CODE_MASTER_PROMPT.md`.
6. Run `python scripts/ocode_spec_gate.py` from the repository root.

## Target outcome

A user can move from an idea to a secure, tested, understandable, maintainable, deployable application while retaining ownership and meaningful control over source code, environments, evidence, costs, approvals, and release decisions.
