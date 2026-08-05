"""Typed errors for the repair package, extending core.errors' DMFError
hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class AcceptanceRepairError(DMFError):
    """Raised when a VerificationResult/Defect/RepairPlan fails
    validation. Carries every problem found, same discipline as every
    other *ValidationError in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "acceptance/repair validation failed")
