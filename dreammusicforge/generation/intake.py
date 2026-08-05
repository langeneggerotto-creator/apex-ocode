"""import_candidate(): the "candidate import" deliverable (spec section
19) -- reads a rendered candidate file's real size and sha256 hash from
disk (reusing core/hashing.py's hash_file(), same stdlib-only,
no-new-dependency discipline as music/wav_inspector.py), hashes the
prompt that produced it, and hashes every reference asset file supplied,
producing a Candidate that's independently verifiable rather than
merely asserted -- this release's acceptance test: "every imported
candidate is traceable."

Fails closed: a missing candidate file or a missing reference file
raises CandidateIntakeError rather than silently skipping it or hashing
nothing, since a Candidate whose hash can't be trusted isn't actually
traceable.
"""
from __future__ import annotations

from pathlib import Path

from ..core.hashing import hash_file, hash_text
from .errors import CandidateIntakeError
from .ids import generate_candidate_id
from .models import Candidate
from .schema import validate_candidate_schema


def import_candidate(
    render_task_id: str,
    provider: str,
    model_version: str,
    file_path: Path,
    prompt: str,
    imported_at: str,
    reference_paths: tuple[Path, ...] = (),
    candidate_id: str | None = None,
) -> Candidate:
    if not file_path.is_file():
        raise CandidateIntakeError([f"no such candidate file: {file_path}"])

    missing_references = [str(path) for path in reference_paths if not path.is_file()]
    if missing_references:
        raise CandidateIntakeError([f"no such reference file: {path}" for path in missing_references])

    candidate = Candidate(
        id=candidate_id or generate_candidate_id(),
        render_task_id=render_task_id,
        provider=provider,
        model_version=model_version,
        file=str(file_path),
        file_size_bytes=file_path.stat().st_size,
        prompt_hash=hash_text(prompt),
        reference_hashes=tuple(hash_file(path) for path in reference_paths),
        output_hash=hash_file(file_path),
        imported_at=imported_at,
    )

    errors = validate_candidate_schema(candidate.to_dict())
    if errors:
        raise CandidateIntakeError(errors)
    return candidate
