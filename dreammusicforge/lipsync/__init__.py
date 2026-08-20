"""DreamMusicForge Film Compiler -- lipsync package (Release 0.12).

Not verified against the original spec's own text for this release --
see models.py's module docstring for why.

Public API:

    from dreammusicforge.lipsync import (
        LIP_SYNC_RESULT_STATUSES, LipSyncRequest, LipSyncResult,
        LipSyncAdapter, NullLipSyncAdapter,
        build_lip_sync_request, apply_lip_sync,
        validate_lip_sync_request_schema, validate_lip_sync_result_schema,
        generate_lip_sync_request_id, is_valid_lip_sync_request_id,
        LipSyncError,
    )
"""
from __future__ import annotations

from .adapter import LipSyncAdapter, NullLipSyncAdapter
from .builder import apply_lip_sync, build_lip_sync_request
from .errors import LipSyncError
from .ids import generate_lip_sync_request_id, is_valid_lip_sync_request_id
from .models import LIP_SYNC_RESULT_STATUSES, LipSyncRequest, LipSyncResult
from .schema import validate_lip_sync_request_schema, validate_lip_sync_result_schema

__all__ = [
    "LIP_SYNC_RESULT_STATUSES", "LipSyncAdapter", "LipSyncError", "LipSyncRequest", "LipSyncResult",
    "NullLipSyncAdapter", "apply_lip_sync", "build_lip_sync_request", "generate_lip_sync_request_id",
    "is_valid_lip_sync_request_id", "validate_lip_sync_request_schema", "validate_lip_sync_result_schema",
]
