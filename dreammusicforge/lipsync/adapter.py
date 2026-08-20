"""LipSyncAdapter: the seam a real lip-sync engine plugs into.

Same shape as providers/kling's provider-boundary discipline: this
release defines the contract and a null implementation, not a real
integration -- there's no lip-sync model available in this
dependency-free-until-necessary codebase, and this repository's rule
against claiming an unexecuted integration means "not_applied" has to
stay the honest, load-bearing default, not a low-effort placeholder."""
from __future__ import annotations

from typing import Protocol

from .models import LipSyncRequest, LipSyncResult


class LipSyncAdapter(Protocol):
    def apply(self, request: LipSyncRequest) -> LipSyncResult: ...


class NullLipSyncAdapter:
    """The only adapter this release ships. Always returns
    status="not_applied" -- the request it was given is fully formed
    and ready for a real engine (providers/kling-style: build the
    package, don't fake running it)."""

    def apply(self, request: LipSyncRequest) -> LipSyncResult:
        return LipSyncResult(
            request_id=request.id,
            status="not_applied",
            reason="no lip-sync engine is integrated in this release -- the request is fully formed and ready for a real adapter",
            output_file=None,
        )
