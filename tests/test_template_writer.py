from strideai.core.models import ComponentThreats, Severity, StrideCategory, Threat, ThreatModel
from strideai.report.template_writer import render_report


def _model() -> ThreatModel:
    return ThreatModel(
        components=[
            ComponentThreats(
                component_type="database",
                instance_count=2,
                threats=[
                    Threat(
                        category=StrideCategory.TAMPERING,
                        description="Alteração não autorizada de dados.",
                        severity=Severity.HIGH,
                        countermeasures=["Consultas parametrizadas"],
                    )
                ],
            )
        ],
        architecture_warnings=["Aviso de arquitetura X."],
    )


def test_report_contains_key_sections():
    md = render_report(_model())
    assert "# Relatório de Modelagem de Ameaças" in md
    assert "database" in md
    assert "Tampering" in md
    assert "Consultas parametrizadas" in md
    assert "Aviso de arquitetura X." in md
    assert "2 instância(s)" in md


def test_empty_model_renders_honest_message():
    md = render_report(ThreatModel())
    assert "Nenhum componente reconhecido" in md


def test_multiple_threats_separated_by_blank_lines():
    """Verify that consecutive threats are separated by blank lines."""
    tm = ThreatModel(
        components=[
            ComponentThreats(
                component_type="api",
                instance_count=1,
                threats=[
                    Threat(
                        category=StrideCategory.SPOOFING,
                        description="Identidade não verificada.",
                        severity=Severity.LOW,
                        countermeasures=["Autenticação OAuth2"],
                    ),
                    Threat(
                        category=StrideCategory.TAMPERING,
                        description="Alteração não autorizada.",
                        severity=Severity.MEDIUM,
                        countermeasures=["Criptografia", "Assinatura digital"],
                    ),
                ],
            )
        ],
    )
    md = render_report(tm)

    # Extract the threats section to verify blank line separation
    # Find the first threat header
    spoofing_idx = md.find("**Spoofing**")
    tampering_idx = md.find("**Tampering**")

    assert spoofing_idx != -1, "First threat not found"
    assert tampering_idx != -1, "Second threat not found"
    assert spoofing_idx < tampering_idx, "Threats not in order"

    # Extract text between the two threat headers
    between_threats = md[spoofing_idx:tampering_idx]

    # Verify there's a blank line (two consecutive newlines) before the second threat
    # This should exist after the countermeasures of the first threat
    assert "\n\n**Tampering**" in md, "No blank line between threat blocks"
