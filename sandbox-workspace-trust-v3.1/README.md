# Bite 1 — Sandbox and Workspace Trust — v3.1

Local-mode Linux sandbox and explicit workspace trust for OCode, per
`ocode-platform-spec/BITE_ROADMAP.md`. See `PLAN.md` for the bounded implementation
plan, scope boundary, verified primitives, risks, and rollback.

## What this is

A workspace must be explicitly marked trusted before any command can be run against
it inside the sandbox. A sandboxed run gets: new mount/UTS/IPC/PID/network
namespaces, workspace-only write access with the rest of the filesystem read-only,
OCode control-plane metadata hidden from the sandboxed view, an empty (deny-by-
default) network namespace, a cleared capability bounding set + `no_new_privs`, a
seccomp deny-list for dangerous syscalls, cgroup-enforced memory/PID/CPU limits, a
wall-clock timeout, and a structured, secret-scrubbed evidence record. Every
mandatory control fails closed: if it can't be established, the command does not run
unconfined.

## Install

```bash
pip install .
```

## CLI usage

```bash
# Explicitly trust a workspace (required once per workspace).
python -m ocode_sandbox trust /path/to/workspace --actor "your-name"

# Run a command inside the sandbox.
python -m ocode_sandbox run /path/to/workspace --timeout 30 -- <command...>
```

## Library usage

```python
from pathlib import Path
from ocode_sandbox import establish_trust, run_sandboxed

ws = Path("/path/to/workspace")
establish_trust(ws, actor="your-name")
result = run_sandboxed(ws, ["bash", "-c", "echo hello"], evidence_dir=ws / ".ocode" / "evidence")
print(result.exit_code, result.stdout)
```

## Tests and evidence

```bash
scripts/run_tests_and_evidence.sh
```

Runs the specification gate, a clean-environment install proof, the full adversarial
+ functional test suite (against the clean-installed package, not the working tree),
and a rollback proof, then writes
`evidence/OCODE_BITE01_SANDBOX_WORKSPACE_TRUST_EVIDENCE_MANIFEST.json`.

## Known gaps (see PLAN.md for detail)

- No user-namespace UID remapping (deferred to a hardening/multi-tenant bite).
- cgroup v1 legacy hierarchies are used on hosts that don't delegate cgroup v2
  memory/pids controllers (this development environment is one); v2 is supported
  when available but has not been independently verified on a v2-only host.
- Seccomp is a deny-list of known-dangerous syscalls, not a strict allow-list.
