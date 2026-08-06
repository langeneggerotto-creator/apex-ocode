"""Internal entrypoint: ``python3 -m ocode_tasks._daemon_main '<json args>'``.

Started via ``subprocess.Popen(..., start_new_session=True)`` from the CLI's
``start-daemon`` command so the job manager survives the CLI process exiting, the
same pattern as Bite 2's ``_daemon_main.py``. Not a public API.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .daemon import JobDaemon


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: _daemon_main '<json args>'", file=sys.stderr)
        return 2
    args = json.loads(sys.argv[1])

    daemon = JobDaemon(
        workspace=Path(args["workspace"]),
        socket_path=Path(args["socket_path"]),
        concurrency=args.get("concurrency", 2),
        evidence_dir=Path(args["evidence_dir"]) if args.get("evidence_dir") else None,
    )
    return daemon.run()


if __name__ == "__main__":
    raise SystemExit(main())
