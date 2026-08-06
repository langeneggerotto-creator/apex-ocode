"""Sandbox orchestrator: explicit workspace trust -> cgroup resource limits ->
Linux namespaces -> private filesystem -> capability drop -> seccomp -> exec ->
timeout -> evidence -> deterministic cleanup.

Every step that can fail, fails closed: the sandboxed command is never started
unconfined, and the wall-clock timeout guarantees termination even if the target
command ignores signals inside its own namespace (SIGKILL on the outer `unshare`
process combined with ``--kill-child`` tears down the whole PID-namespace subtree).
"""

from __future__ import annotations

import dataclasses
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .cgroups import CgroupSandbox, ResourceLimits
from .evidence import EvidenceRecord, cap_and_scrub, new_run_id, write_evidence
from .fs_isolation import build_mount_script
from .seccomp_policy import DENIED_SYSCALLS, seccomp_available
from .trust import verify_trust

DEFAULT_TIMEOUT_SECONDS = 30


class WorkspaceNotTrustedError(RuntimeError):
    """Raised when run_sandboxed is called against a workspace with no valid,
    intact trust marker. Fail closed: there is no unattended trust fallback."""


class SandboxSetupError(RuntimeError):
    """Raised when a mandatory isolation control cannot be established. The run is
    never started unconfined in this case."""


@dataclasses.dataclass
class SandboxResult:
    run_id: str
    exit_code: Optional[int]
    timed_out: bool
    stdout: str
    stderr: str
    controls_applied: Dict[str, Any]
    resource_usage: Dict[str, Any]
    evidence_path: Optional[str]


def run_sandboxed(
    workspace_dir: Path,
    command: Sequence[str],
    *,
    protected_paths: Optional[Sequence[Path]] = None,
    limits: Optional[ResourceLimits] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    evidence_dir: Optional[Path] = None,
) -> SandboxResult:
    workspace_dir = Path(workspace_dir).resolve()

    trust_record = verify_trust(workspace_dir)
    if trust_record is None:
        raise WorkspaceNotTrustedError(
            f"workspace is not trusted (no valid trust marker): {workspace_dir}"
        )

    if not seccomp_available():
        raise SandboxSetupError(
            "seccomp (pyseccomp/libseccomp) unavailable; refusing to start an "
            "unconfined sandbox"
        )

    limits = limits or ResourceLimits()
    protected = list(protected_paths or [])
    protected.append(workspace_dir / ".ocode")

    run_id = new_run_id()

    exec_helper_argv = [sys.executable, "-m", "ocode_sandbox._exec_helper", json.dumps(list(command))]
    setpriv_argv = [
        "setpriv",
        "--inh-caps=-all",
        "--bounding-set=-all",
        "--no-new-privs",
        "--",
        *exec_helper_argv,
    ]

    controls_applied: Dict[str, Any] = {
        "workspace_trust": {
            "actor": trust_record.actor,
            "established_at": trust_record.established_at,
        },
        "namespaces": ["mount", "uts", "ipc", "pid", "net"],
        "network_deny_by_default": True,
        "filesystem": {
            "workspace_writable": str(workspace_dir),
            "root_read_only": True,
            "protected_paths_hidden": [str(p) for p in protected],
        },
        "capabilities_dropped": "bounding-set=-all, inheritable=-all, no_new_privs",
        "seccomp_denied_syscalls": list(DENIED_SYSCALLS),
        "cgroup_mode": None,
    }

    started_at = time.time()
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code: Optional[int] = None
    usage: Dict[str, Any] = {}

    with CgroupSandbox(limits, name=f"ocode-sandbox-{run_id}") as cg:
        controls_applied["cgroup_mode"] = cg.mode
        controls_applied["resource_limits"] = dataclasses.asdict(limits)

        mount_script = build_mount_script(workspace_dir, protected, cg.procs_paths())
        inner_script = mount_script + "exec " + " ".join(shlex.quote(part) for part in setpriv_argv) + "\n"
        outer_argv = [
            "unshare",
            "--mount",
            "--uts",
            "--ipc",
            "--pid",
            "--net",
            "--fork",
            "--mount-proc",
            "--kill-child=SIGKILL",
            "--",
            "bash",
            "-c",
            inner_script,
        ]

        proc = subprocess.Popen(
            outer_argv,
            cwd=str(workspace_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
            exit_code = proc.returncode

        usage = cg.usage()

    finished_at = time.time()

    record = EvidenceRecord(
        schema_version="ocode.sandbox-run-evidence.v1",
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        workspace=str(workspace_dir),
        command=list(command),
        controls_applied=controls_applied,
        exit_code=exit_code,
        timed_out=timed_out,
        resource_usage=usage,
        stdout=cap_and_scrub(stdout),
        stderr=cap_and_scrub(stderr),
    )

    evidence_path: Optional[str] = None
    if evidence_dir is not None:
        evidence_path = str(write_evidence(record, Path(evidence_dir)))

    return SandboxResult(
        run_id=run_id,
        exit_code=exit_code,
        timed_out=timed_out,
        stdout=record.stdout,
        stderr=record.stderr,
        controls_applied=controls_applied,
        resource_usage=usage,
        evidence_path=evidence_path,
    )
