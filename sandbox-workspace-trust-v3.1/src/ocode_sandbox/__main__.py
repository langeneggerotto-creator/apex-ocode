"""CLI entrypoint: python -m ocode_sandbox <trust|run> ...

Usage:
    python -m ocode_sandbox trust <workspace> --actor <name>
    python -m ocode_sandbox run <workspace> [--timeout SECONDS] [--evidence-dir DIR] -- <command...>
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from .runner import SandboxSetupError, WorkspaceNotTrustedError, run_sandboxed
from .trust import establish_trust


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Split out the literal command to run *before* argparse sees it. A REMAINDER
    # positional would swallow flags (like --timeout) that appear after it, so the
    # split has to happen ourselves: everything after the first bare "--" is the
    # command, verbatim, and never touches the argparse grammar.
    command: list[str] = []
    if "run" in argv:
        try:
            sep_index = argv.index("--")
            command = argv[sep_index + 1 :]
            argv = argv[:sep_index]
        except ValueError:
            command = []

    parser = argparse.ArgumentParser(prog="python -m ocode_sandbox")
    sub = parser.add_subparsers(dest="action", required=True)

    trust_parser = sub.add_parser("trust", help="establish explicit workspace trust")
    trust_parser.add_argument("workspace", type=Path)
    trust_parser.add_argument("--actor", required=True)

    run_parser = sub.add_parser("run", help="run a command inside the sandbox")
    run_parser.add_argument("workspace", type=Path)
    run_parser.add_argument("--timeout", type=int, default=30)
    run_parser.add_argument("--evidence-dir", type=Path, default=None)

    args = parser.parse_args(argv)

    if args.action == "trust":
        record = establish_trust(args.workspace, args.actor)
        print(json.dumps(record.to_dict(), indent=2))
        return 0

    if args.action == "run":
        if not command:
            print("no command given (pass it after a literal '--')", file=sys.stderr)
            return 2
        try:
            result = run_sandboxed(
                args.workspace,
                command,
                timeout_seconds=args.timeout,
                evidence_dir=args.evidence_dir,
            )
        except (WorkspaceNotTrustedError, SandboxSetupError) as exc:
            print(f"sandbox refused to run: {exc}", file=sys.stderr)
            return 1

        print(json.dumps(dataclasses.asdict(result), indent=2))
        return result.exit_code if result.exit_code is not None else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
