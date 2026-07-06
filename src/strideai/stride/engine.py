"""Deterministic STRIDE analysis: KB lookup per component + composition rules."""
from collections import Counter

from strideai.core.models import (
    COMPONENT_CLASSES,
    ComponentThreats,
    DetectedComponent,
    ThreatModel,
)
from strideai.stride.kb import load_kb

_RULES: list[tuple[set[str], set[str], str]] = [
    # (must be present, must be absent, warning in pt-BR)
    (
        {"database"},
        {"firewall_waf"},
        "Banco de dados detectado sem WAF/firewall na arquitetura — "
        "considere adicionar proteção de perímetro na frente das camadas de aplicação.",
    ),
    (
        {"user"},
        {"auth_service"},
        "Usuários interagem com o sistema, mas nenhum serviço de autenticação dedicado foi "
        "detectado — verifique como identidade e sessões são gerenciadas.",
    ),
    (
        {"external_service"},
        set(),
        "Serviço externo detectado — os dados cruzam a fronteira de confiança da organização; "
        "revise contratos, criptografia e validação das integrações.",
    ),
]


def analyze(detections: list[DetectedComponent]) -> ThreatModel:
    kb = load_kb()
    counts = Counter(d.component_type for d in detections)
    present = set(counts)

    components = [
        ComponentThreats(
            component_type=name,
            instance_count=counts[name],
            threats=kb[name],
        )
        for name in COMPONENT_CLASSES
        if name in counts
    ]

    warnings = [
        warning
        for required, absent, warning in _RULES
        if required <= present and not (absent & present)
    ]

    return ThreatModel(components=components, architecture_warnings=warnings)
