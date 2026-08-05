"""Path confinement -- required by spec section 16 ("confine file access to
the project workspace", "validate all file paths", "reject path
traversal"). Every filesystem path this application touches on behalf of a
project must be resolved through confine_path() before use. Nothing else
in core/ or storage/ constructs a filesystem path from user input directly.
"""
from __future__ import annotations

from pathlib import Path

from .errors import PathConfinementError


def confine_path(root: Path, relative: str) -> Path:
    """Resolve `relative` against `root` and return the resolved, absolute
    path -- only if it stays inside root. Catches both literal traversal
    (`../../etc/passwd`) and symlink escapes (resolve() follows symlinks,
    so a symlink pointing outside root is caught the same way literal
    traversal is). Raises PathConfinementError otherwise; never silently
    clamps or truncates a path back inside the root, since that could
    silently redirect a caller to the wrong file."""
    root_resolved = root.resolve()
    if not root_resolved.is_dir():
        raise PathConfinementError(relative, str(root))

    candidate = (root_resolved / relative).resolve()

    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        raise PathConfinementError(relative, str(root_resolved)) from None

    return candidate
