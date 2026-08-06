"""CLI: python -m ocode_terminal <start|attach|send|resize|status|stop> ...

Usage:
    python -m ocode_terminal start <workspace> --run-id ID [--evidence-dir DIR]
        [--idle-timeout SECS] [--max-duration SECS] -- <command...>
    python -m ocode_terminal status <socket_path>
    python -m ocode_terminal resize <socket_path> <cols> <rows>
    python -m ocode_terminal send <socket_path> <text>
    python -m ocode_terminal stop <socket_path> [--force]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .client import TerminalClient


def _cmd_start(args: argparse.Namespace, command: list[str]) -> int:
    if not command:
        print("no command given (pass it after a literal '--')", file=sys.stderr)
        return 2

    workspace = Path(args.workspace).resolve()
    socket_path = workspace / ".ocode" / "terminal" / f"{args.run_id}.sock"
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else (workspace / ".ocode" / "evidence")

    daemon_args = {
        "workspace": str(workspace),
        "command": command,
        "socket_path": str(socket_path),
        "run_id": args.run_id,
        "evidence_dir": str(evidence_dir),
        "cols": args.cols,
        "rows": args.rows,
        "idle_timeout_seconds": args.idle_timeout,
        "max_duration_seconds": args.max_duration,
    }

    subprocess.Popen(
        [sys.executable, "-m", "ocode_terminal._daemon_main", json.dumps(daemon_args)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(json.dumps({"run_id": args.run_id, "socket_path": str(socket_path)}, indent=2))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    client = TerminalClient(Path(args.socket_path))
    print(json.dumps(client.status(), indent=2))
    client.close()
    return 0


def _cmd_resize(args: argparse.Namespace) -> int:
    client = TerminalClient(Path(args.socket_path))
    print(json.dumps(client.resize(args.cols, args.rows), indent=2))
    client.close()
    return 0


def _cmd_send(args: argparse.Namespace) -> int:
    client = TerminalClient(Path(args.socket_path))
    client.send_input((args.text + "\n").encode("utf-8"))
    client.close()
    return 0


def _cmd_stop(args: argparse.Namespace) -> int:
    client = TerminalClient(Path(args.socket_path))
    print(json.dumps(client.stop(force=args.force), indent=2))
    client.close()
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    command: list[str] = []
    if argv and argv[0] == "start" and "--" in argv:
        sep_index = argv.index("--")
        command = argv[sep_index + 1 :]
        argv = argv[:sep_index]

    parser = argparse.ArgumentParser(prog="python -m ocode_terminal")
    sub = parser.add_subparsers(dest="action", required=True)

    start_p = sub.add_parser("start")
    start_p.add_argument("workspace", type=Path)
    start_p.add_argument("--run-id", required=True)
    start_p.add_argument("--evidence-dir", default=None)
    start_p.add_argument("--cols", type=int, default=80)
    start_p.add_argument("--rows", type=int, default=24)
    start_p.add_argument("--idle-timeout", type=float, default=15 * 60)
    start_p.add_argument("--max-duration", type=float, default=8 * 60 * 60)

    status_p = sub.add_parser("status")
    status_p.add_argument("socket_path")

    resize_p = sub.add_parser("resize")
    resize_p.add_argument("socket_path")
    resize_p.add_argument("cols", type=int)
    resize_p.add_argument("rows", type=int)

    send_p = sub.add_parser("send")
    send_p.add_argument("socket_path")
    send_p.add_argument("text")

    stop_p = sub.add_parser("stop")
    stop_p.add_argument("socket_path")
    stop_p.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)

    if args.action == "start":
        return _cmd_start(args, command)
    if args.action == "status":
        return _cmd_status(args)
    if args.action == "resize":
        return _cmd_resize(args)
    if args.action == "send":
        return _cmd_send(args)
    if args.action == "stop":
        return _cmd_stop(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
