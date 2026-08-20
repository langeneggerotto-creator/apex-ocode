"""build_operator_report(): assembles a validated, immutable
OperatorReport snapshot from whatever typed results a caller currently
holds in memory."""
from __future__ import annotations

from ..assembly.models import ExportManifest
from ..finishing.models import FinishingResult
from ..repair.models import VerificationResult
from .errors import OperatorStudioError
from .ids import generate_operator_report_id
from .models import OperatorReport
from .schema import validate_operator_report_schema


def build_operator_report(
    verification_results: tuple[VerificationResult, ...] = (),
    export_manifests: tuple[ExportManifest, ...] = (),
    finishing_results: tuple[FinishingResult, ...] = (),
    generated_at: str = "",
    report_id: str | None = None,
) -> OperatorReport:
    report = OperatorReport(
        id=report_id or generate_operator_report_id(),
        generated_at=generated_at,
        verification_results=tuple(verification_results),
        export_manifests=tuple(export_manifests),
        finishing_results=tuple(finishing_results),
    )

    errors = validate_operator_report_schema(report.to_dict())
    if errors:
        raise OperatorStudioError(errors)
    return report
