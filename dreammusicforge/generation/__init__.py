"""DreamMusicForge Film Compiler -- generation package (Release 0.8).

Public API:

    from dreammusicforge.generation import (
        CANDIDATE_VERIFICATION_STATUSES, CANDIDATE_DECISIONS, Candidate,
        import_candidate, validate_candidate_schema,
        generate_candidate_id, is_valid_candidate_id,
        CandidateIntakeError,
    )

Everything else in the full spec (technical verification, repair,
assembly, ...) is later releases and is not present here.
"""
from __future__ import annotations

from .errors import CandidateIntakeError
from .ids import generate_candidate_id, is_valid_candidate_id
from .intake import import_candidate
from .models import CANDIDATE_DECISIONS, CANDIDATE_VERIFICATION_STATUSES, Candidate
from .schema import validate_candidate_schema

__all__ = [
    "CANDIDATE_DECISIONS", "CANDIDATE_VERIFICATION_STATUSES", "Candidate", "CandidateIntakeError",
    "generate_candidate_id", "import_candidate", "is_valid_candidate_id", "validate_candidate_schema",
]
