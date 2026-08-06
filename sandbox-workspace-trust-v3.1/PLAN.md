# Bite 1 — Sandbox and Workspace Trust — v3.1 — Implementation Plan

Status at plan time: no prior bite implementation exists in this repository. This is the
first eligible incomplete bite per `ocode-platform-spec/BITE_ROADMAP.md`, and is a
required security foundation, so predecessor-seal checks are satisfied trivially
(there is no predecessor).

## Scope boundary

This bite implements the **Local mode** sandbox worker described in
`ocode-platform-spec/SECURITY_DEPLOYMENT.md` ("Local mode: single-user control plane,
local repository storage, browser Studio, CLI, and Linux sandbox worker") and the
Linux isolation model in `FULL_PLATFORM_SPEC.md` §13.

In scope:
- Explicit workspace trust (a workspace must be explicitly marked trusted before any
  sandboxed command runs against it; untrusted or missing trust state fails closed).
- Linux OS-level sandbox for running a single command against a trusted workspace:
  mount, UTS, IPC, PID, and network namespaces; a private filesystem view where only
  the workspace is writable and everything else is read-only; OCode control-plane
  metadata hidden from the sandboxed view; deny-by-default network egress; capability
  bounding-set drop and `no_new_privs`; a seccomp deny-list for dangerous syscalls;
  cgroup-enforced memory, PID-count, and CPU limits; a wall-clock timeout; and
  deterministic runtime cleanup.
- Adversarial isolation tests proving each control actually holds, plus a positive
  functional test proving legitimate work still succeeds.
- Executable evidence (structured JSON receipts + captured test output) for every
  claimed control.

Out of scope for this bite (explicitly deferred, to respect "do not implement
later-bite capabilities except the minimum interfaces required"):
- User-namespace UID remapping / rootless remapping and multi-tenant, container, or
  microVM execution tiers (Bite 13, "Multi-tenant production hardening").
- Persistent PTY sessions, terminal streaming, reconnect (Bite 2).
- Declarative task runner, job queue states (Bite 3).
- Any control-plane API, auth, or UI surface (later bites / Bite 10).
- Dev Containers / Dockerfiles / Nix environment profiles (Bite 8).

## Target environment and honest constraints

This plan is implemented and evidenced inside the current development container,
which is itself a nested, already-sandboxed Linux environment (root inside a
Firecracker-style VM). Primitive-by-primitive validation was performed before writing
production code:

| Control | Primitive | Verified in this environment |
|---|---|---|
| Namespaces | `unshare --mount --uts --ipc --pid --net --fork --mount-proc` | Yes |
| Network deny-by-default | empty net namespace (no interfaces except loopback) | Yes — `curl` returns "Network unreachable" |
| Private filesystem / workspace-only write | `mount --make-rprivate /`, then bind-mount the workspace **before** bind+remounting `/` read-only (ordering is load-bearing — binding the workspace after the read-only remount inherits read-only) | Yes |
| Protected metadata hidden | empty-mode `tmpfs` bind over the protected path | Yes — listing and reading both fail |
| Capability drop + no_new_privs | `setpriv --inh-caps=-all --bounding-set=-all --no-new-privs` | Yes — `mount` and `unshare` inside the dropped shell both fail with `EPERM`/`Operation not permitted` even though the process is still uid 0 |
| Resource limits | cgroup **v1** legacy hierarchies (`memory`, `pids`) | Yes — a 500 MB allocation under a 10 MB `memory.limit_in_bytes` is SIGKILLed (exit 137); fork-bombing under `pids.max=5` fails with `Resource temporarily unavailable` |
| Seccomp deny-list | `pyseccomp` (ctypes binding to the already-installed `libseccomp.so.2`) | Yes — a filter denying `ptrace` causes `ptrace()` to return `EPERM` |

Known environment gap: cgroup v2 (`/sys/fs/cgroup/unified`) is mounted but only
delegates the `hugetlb` controller in this container, so `memory`/`pids`/`cpu`
controllers are not available there. The implementation therefore targets cgroup v1
legacy hierarchies, which are fully delegated and enforce correctly here. The runner
detects at runtime whether v1 legacy or v2 unified controllers are writable and uses
whichever is available; if neither is writable, resource limiting fails closed (the
run is refused rather than started unconfined).

User-namespace uid remapping was evaluated and intentionally deferred: since the
capability bounding set is fully cleared and `no_new_privs` is set, a uid-0 process
inside the sandbox cannot `mount`, `unshare`, `ptrace`, or otherwise re-escalate even
though its uid is still 0 — the filesystem permission model still applies normally to
uid 0 once `CAP_DAC_OVERRIDE`/`CAP_DAC_READ_SEARCH` are dropped, so this does not
weaken the workspace-only-write guarantee. This is recorded as a residual risk below.

## Files

```
sandbox-workspace-trust-v3.1/
  PLAN.md                          (this file)
  README.md                        (usage + control summary)
  requirements.txt                 (pyseccomp)
  pyproject.toml                   (packaging)
  src/ocode_sandbox/
    __init__.py
    trust.py                       (workspace trust marker: establish / verify / revoke)
    cgroups.py                     (cgroup v1/v2 resource-limit group lifecycle)
    seccomp_policy.py              (deny-list syscall filter, fail-closed if unavailable)
    fs_isolation.py                (inner mount-setup script generator)
    runner.py                      (orchestrator: trust check -> cgroup -> unshare -> fs
                                     isolation -> capability drop -> seccomp -> exec ->
                                     timeout -> evidence -> cleanup)
    evidence.py                    (structured evidence record writer, secret-scrubbing)
    __main__.py                    (`python -m ocode_sandbox` CLI)
  tests/
    test_trust.py                  (unit: trust marker lifecycle, fail-closed default)
    test_isolation.py              (adversarial + functional, requires Linux root; each
                                     test is individually skipped with a clear reason if
                                     an underlying primitive is unavailable, never
                                     silently downgraded to "pass")
  scripts/
    run_tests_and_evidence.sh      (baseline + test run -> evidence manifest)
    install_clean_env.sh           (fresh-venv install proof)
    rollback_demo.sh               (uninstall / revert proof)
  evidence/                        (generated JSON + captured logs; gitignored raw logs,
                                     committed manifest)
```

## Contracts

- `establish_trust(workspace_dir, actor) -> TrustRecord` / `verify_trust(workspace_dir) -> TrustRecord | None`
  writes/reads `<workspace>/.ocode/trust.json` with an explicit `trusted: true`,
  timestamp, actor, and content hash of the trust file itself (tamper-evident, not
  tamper-proof — full signing is a later-bite identity concern).
- `run_sandboxed(workspace_dir, command, *, protected_paths, limits, timeout_seconds) -> SandboxResult`
  refuses to run (raises `WorkspaceNotTrustedError`) unless `verify_trust` succeeds.
  Returns exit code, stdout/stderr (size-capped), timing, resource usage, and the exact
  list of controls that were applied — never a boolean "safe" claim.
- All internal failures (seccomp unavailable, no writable cgroup controller, mount
  setup step fails) raise and abort the run. There is no fallback to an unconfined
  execution path.

## Risks

- **Nested-container evidence generalization**: primitives were proven inside this
  dev container, not on a bare-metal / typical end-user Linux host. Behavior should be
  equivalent (same kernel mechanisms) but has not been independently verified outside
  this environment. Recorded as a residual risk, not silently assumed away.
- **cgroup v1 deprecation**: legacy v1 hierarchies still work broadly today but are
  being phased out upstream; the runner's controller-detection code isolates this
  dependency so a future bite can add v2-only hosts without touching call sites.
- **No UID remapping**: covered above; mitigated by capability/no_new_privs, not by
  uid separation.
- **Seccomp deny-list vs allow-list**: a deny-list of known-dangerous syscalls is used
  rather than a strict allow-list, to keep ordinary interpreters/toolchains working
  inside the sandbox without a bespoke per-language allow-list. This is weaker than an
  allow-list in principle; capability dropping and namespace isolation provide the
  primary boundary, seccomp is defense-in-depth. Documented, not hidden.

## Tests

Unit: trust marker establish/verify/revoke, fail-closed on missing/invalid marker.

Adversarial isolation (each proves a specific control, run against the packaged
runner, not a shortcut):
1. Network egress denied by default.
2. Filesystem write outside the workspace denied.
3. Protected OCode metadata unreadable from inside the sandbox.
4. Memory limit enforced (over-limit allocation is killed).
5. PID/process-count limit enforced (fork bomb blocked).
6. Privilege escalation blocked (`mount`, `unshare`, `ptrace` all denied from inside).
7. Untrusted workspace refused (no trust marker -> sandbox does not start).

Functional (positive path): a trusted workspace can run an ordinary command, write a
file inside the workspace, and read it back successfully.

## Evidence

`scripts/run_tests_and_evidence.sh` runs the full suite and writes
`evidence/OCODE_BITE01_SANDBOX_WORKSPACE_TRUST_EVIDENCE_MANIFEST.json` containing: gate
result, test pass/fail per adversarial control, install proof, rollback proof, and the
truth label this evidence supports.

## Rollback

Because there is no prior capability to protect, rollback is demonstrated rather than
required for safety: `scripts/rollback_demo.sh` performs a clean `pip uninstall`
(proving the packaged artifact is fully removable) and documents that `git revert
<bite-1-commit>` cleanly removes the bite's files with no other part of the repository
depending on them (new, additive directory only).

## Truth label target

`LOCALLY_VERIFIED` — implemented, executed, and tested with evidence captured inside
this development environment. Not `PRODUCTION_DEPLOYED` or `OPERATIONALLY_PROVEN`
(no deployment target exists yet), and not claimed as such.

## Next eligible bite (not started)

Bite 2 — Persistent integrated terminal — v3.2.
