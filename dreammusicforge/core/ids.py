"""Identifier generation and validation for kernel entities.

Every id in this application follows PREFIX-TOKEN, where TOKEN is 8
lowercase hex characters from `secrets.token_hex` -- unique per call
(not content-derived; that's what core/hashing.py is for), but formatted
deterministically and checkably so a malformed id is always caught rather
than accepted and causing confusing failures downstream."""
from __future__ import annotations

import re
import secrets

from .errors import InvalidProjectIdError

PROJECT_ID_PREFIX = "DMF-PROJECT-"
PROJECT_ID_PATTERN = re.compile(rf"^{re.escape(PROJECT_ID_PREFIX)}[0-9a-f]{{8}}$")


def generate_project_id() -> str:
    return f"{PROJECT_ID_PREFIX}{secrets.token_hex(4)}"


def validate_project_id(project_id: str) -> None:
    """Raises InvalidProjectIdError if project_id doesn't match the
    required format. Returns None (not a bool) so callers can't
    accidentally ignore a False result -- fail closed."""
    if not isinstance(project_id, str) or not PROJECT_ID_PATTERN.match(project_id):
        raise InvalidProjectIdError(project_id if isinstance(project_id, str) else repr(project_id))


def is_valid_project_id(project_id: str) -> bool:
    """Non-raising check, for validators that need to collect every error
    rather than stop at the first one (see core/schema.py)."""
    return isinstance(project_id, str) and bool(PROJECT_ID_PATTERN.match(project_id))
