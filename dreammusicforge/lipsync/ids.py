"""Identifier generation and validation for Release 0.12's LipSyncRequest,
built on the generic generate_id()/is_valid_id() core.ids added in
Release 0.2 -- same pattern as every sibling package's ids.py.

LipSyncResult doesn't get its own id: it always exists attached to the
request_id that produced it, same reasoning repair/ids.py's docstring
gives for VerificationResult not having a separate id."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

LIP_SYNC_REQUEST_ID_PREFIX = "LIPSYNC-"


def generate_lip_sync_request_id() -> str:
    return generate_id(LIP_SYNC_REQUEST_ID_PREFIX)


def is_valid_lip_sync_request_id(value: object) -> bool:
    return is_valid_id(value, LIP_SYNC_REQUEST_ID_PREFIX)
