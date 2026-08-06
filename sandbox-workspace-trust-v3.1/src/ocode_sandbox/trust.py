"""Explicit workspace trust.

A workspace must carry an explicit, tamper-evident trust marker before any sandboxed
command may run against it. There is no implicit trust: a missing, malformed, or
tampered marker is treated as untrusted (fail closed), never as an error to ignore.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from pathlib import Path
from typing import Optional

TRUST_DIR_NAME = ".ocode"
TRUST_FILE_NAME = "trust.json"
SCHEMA_VERSION = "ocode.workspace-trust.v1"


@dataclasses.dataclass(frozen=True)
class TrustRecord:
    schema_version: str
    workspace: str
    actor: str
    established_at: float
    trusted: bool
    content_hash: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _trust_path(workspace_dir: Path) -> Path:
    return workspace_dir / TRUST_DIR_NAME / TRUST_FILE_NAME


def _compute_hash(workspace: str, actor: str, established_at: float, trusted: bool) -> str:
    payload = json.dumps(
        {
            "schema_version": SCHEMA_VERSION,
            "workspace": workspace,
            "actor": actor,
            "established_at": established_at,
            "trusted": trusted,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def establish_trust(workspace_dir: Path, actor: str) -> TrustRecord:
    """Explicitly mark a workspace as trusted. Requires an identified actor."""
    if not actor or not actor.strip():
        raise ValueError("establish_trust requires a non-empty actor identity")

    workspace_dir = workspace_dir.resolve()
    if not workspace_dir.is_dir():
        raise FileNotFoundError(f"workspace does not exist: {workspace_dir}")

    established_at = time.time()
    content_hash = _compute_hash(str(workspace_dir), actor, established_at, True)
    record = TrustRecord(
        schema_version=SCHEMA_VERSION,
        workspace=str(workspace_dir),
        actor=actor,
        established_at=established_at,
        trusted=True,
        content_hash=content_hash,
    )

    trust_path = _trust_path(workspace_dir)
    trust_path.parent.mkdir(parents=True, exist_ok=True)
    trust_path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trust_path.chmod(0o600)
    return record


def verify_trust(workspace_dir: Path) -> Optional[TrustRecord]:
    """Return the TrustRecord if, and only if, the workspace carries a valid, intact,
    ``trusted: true`` marker. Any failure mode returns ``None`` (fail closed) rather
    than raising, so callers cannot accidentally treat an exception path as trusted.
    """
    workspace_dir = workspace_dir.resolve()
    trust_path = _trust_path(workspace_dir)
    if not trust_path.is_file():
        return None

    try:
        data = json.loads(trust_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    required_keys = {"schema_version", "workspace", "actor", "established_at", "trusted", "content_hash"}
    if not required_keys.issubset(data.keys()):
        return None

    if data["schema_version"] != SCHEMA_VERSION:
        return None

    if data["workspace"] != str(workspace_dir):
        return None

    if data["trusted"] is not True:
        return None

    expected_hash = _compute_hash(data["workspace"], data["actor"], data["established_at"], True)
    if expected_hash != data["content_hash"]:
        return None

    return TrustRecord(
        schema_version=data["schema_version"],
        workspace=data["workspace"],
        actor=data["actor"],
        established_at=data["established_at"],
        trusted=True,
        content_hash=data["content_hash"],
    )


def revoke_trust(workspace_dir: Path) -> bool:
    """Remove the trust marker. Returns True if a marker was present and removed."""
    workspace_dir = workspace_dir.resolve()
    trust_path = _trust_path(workspace_dir)
    if trust_path.is_file():
        trust_path.unlink()
        return True
    return False
