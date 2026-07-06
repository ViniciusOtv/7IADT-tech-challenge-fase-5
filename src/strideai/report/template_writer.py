"""Deterministic Markdown report from a ThreatModel (fallback path)."""
from jinja2 import Environment, PackageLoader, select_autoescape

from strideai.core.models import ThreatModel

_env = Environment(
    loader=PackageLoader("strideai.report", "templates"),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_report(tm: ThreatModel) -> str:
    return _env.get_template("report.md.j2").render(tm=tm)
