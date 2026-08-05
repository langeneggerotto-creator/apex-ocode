"""Identifier generation and validation for kernel entities.

Every id in this application follows PREFIX-TOKEN, where TOKEN is 8
lowercase hex characters from `secrets.token_hex` -- unique per call
(not content-derived; that's what core/hashing.py is for), but formatted
deterministically and checkably so a malformed id is always caught rather
than accepted and causing confusing failures downstream.

generate_id()/is_valid_id() are the generic, prefix-parameterized form,
added in Release 0.2 for the new entity types (AUDIO-, SECTION-, LYRIC-)
introduced there. generate_project_id()/validate_project_id()/
is_valid_project_id() -- Release 0.1's original, still-exact API -- are
now thin wrappers over them; behavior is unchanged (see
tests/kernel/test_ids.py, which still passes unmodified)."""
from __future__ import annotations

import re
import secrets

from .errors import InvalidProjectIdError

PROJECT_ID_PREFIX = "DMF-PROJECT-"
PROJECT_ID_PATTERN = re.compile(rf"^{re.escape(PROJECT_ID_PREFIX)}[0-9a-f]{{8}}$")

_ID_TOKEN_PATTERN = "[0-9a-f]{8}"


def generate_id(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(4)}"


def is_valid_id(value: object, prefix: str) -> bool:
    if not isinstance(value, str):
        return False
    pattern = re.compile(rf"^{re.escape(prefix)}{_ID_TOKEN_PATTERN}$")
    return bool(pattern.match(value))


def generate_project_id() -> str:
    return generate_id(PROJECT_ID_PREFIX)


def validate_project_id(project_id: str) -> None:
    """Raises InvalidProjectIdError if project_id doesn't match the
    required format. Returns None (not a bool) so callers can't
    accidentally ignore a False result -- fail closed."""
    if not is_valid_id(project_id, PROJECT_ID_PREFIX):
        raise InvalidProjectIdError(project_id if isinstance(project_id, str) else repr(project_id))


def is_valid_project_id(project_id: str) -> bool:
    """Non-raising check, for validators that need to collect every error
    rather than stop at the first one (see core/schema.py)."""
    return is_valid_id(project_id, PROJECT_ID_PREFIX)
