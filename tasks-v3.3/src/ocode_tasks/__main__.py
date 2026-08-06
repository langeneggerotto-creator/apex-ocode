"""CLI: python -m ocode_tasks <start-daemon|submit|status|list|cancel|logs|shutdown>

Usage:
    python -m ocode_tasks start-daemon <workspace> [--concurrency N] [--evidence-dir DIR]
    python -m ocode_tasks submit <workspace> --task <name> [--timeout SECS]
    python -m ocode_tasks submit <workspace> --timeout SECS -- <command...>
    python -m ocode_tasks status <workspace> <job_id>
    python -m ocode_tasks list <workspace>
    python -m ocode_tasks cancel <workspace> <job_id>
    python -m ocode_tasks logs <workspace> <job_id>
    python -m ocode_tasks shutdown <workspace>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .client import JobClient
from .manifest import ManifestError, load as load_manifest

DEFAULT_SOCKET_NAME = "daemon.sock"


def _socket_path(workspace: Path) -> Path:
    return workspace / ".ocode" / "tasks" / DEFAULT_SOCKET_NAME


def _cmd_start_daemon(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    socket_path = _socket_path(workspace)
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else (workspace / ".ocode" / "evidence")

    daemon_args = {
        "workspace": str(workspace),
        "socket_path": str(socket_path),
        "concurrency": args.concurrency,
        "evidence_dir": str(evidence_dir),
    }

    subprocess.Popen(
        [sys.executable, "-m", "ocode_tasks._daemon_main", json.dumps(daemon_args)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(json.dumps({"socket_path": str(socket_path)}, indent=2))
    return 0


def _cmd_submit(args: argparse.Namespace, command: list[str]) -> int:
    workspace = Path(args.workspace).resolve()
    client = JobClient(_socket_path(workspace))

    task_name = args.task
    limits = None
    timeout_seconds = args.timeout

    if task_name:
        try:
            manifest = load_manifest(workspace)
            spec = manifest.get(task_name)
        except ManifestError as exc:
            print(f"manifest error: {exc}", file=sys.stderr)
            return 2
        command = spec.command
        if timeout_seconds is None:
            timeout_seconds = spec.timeout_seconds
        if spec.memory_bytes or spec.pids_max or spec.cpu_quota_percent:
            limits = {}
            if spec.memory_bytes:
                limits["memory_bytes"] = spec.memory_bytes
            if spec.pids_max:
                limits["pids_max"] = spec.pids_max
            if spec.cpu_quota_percent:
                limits["cpu_quota_percent"] = spec.cpu_quota_percent
    else:
        if not command:
            print("no command given (pass --task NAME or a command after a literal '--')", file=sys.stderr)
            return 2
        if timeout_seconds is None:
            timeout_seconds = 600

    job_id = client.submit(command, task_name=task_name, timeout_seconds=timeout_seconds, limits=limits)
    print(json.dumps({"job_id": job_id}, indent=2))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    client = JobClient(_socket_path(Path(args.workspace).resolve()))
    print(json.dumps(client.status(args.job_id), indent=2))
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    client = JobClient(_socket_path(Path(args.workspace).resolve()))
    print(json.dumps(client.list(), indent=2))
    return 0


def _cmd_cancel(args: argparse.Namespace) -> int:
    client = JobClient(_socket_path(Path(args.workspace).resolve()))
    ok = client.cancel(args.job_id)
    print(json.dumps({"cancelled": ok}, indent=2))
    return 0 if ok else 1


def _cmd_logs(args: argparse.Namespace) -> int:
    client = JobClient(_socket_path(Path(args.workspace).resolve()))
    data = client.logs(args.job_id)
    sys.stdout.buffer.write(data)
    return 0


def _cmd_shutdown(args: argparse.Namespace) -> int:
    client = JobClient(_socket_path(Path(args.workspace).resolve()))
    client.shutdown()
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    command: list[str] = []
    if argv and argv[0] == "submit" and "--" in argv:
        sep_index = argv.index("--")
        command = argv[sep_index + 1 :]
        argv = argv[:sep_index]

    parser = argparse.ArgumentParser(prog="python -m ocode_tasks")
    sub = parser.add_subparsers(dest="action", required=True)

    start_p = sub.add_parser("start-daemon")
    start_p.add_argument("workspace", type=Path)
    start_p.add_argument("--concurrency", type=int, default=2)
    start_p.add_argument("--evidence-dir", default=None)

    submit_p = sub.add_parser("submit")
    submit_p.add_argument("workspace", type=Path)
    submit_p.add_argument("--task", default=None)
    submit_p.add_argument("--timeout", type=int, default=None)

    for name in ("status", "cancel", "logs"):
        p = sub.add_parser(name)
        p.add_argument("workspace", type=Path)
        p.add_argument("job_id")

    list_p = sub.add_parser("list")
    list_p.add_argument("workspace", type=Path)

    shutdown_p = sub.add_parser("shutdown")
    shutdown_p.add_argument("workspace", type=Path)

    args = parser.parse_args(argv)

    dispatch = {
        "start-daemon": _cmd_start_daemon,
        "status": _cmd_status,
        "list": _cmd_list,
        "cancel": _cmd_cancel,
        "logs": _cmd_logs,
        "shutdown": _cmd_shutdown,
    }
    if args.action == "submit":
        return _cmd_submit(args, command)
    return dispatch[args.action](args)


if __name__ == "__main__":
    raise SystemExit(main())
