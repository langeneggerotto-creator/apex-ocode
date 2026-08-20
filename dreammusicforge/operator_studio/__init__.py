"""DreamMusicForge Film Compiler -- operator_studio package (Release 0.15).

Not verified against the original spec's own text for this release --
see models.py's module docstring for why.

Public API:

    from dreammusicforge.operator_studio import (
        OperatorReport,
        build_operator_report, render_report_html, create_operator_server,
        validate_operator_report_schema,
        generate_operator_report_id, is_valid_operator_report_id,
        OperatorStudioError,
    )
"""
from __future__ import annotations

from .builder import build_operator_report
from .errors import OperatorStudioError
from .ids import generate_operator_report_id, is_valid_operator_report_id
from .models import OperatorReport
from .render import render_report_html
from .schema import validate_operator_report_schema
from .server import create_operator_server

__all__ = [
    "OperatorReport", "OperatorStudioError", "build_operator_report", "create_operator_server",
    "generate_operator_report_id", "is_valid_operator_report_id", "render_report_html",
    "validate_operator_report_schema",
]
