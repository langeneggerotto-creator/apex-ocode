# OCode Master Platform Specification

## 1. Product definition

OCode is a provider-neutral, AI-native software-development operating platform coordinating human intent, repositories, editors, terminals, agents, runtimes, security policies, tests, debugging, source control, preview, deployment, monitoring, evidence, and rollback.

## 2. Mission

Enable users—from nonexpert builders to professional teams—to transform a software objective into a working, tested, understandable, maintainable, deployable application without losing ownership or control.

## 3. Product principles

- Secure by default
- Human authority at irreversible boundaries
- Provider neutrality
- Local-first ownership
- Reproducible environments
- Evidence before claims
- Reversible changes
- Least privilege
- Explicit workspace trust
- Bite-size delivery
- Accessible mobile control
- Stable extensibility contracts
- Production operability rather than demo-only behavior

## 4. User classes

### Individual developer
Builds, tests, reviews, and releases local projects.

### Nonexpert builder
Uses natural language while retaining access to plans, code, explanations, and approvals.

### Professional team
Collaborates through shared workspaces, roles, reviews, environments, and policies.

### Platform administrator
Manages identity, tenancy, providers, secrets, quotas, policy, audit, and infrastructure.

### Security and compliance reviewer
Inspects trust, execution isolation, supply-chain controls, evidence, approvals, and incident history.

## 5. Primary user journey

1. Create, clone, or import a repository.
2. Establish workspace trust.
3. Discover architecture, dependencies, tests, and health.
4. Express a change objective.
5. Generate and approve a bounded plan.
6. Create a branch and protected snapshot.
7. Implement through human or governed agent actions.
8. Review exact diffs.
9. Execute inside a governed environment.
10. Run tests, lint, type checks, security scans, and builds.
11. Debug failures.
12. Preview the application.
13. Review evidence and residual risk.
14. Commit, package, release, and deploy.
15. Monitor health and roll back when necessary.

## 6. Platform surfaces

- Web Studio
- Desktop application
- Command-line interface
- Mobile control surface
- REST and WebSocket API
- Agent SDK
- AI-provider adapter SDK
- Extension SDK
- Administrative console

## 7. Workspace and repository management

OCode shall support create, clone, import, fork, archive, restore, and export; repository-confined tree, read, search, create, update, exact replace, move, and delete; optimistic concurrency using content hashes; atomic writes; symlink and path-escape protection; binary and large-file handling; submodules, sparse checkout, monorepos, templates, quotas, background indexing, and explicit trust state.

Every state-changing operation must expose authorization, validation, idempotency, concurrency, audit, evidence, recovery, and UI failure states.

## 8. Professional editor and language intelligence

The target editor shall use Monaco or an equivalent professional editing engine with multi-tab and split-pane support, diff editors, syntax highlighting, formatting, rename, references, hover, completion, diagnostics, symbols, breadcrumbs, outline, search and replace, autosave policy, unsaved-change recovery, merge conflict handling, binary viewers, and a Language Server Protocol broker with isolated per-language processes.

## 9. Terminal, jobs, and tasks

OCode shall provide persistent sandboxed PTY sessions with resize, reconnect, scrollback, exit status, and stop escalation. Structured jobs shall move through queued, leased, running, succeeded, failed, cancelled, and timed-out states. Declarative tasks shall cover run, test, lint, format, type-check, build, preview, migration, release, and deployment. Output shall stream over authenticated channels with resource quotas, timeouts, concurrency limits, environment scrubbing, and evidence capture.

## 10. Testing, quality, and debugging

The platform shall support framework-neutral test discovery and structured results; coverage, lint, formatting, type checks, dependency checks, static analysis, secret scanning, license checks, and configurable quality gates. A Debug Adapter Protocol broker shall provide breakpoints, stepping, variables, watches, call stacks, and debug consoles. The system shall identify flaky tests, support governed retries, and require regression tests for fixed defects.

## 11. Git and change management

OCode shall support status, diff, stage, unstage, commit, history, branches, tags, stash, restore, cherry-pick, rebase, merge, protected branch rules, required checks, review gates, provider adapters for pull or merge requests, conflict resolution, and rollback points. Git credentials must be isolated; hooks, external diff programs, text conversions, prompts, and untrusted configuration are disabled unless explicitly authorized.

## 12. AI and agent orchestration

