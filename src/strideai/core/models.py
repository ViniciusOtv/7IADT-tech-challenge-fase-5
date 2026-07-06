"""Shared contracts between detection, STRIDE engine, report, and API."""
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# Canonical component classes. The list index IS the YOLO class index.
COMPONENT_CLASSES: list[str] = [
    "user", "web_client", "api_gateway", "load_balancer", "app_server",
    "database", "cache", "queue", "storage", "function_serverless",
    "firewall_waf", "auth_service", "cdn", "monitoring", "external_service",
]


class StrideCategory(str, Enum):
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DetectedComponent(BaseModel):
    component_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels

    @field_validator("component_type")
    @classmethod
    def _known_class(cls, v: str) -> str:
        if v not in COMPONENT_CLASSES:
            raise ValueError(f"unknown component class: {v}")
        return v


class Threat(BaseModel):
    category: StrideCategory
    description: str
    severity: Severity
    countermeasures: list[str]


class ComponentThreats(BaseModel):
    component_type: str
    instance_count: int = Field(ge=1)
    threats: list[Threat]


class ThreatModel(BaseModel):
    components: list[ComponentThreats] = []
    architecture_warnings: list[str] = []


class AnalysisResponse(BaseModel):
    detections: list[DetectedComponent]
    threat_model: ThreatModel
    report_markdown: str
    report_source: str  # "llm" | "template"
    annotated_image_base64: str
