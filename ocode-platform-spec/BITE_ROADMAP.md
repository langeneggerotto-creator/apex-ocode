# OCode Incremental Build Roadmap

OCode must be built in independently testable and recoverable increments. One bite is active at a time.

## Standard bite lifecycle

1. Confirm predecessor release is sealed.
2. Run baseline tests before modification.
3. Write a bounded plan naming affected files, contracts, risks, tests, evidence, and rollback.
4. Implement only the selected capability.
5. Add unit, contract, integration, workflow, negative, and abuse tests as applicable.
6. Run all mandatory gates.
7. Install or deploy the built artifact in a clean environment.
8. Demonstrate rollback.
9. Generate evidence and update truth labels.
10. Commit, package, and stop.

## Bite 1 — Sandbox and workspace trust — v3.1

Linux OS-level sandbox, workspace trust, deny-by-default network, protected metadata, resource limits, adversarial isolation tests, and fail-closed behavior. This is the first required security foundation.

## Bite 2 — Persistent integrated terminal — v3.2

Sandboxed PTY sessions, resize, reconnect, scrollback, command history, stop escalation, timeout, streaming, terminal evidence, and mobile-safe controls.

## Bite 3 — Tasks and runtime profiles — v3.3

Declarative run, test, lint, format, type-check, build, preview, and migration tasks; structured job states; logs; cancellation; concurrency and resource policy.

## Bite 4 — Professional editor foundation — v3.4

Monaco integration, multiple tabs, split panes, unsaved states, search and replace, diff editor, diagnostics, symbols, formatting, accessibility, and recovery.

## Bite 5 — Source-control workspace — v3.5

Graphical Git, staging, branch lifecycle, history, tags, stash, conflicts, review checks, provider contracts, and restore operations.

## Bite 6 — Debugging — v3.6

Debug Adapter Protocol broker, breakpoints, stepping, variables, watches, call stacks, debug console, Python and Node adapters, and debug evidence.

## Bite 7 — AI provider and agent layer — v3.7

Provider-neutral adapters, model registry, governed agent tools, plan approval, budgets, context provenance, prompt-injection defenses, replay, evaluation, and fallback.

## Bite 8 — Reproducible environments — v3.8

Dev Containers, Dockerfiles, environment profiles, dependency policy, package proxies, caches, lifecycle, snapshots, and environment attestations.

## Bite 9 — Secrets, previews, and deployment — v3.9

Encrypted secret references, authenticated port previews, preview environments, deployment adapters, release manifests, SBOM, signing, promotion, and rollback.

## Bite 10 — Identity and collaboration — v4.0

Authentication, MFA, SSO, organizations, teams, roles, fine-grained authorization, reviews, comments, presence, notifications, shared sessions, and audit.

## Bite 11 — Observability and operations — v4.1

Logs, metrics, traces, health, dashboards, alerts, SLOs, incidents, backup, restore, disaster recovery, support, and deletion verification.

## Bite 12 — Extensibility and integrations — v4.2

Extension SDK, provider SDK, capability manifests, permission model, signing, isolated extension hosts, Git, issue, chat, registry, CI, and cloud integrations.

## Bite 13 — Multi-tenant production hardening — v5.0

Tenant isolation, dedicated execution tiers, quotas, metering, billing, abuse controls, security qualification, penetration testing, regional resilience, and production support.

## Mandatory entry gates

- Previous bite sealed and recoverable
- Baseline tests green
- Architecture and security impacts documented
- Acceptance criteria and failure states specified
- Rollback strategy present

## Mandatory exit gates

- Specification gate passes
- Build and packaging pass
- Functional tests pass
- Security and abuse tests pass
- Reliability and rollback pass
- Operability assets exist
- Evidence manifest complete
- Highest truth label supported by evidence
- Release commit clean and recoverable

## Scope prohibition

Do not implement later-bite capabilities except the minimum interfaces required by the selected bite. Any interface without behavior must be labeled `SCAFFOLDED`.
