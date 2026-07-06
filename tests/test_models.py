import pytest
from pydantic import ValidationError

from strideai.core.models import (
    COMPONENT_CLASSES,
    ComponentThreats,
    DetectedComponent,
    Severity,
    StrideCategory,
    Threat,
    ThreatModel,
)


def test_component_classes_order_and_content():
    assert COMPONENT_CLASSES == [
        "user", "web_client", "api_gateway", "load_balancer", "app_server",
        "database", "cache", "queue", "storage", "function_serverless",
        "firewall_waf", "auth_service", "cdn", "monitoring", "external_service",
    ]


def test_stride_has_six_categories():
    assert len(StrideCategory) == 6


def test_detected_component_roundtrip():
    c = DetectedComponent(component_type="database", confidence=0.91, bbox=(10, 20, 110, 120))
    data = c.model_dump()
    assert DetectedComponent(**data) == c


def test_detected_component_rejects_unknown_class():
    with pytest.raises(ValidationError):
        DetectedComponent(component_type="mainframe", confidence=0.9, bbox=(0, 0, 1, 1))


def test_detected_component_rejects_bad_confidence():
    with pytest.raises(ValidationError):
        DetectedComponent(component_type="user", confidence=1.5, bbox=(0, 0, 1, 1))


def test_threat_model_shape():
    tm = ThreatModel(
        components=[
            ComponentThreats(
                component_type="database",
                instance_count=2,
                threats=[
                    Threat(
                        category=StrideCategory.TAMPERING,
                        description="x",
                        severity=Severity.HIGH,
                        countermeasures=["y"],
                    )
                ],
            )
        ],
        architecture_warnings=["w"],
    )
    assert tm.components[0].instance_count == 2
