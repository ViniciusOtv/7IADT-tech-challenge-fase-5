"""Chooses the LLM path when possible, template fallback otherwise."""
import os

from strideai.core.models import ThreatModel
from strideai.report.llm_writer import LLMError, write_report
from strideai.report.template_writer import render_report


def generate_report(tm: ThreatModel) -> tuple[str, str]:
    """Returns (markdown, source) where source is 'llm' or 'template'."""
    if not tm.components or not os.environ.get("ANTHROPIC_API_KEY"):
        return render_report(tm), "template"
    try:
        return write_report(tm), "llm"
    except LLMError:
        return render_report(tm), "template"
