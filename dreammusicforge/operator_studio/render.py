"""render_report_html(): turns an OperatorReport into one self-contained
HTML page -- inline CSS only, no external assets, no JavaScript. Every
dynamic string is passed through html.escape() before being written
into the page; none of this data is trusted (candidate ids, defect
recommendations, and repair actions all ultimately trace back to
provider output or human-entered strings upstream)."""
from __future__ import annotations

from html import escape

from .models import OperatorReport

_STYLE = """
body { font-family: -apple-system, sans-serif; margin: 2rem; color: #1a1a1a; background: #fafafa; }
h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 0.3rem; }
table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }
th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }
th { background: #f0f0f0; }
.accept { color: #1a7f37; font-weight: 600; } .reject { color: #b42318; font-weight: 600; }
.empty { color: #888; font-style: italic; }
"""


def _verification_rows(results, decision: str) -> str:
    rows = [r for r in results if r.decision == decision]
    if not rows:
        return '<p class="empty">none</p>'
    body = "".join(
        f"<tr><td>{escape(r.candidate_id)}</td><td>{escape(f'{r.overall_score:.1f}')}</td>"
        f"<td>{escape(', '.join(r.critical_failures) or '-')}</td>"
        f"<td>{escape(r.repair.action if r.repair else '-')}</td></tr>"
        for r in rows
    )
    return f"<table><tr><th>Candidate</th><th>Score</th><th>Critical failures</th><th>Repair action</th></tr>{body}</table>"


def _export_rows(manifests) -> str:
    if not manifests:
        return '<p class="empty">none</p>'
    body = "".join(
        f"<tr><td>{escape(m.id)}</td><td>{escape(m.output_file)}</td>"
        f"<td>{escape(f'{m.total_duration_seconds:.2f}s')}</td><td>{escape(m.output_hash[:12])}...</td></tr>"
        for m in manifests
    )
    return f"<table><tr><th>Export</th><th>Output file</th><th>Duration</th><th>Hash</th></tr>{body}</table>"


def _finishing_rows(results) -> str:
    if not results:
        return '<p class="empty">none</p>'
    body = "".join(
        f"<tr><td>{escape(r.id)}</td><td>{escape(f'{r.measured_loudness.integrated_lufs:.1f} LUFS')}</td>"
        f"<td>{escape(f'{r.target_lufs:.1f} LUFS')}</td><td>{escape(r.output_file)}</td></tr>"
        for r in results
    )
    return f"<table><tr><th>Result</th><th>Measured loudness</th><th>Target</th><th>Output file</th></tr>{body}</table>"


def render_report_html(report: OperatorReport) -> str:
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>DreamMusicForge Operator Studio</title><style>{_STYLE}</style></head>
<body>
<h1>Operator Studio</h1>
<p>Report {escape(report.id)} &mdash; generated {escape(report.generated_at)}</p>

<h2 class="reject">Needs decision (rejected)</h2>
{_verification_rows(report.verification_results, "reject")}

<h2 class="accept">Accepted</h2>
{_verification_rows(report.verification_results, "accept")}

<h2>Assembled exports</h2>
{_export_rows(report.export_manifests)}

<h2>Finished (color/audio) exports</h2>
{_finishing_rows(report.finishing_results)}
</body>
</html>
"""
