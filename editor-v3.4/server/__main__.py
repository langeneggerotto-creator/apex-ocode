"""CLI: python -m server <workspace> [--port N] [--frontend-dir DIR]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .httpserver import serve

DEFAULT_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m server")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--frontend-dir", type=Path, default=DEFAULT_FRONTEND_DIR)
    args = parser.parse_args(argv)

    httpd = serve(args.workspace, args.frontend_dir, host=args.host, port=args.port)
    host, port = httpd.server_address
    print(f"http://{host}:{port}")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
