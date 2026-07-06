"""LLM-written report grounded exclusively in the structured ThreatModel."""
import os

import anthropic

from strideai.core.models import ThreatModel

DEFAULT_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = """Você é um analista de segurança que escreve relatórios de modelagem \
de ameaças STRIDE em português do Brasil, em Markdown.

Você receberá um JSON com os componentes detectados em um diagrama de arquitetura, as \
ameaças STRIDE de cada componente e avisos de arquitetura. Escreva um relatório com:
1. Um título "# Relatório de Modelagem de Ameaças (STRIDE)".
2. Um sumário executivo (2-3 parágrafos) sobre a postura de segurança da arquitetura.
3. Uma seção "## Avisos de Arquitetura" (se houver avisos).
4. Uma seção "## Ameaças por Componente" com uma subseção por componente listando \
categoria STRIDE, severidade, descrição e contramedidas.
5. Uma seção final "## Contramedidas Prioritárias" com as 5 ações mais importantes, \
priorizando severidade alta.

REGRAS ESTRITAS: use APENAS os componentes, ameaças e contramedidas presentes no JSON. \
Não invente componentes, ameaças ou contramedidas. Você pode reformular e organizar o \
texto, mas não adicionar conteúdo técnico novo."""


class LLMError(Exception):
    """Raised when the LLM report could not be produced for any reason."""


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def write_report(tm: ThreatModel) -> str:
    model = os.environ.get("STRIDEAI_LLM_MODEL", DEFAULT_MODEL)
    try:
        payload = tm.model_dump_json(indent=2)
        response = _get_client().messages.create(
            model=model,
            max_tokens=8000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Modelo de ameaças (JSON):\n{payload}"}],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
    except Exception as exc:  # any SDK/network failure means: fall back
        raise LLMError(str(exc)) from exc
    if not text.strip():
        raise LLMError("empty LLM response")
    return text
