# OCode Security, Deployment, and Operations Contract

## Threat model

Protected assets include source code, intellectual property, credentials, secrets, user and tenant data, build artifacts, evidence, deployment environments, prompts, provider credentials, and platform control infrastructure.

Principal threats include malicious repositories, prompt injection, sandbox escape, cross-tenant access, secret exfiltration, dependency compromise, unsafe Git configuration, malicious extensions, privilege escalation, resource exhaustion, evidence tampering, unauthorized deployment, insider misuse, and account takeover.

## Security requirements

- Explicit workspace trust
- Least privilege and deny-by-default policy
- Strong untrusted execution isolation
- Network egress controls
- Secret references rather than raw values
- Tenant-aware authorization at every service boundary
- Signed dependencies, SBOM, provenance, and artifact verification
- Immutable audit and evidence
- Quotas, budgets, rate limits, timeouts, and cancellation
- MFA for privileged roles
- OIDC and SAML enterprise identity
- Short-lived tokens and service identities
- TLS externally and appropriate service-to-service authentication
- Encryption at rest with managed keys
- Central authorization decisions and recorded outcomes
- No direct sandbox access to control-plane networks
- Scanning of source, dependencies, containers, infrastructure, licenses, and secrets

## Release-blocking security failures

- Known sandbox escape
- Cross-tenant authorization failure
- Secret found in logs, prompts, diffs, output, or evidence
- Unsigned production artifact
- Destructive migration without demonstrated backup and rollback
- Unreviewed critical dependency vulnerability
- Ability to bypass workspace trust or release approval

## Deployment modes

### Local mode
Single-user control plane, local repository storage, browser Studio, CLI, and Linux sandbox worker.

### Team mode
Containerized services with managed PostgreSQL, cache, object storage, secrets and key management, execution workers, and authenticated preview proxy.

### Enterprise mode
Kubernetes across separate control, data, and execution node pools. Network policy isolates workers. Higher-assurance tenants may receive dedicated workers, databases, keys, or clusters.

## Environments

Local, development, integration, staging, production, and disaster recovery.

## Initial SLOs

- Control-plane availability: 99.9%
- API p95: under 500 ms excluding long operations
- Job scheduling p95: under two seconds
- Terminal output delivery p95: under 500 ms after process emission
- Production deployment success: above 99.5%
- Restore drill success: 100%

## Mandatory runbooks

Authentication outage, database degradation, queue backlog, sandbox compromise, secret exposure, provider outage, preview failure, deployment rollback, evidence integrity failure, tenant export and deletion, backup restore, and regional recovery.

## Production release gates

Infrastructure reviewed; migrations tested forward and backward; canary or blue-green plan; health and readiness probes; backup and restore drill; rollback tested; alerts and dashboards active; signed release and evidence manifest verified.
