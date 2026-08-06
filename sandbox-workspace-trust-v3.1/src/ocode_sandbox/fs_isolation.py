"""Private filesystem view: workspace-only write access, everything else read-only,
OCode control-plane metadata hidden, and self-assignment into the pre-created
resource-limit cgroup.

Generates a shell script that runs *inside* an already-unshared mount+PID namespace
(``unshare --mount --pid ... --fork``) and must run before any privilege-dropping
step, because it needs the mount capabilities the sandboxed command itself will not
retain afterwards.

Ordering is load-bearing and was verified empirically in the reference environment:

1. ``mount --make-rprivate /`` — stop mount events from propagating back to the host
   mount namespace before anything else happens.
2. ``mount --rbind / /`` — a *recursive* bind of the whole mount tree. A plain
   (non-recursive) ``--bind`` only captures the top-level ``/`` entry and silently
   drops every separately-mounted submount (``/sys/fs/cgroup/*``, ``/dev/pts``, ...)
   from the new namespace's view, which both breaks tooling that lives under those
   submounts and — more importantly — leaves cgroup, ``/proc``, and ``/dev`` mounted
   read-write with none of the isolation below applying to them.
3. Bind-mount the workspace onto itself, making it its own mount point, **before**
   anything is remounted read-only. A bind mount created after an ancestor is
   remounted read-only inherits read-only; created before, it does not.
4. Hide protected paths by bind-mounting an empty, mode-000 tmpfs (directories) or
   ``/dev/null`` (files) over each one.
5. Self-assign the current shell (the new PID namespace's PID 1) into each cgroup
   controller's ``cgroup.procs`` *before* anything is made read-only, and *from
   inside* the sandboxed process tree rather than from the trusted orchestrator
   process externally — an external, post-hoc ``cgroup.procs`` write races against
   ``unshare --fork``'s internal fork and can attach the wrong process, leaving the
   actual workload unlimited. Every descendant (setpriv, the seccomp-exec helper,
   the target command) inherits this cgroup membership through fork, which is
   unaffected by namespaces.
6. Walk ``/proc/self/mountinfo`` and remount every mount point read-only, deepest
   first, except the workspace subtree — this is the step that actually enforces
   "workspace-only write access" for the submounts captured by the recursive bind
   (``/proc``, ``/sys``, ``/dev``, cgroup controllers, ...), not just the top-level
   root entry.
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Iterable, List


def build_mount_script(
    workspace: Path,
    protected_paths: Iterable[Path],
    cgroup_procs_paths: Iterable[Path] = (),
) -> str:
    workspace = workspace.resolve()
    protected = [p.resolve() for p in protected_paths]
    cgroup_procs = [str(p) for p in cgroup_procs_paths]

    lines: List[str] = [
        "set -e",
        "mount --make-rprivate /",
        "mount --rbind / /",
        f"mkdir -p {shlex.quote(str(workspace))}",
        f"mount --bind {shlex.quote(str(workspace))} {shlex.quote(str(workspace))}",
    ]

    for p in protected:
        lines.append(f"if [ -e {shlex.quote(str(p))} ]; then")
        lines.append(f"  if [ -d {shlex.quote(str(p))} ]; then")
        lines.append(f"    mount -t tmpfs -o size=0,mode=000 tmpfs {shlex.quote(str(p))}")
        lines.append("  else")
        lines.append(f"    mount --bind /dev/null {shlex.quote(str(p))}")
        lines.append("  fi")
        lines.append("fi")

    for procs_path in cgroup_procs:
        lines.append(f"echo $$ > {shlex.quote(procs_path)}")

    # Recursively remount everything read-only except the workspace subtree.
    # Deepest-first ordering (sort -r on the path column) avoids a shallow read-only
    # remount interfering with a deeper mount point's own remount right after it.
    lines.append(f'__OCODE_WORKSPACE={shlex.quote(str(workspace))}')
    lines.append(
        'awk \'{print $5}\' /proc/self/mountinfo | sort -r | while read -r mp; do\n'
        '  case "$mp" in\n'
        '    "$__OCODE_WORKSPACE"|"$__OCODE_WORKSPACE"/*) continue ;;\n'
        '  esac\n'
        '  mount -o remount,bind,ro "$mp" 2>/dev/null || true\n'
        'done'
    )

    return "\n".join(lines) + "\n"
