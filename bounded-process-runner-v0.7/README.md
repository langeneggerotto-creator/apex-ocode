# OCODE v0.7 — Bounded Linux Process Runner

Truth status: `IMPLEMENTED_AND_LOCALLY_VERIFIED__LINUX_NAMESPACE_SANDBOX__NO_STUDIO_UI__NOT_PRODUCTION_READY`

This stacked bite attaches one real process runner to the v0.6 terminal-session kernel. It remains intentionally narrow and does not add the OCODE Studio interface.

## What this bite implements

- Direct process spawning with `shell: false`.
- Existing v0.6 command admission before execution.
- Physical and logical workspace working-directory confinement.
- A Linux sandbox composed of:
  - user namespace;
  - mount namespace;
  - PID namespace;
  - network namespace;
  - `chroot` filesystem boundary;
  - read-only `/usr` and `/opt` toolchains;
  - read-write `/workspace` only;
  - private in-memory `/tmp`;
  - minimal `/etc` and `/dev/null`.
- Networking denied for every v0.7 execution. Network inheritance requests fail before spawn.
- Timeout enforcement with process-group termination and forced-kill fallback.
- AbortSignal cancellation.
- Combined stdout/stderr byte limits with truncation and termination.
- Structured execution results and transcript evidence written through the v0.6 session store.
- Fail-closed behavior when the Linux namespace sandbox cannot be established.

## Verification

```bash
cd bounded-process-runner-v0.7
npm run verify
```

The deterministic test suite proves:

1. an allowlisted Node process executes and writes inside the workspace;
2. network inheritance is denied by policy;
3. external network access fails inside the network namespace;
4. an absolute host file outside the workspace is unreadable inside the chroot;
5. a working-directory symlink escape is rejected before spawn;
6. timeout termination works;
7. AbortSignal cancellation works;
8. the combined output limit terminates noisy processes at the configured cap;
9. a non-allowlisted executable returns `POLICY_DENIED` without spawning.

## Required host capability

This bite is Linux-only and requires unprivileged user, mount, PID, and network namespaces plus `mount`, `chroot`, `/usr`, and `/opt`. If those capabilities are missing or disabled, execution returns `SANDBOX_UNAVAILABLE`; it does not silently fall back to an unconfined process.

## Explicit exclusions

- No PTY or interactive shell.
- No WebSocket or streaming transport.
- No Studio interface.
- No Windows or macOS sandbox backend.
- No network-enabled execution mode.
- No package installation or image pulling.
- No cgroup CPU or memory limits yet.
- No seccomp profile yet.
- No multi-user authorization boundary.
- No production-readiness or universal OS-sandbox claim.

## Stop condition

Stop after one non-interactive, allowlisted process can execute with verified timeout, cancellation, output, workspace, and network boundaries. Do not add PTY support, the Studio UI, containers, deployment, or remote execution in this increment.

## Next independent bite

Add bounded CPU and memory enforcement using one explicit Linux cgroup-v2 backend with fail-closed capability detection and evidence. Keep PTY and Studio UI work separate.
