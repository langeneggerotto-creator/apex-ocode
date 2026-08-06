"""Internal entrypoint: ``python3 -m ocode_terminal._daemon_main '<json args>'``.

Started via ``subprocess.Popen(..., start_new_session=True)`` from the CLI's
``start`` command so the daemon (and the session it owns) survives the CLI process
exiting. Not a public API.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ocode_sandbox.cgroups import ResourceLimits

from .daemon import SessionDaemon


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: _daemon_main '<json args>'", file=sys.stderr)
        return 2
    args = json.loads(sys.argv[1])

    limits = ResourceLimits(**args["limits"]) if args.get("limits") else None

    daemon = SessionDaemon(
        workspace_dir=Path(args["workspace"]),
        command=args["command"],
        socket_path=Path(args["socket_path"]),
        run_id=args["run_id"],
        evidence_dir=Path(args["evidence_dir"]) if args.get("evidence_dir") else None,
        limits=limits,
        cols=args.get("cols", 80),
        rows=args.get("rows", 24),
        idle_timeout_seconds=args.get("idle_timeout_seconds", 15 * 60),
        max_duration_seconds=args.get("max_duration_seconds", 8 * 60 * 60),
        grace_seconds=args.get("grace_seconds", 5.0),
    )
    return daemon.run()


if __name__ == "__main__":
    raise SystemExit(main())
