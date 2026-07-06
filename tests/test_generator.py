from strideai.core.models import ComponentThreats, Severity, StrideCategory, Threat, ThreatModel
from strideai.report import generator
from strideai.report.llm_writer import LLMError


def _model() -> ThreatModel:
    return ThreatModel(
        components=[
            ComponentThreats(
                component_type="user",
                instance_count=1,
                threats=[
                    Threat(
                        category=StrideCategory.SPOOFING,
                        description="d",
                        severity=Severity.HIGH,
                        countermeasures=["m"],
                    )
                ],
            )
        ]
    )


def test_uses_llm_when_available(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(generator, "write_report", lambda tm: "# LLM")
    md, source = generator.generate_report(_model())
    assert (md, source) == ("# LLM", "llm")


def test_falls_back_when_llm_fails(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def boom(tm):
        raise LLMError("down")

    monkeypatch.setattr(generator, "write_report", boom)
    md, source = generator.generate_report(_model())
    assert source == "template"
    assert "Relatório de Modelagem de Ameaças" in md


def test_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    md, source = generator.generate_report(_model())
    assert source == "template"


def test_empty_model_skips_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def never(tm):
        raise AssertionError("LLM must not be called for empty models")

    monkeypatch.setattr(generator, "write_report", never)
    md, source = generator.generate_report(ThreatModel())
    assert source == "template"
    assert "Nenhum componente reconhecido" in md
