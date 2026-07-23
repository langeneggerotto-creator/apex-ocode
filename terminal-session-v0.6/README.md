# OCODE v0.6 — Persistent Governed Terminal Session Kernel

Truth status: `IMPLEMENTED_AND_LOCALLY_TESTED__STATE_KERNEL_ONLY__NO_PROCESS_OR_PTY_EXECUTION`

This is the next deliberately small OCODE increment. It adds the durable state and policy boundary needed before attaching a real integrated terminal.

## Included

- Workspace-confined terminal working directories.
- Allowlisted shells and executables.
- Denial of shell control syntax in this bounded command-admission layer.
- Persistent terminal session lifecycle: create, reload, append transcript, close.
- Atomic JSON state writes.
- Hash-linked evidence events for every session transition.
- Deterministic Node test suite.

## Explicitly excluded

- No subprocess execution.
- No PTY allocation.
- No WebSocket streaming.
- No browser terminal component.
- No container or VM provisioning.
- No claim of OS-level isolation.
- No production security or multi-user readiness.

## Verify

```bash
cd terminal-session-v0.6
npm run verify
```

## Promotion gate

This bite passes only when all tests prove:

1. sessions survive reload;
2. workspace escape attempts are denied;
3. non-allowlisted and compound shell commands are denied;
4. transcript state persists;
5. closed sessions cannot mutate;
6. the evidence hash chain verifies.

## Next bite

Attach one bounded, allowlisted process runner to this kernel with timeout, output limits, cancellation, and zero network privileges by default. Do not add the Studio UI in the same increment.
