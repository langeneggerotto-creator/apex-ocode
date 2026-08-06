"""Internal helper: runs as the final process before the sandboxed command.

Invoked as ``python3 -m ocode_sandbox._exec_helper '<json argv>'`` from inside
``setpriv`` (after capabilities and no_new_privs have already been applied), so this
process only needs to load the seccomp filter and exec into the real command. Not a
public API.
"""

from __future__ import annotations

import json
import sys

from .seccomp_policy import apply_and_exec


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: _exec_helper '<json-encoded argv list>'", file=sys.stderr)
        raise SystemExit(2)
    argv = json.loads(sys.argv[1])
    apply_and_exec(argv)


if __name__ == "__main__":
    main()
