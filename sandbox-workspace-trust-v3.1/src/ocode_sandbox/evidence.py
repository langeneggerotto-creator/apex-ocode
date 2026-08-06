"""Structured, secret-scrubbed evidence records for sandboxed runs.

Every claim this module supports is an executed, observed fact (exit code, which
controls were actually applied, resource usage read back from the kernel) — never an
aspirational or assumed claim.
"""

from __future__ import annotations

import dataclasses
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

MAX_CAPTURED_OUTPUT_BYTES = 8192

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*\S+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"[A-Za-z0-9_\-]{32,}"),
]

_REDACTED = "[REDACTED]"


def scrub(text: str) -> str:
    scrubbed = text
    for pattern in _SECRET_PATTERNS:
        scrubbed = pattern.sub(_REDACTED, scrubbed)
    return scrubbed


def cap_and_scrub(text: Optional[str]) -> str:
    if text is None:
        return ""
    truncated = text[:MAX_CAPTURED_OUTPUT_BYTES]
    if len(text) > MAX_CAPTURED_OUTPUT_BYTES:
        truncated += f"\n...[truncated, {len(text) - MAX_CAPTURED_OUTPUT_BYTES} bytes omitted]"
    return scrub(truncated)


@dataclasses.dataclass
class EvidenceRecord:
    schema_version: str
    run_id: str
    started_at: float
    finished_at: float
    workspace: str
    command: List[str]
    controls_applied: Dict[str, Any]
    exit_code: Optional[int]
    timed_out: bool
    resource_usage: Dict[str, Any]
    stdout: str
    stderr: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def write_evidence(record: EvidenceRecord, evidence_dir: Path) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_path = evidence_dir / f"run-{record.run_id}.json"
    out_path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path


def new_run_id() -> str:
    return f"{int(time.time() * 1000):x}"