OCode shall provide a provider-neutral model registry and capability negotiation. Specialized agents may plan, architect, implement, review, test, debug, secure, document, and release, but each receives only task-required tools, context, permissions, time, token budget, and cost budget. The system shall provide repository maps, context retrieval, provenance, prompt-injection defenses, plan approval, diff approval, irreversible-action approval, replay, evaluation, evidence, and provider fallback. No core workflow may depend on one model vendor.

## 13. Sandboxes and reproducible environments

Linux is the reference execution platform. Strong isolation shall use namespaces, seccomp, no-new-privileges, capability drop, cgroups or equivalent quotas, a private filesystem, workspace-only write access, protected OCode metadata, deny-by-default network egress, runtime cleanup, and evidence. Stronger multi-tenant tiers shall support containers and microVMs. Dev Container, Dockerfile, Nix, environment profiles, package proxies, cache boundaries, snapshots, and attestation shall be supported.

## 14. Secrets and configuration

Secrets shall be encrypted through envelope encryption and managed keys, scoped to organization, project, workspace, environment, or deployment, injected by reference at runtime, and excluded from UI output, logs, prompts, diffs, and evidence. Rotation, revocation, expiration, access reviews, configuration schemas, overlays, validation, and drift detection are required.

## 15. Preview, deployment, and release

OCode shall detect ports and expose authenticated preview proxies, branch-specific preview environments, deployment adapters for static hosting, containers, Kubernetes, serverless, and approved clouds. Releases shall include semantic versions, changelogs, manifests, SBOM, provenance, signatures, attestations, progressive delivery, health checks, rollback, and environment promotion.

## 16. Identity, collaboration, and tenancy

Production mode requires OIDC or SAML, MFA and passkeys, service identities, secure sessions, organizations, teams, projects, workspaces, roles, fine-grained permissions, presence, comments, reviews, approvals, notifications, shared sessions, tenant isolation, quotas, billing dimensions, support-access controls, and managed organization policy.

## 17. Observability and operations

OCode shall emit structured logs, metrics, traces, health, readiness, and dependency status. Required operational views cover jobs, sandboxes, providers, deployments, costs, latency, errors, SLOs, and security. The platform shall include alerts, incidents, runbooks, backup, restore, disaster recovery, retention, export, deletion verification, capacity planning, and operational evidence.

## 18. Extensions, integrations, and mobile

Versioned extension and provider SDKs shall use capability manifests, permissions, signing, and isolated extension hosts. Integrations shall include source-control providers, issue trackers, chat, artifact registries, CI systems, cloud platforms, and enterprise connectors. Mobile shall support approvals, monitoring, diff review, evidence, task initiation, and rollback without becoming an unsafe unrestricted terminal.

## 19. Nonfunctional requirements

### Security
No unauthenticated production access; strong untrusted-code isolation; explicit network policy; no secret exposure; signed artifacts; SBOM and provenance; organization policy may narrow but not silently broaden access.

### Reliability
Initial control-plane availability target 99.9%; durable job state; idempotent state-changing APIs; documented RPO and RTO; no job may corrupt another workspace.

### Performance
Warm workspace shell under two seconds; ordinary file-open p95 under 300 ms; UI interaction p95 under 100 ms excluding remote work; output streaming begins within 500 ms of process output; search and indexing are incremental and cancellable.

### Scalability
Local single-user mode, remote team mode, and multi-tenant control plane with isolated execution planes, horizontal workers, quotas, budgets, and cost controls.

### Accessibility
WCAG 2.2 AA target, keyboard-complete navigation, screen-reader announcements, suitable mobile touch targets, reduced motion, and high contrast.

### Portability
Linux reference execution; Windows and macOS control surfaces with approved sandbox backends; reproducible container and Kubernetes deployment; provider-neutral AI contracts.

## 20. Required data classifications

Public, Internal, Confidential, Secret, and Regulated. Every entity declares retention, encryption, access, export, and deletion behavior.

## 21. Trust boundaries

User device; client; API edge; identity and authorization; control plane; repository storage; secrets service; scheduler; execution plane; deployment plane; telemetry and evidence; external providers and integrations.

## 22. Definition of full completion

OCode is not complete because interfaces exist. The platform target is achieved only when mandatory capabilities are implemented, tested, independently verifiable, deployable, operable, supportable, secure for their declared threat model, and evidenced against this specification.
