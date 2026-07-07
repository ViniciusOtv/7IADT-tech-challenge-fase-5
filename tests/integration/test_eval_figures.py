"""Full-pipeline smoke tests against the challenge's evaluation figures.

These are the acceptance bar from the design spec: the pipeline must identify
the major components in both PDF figures. Skipped until trained weights exist.
Run explicitly with: python -m pytest -m integration -v
"""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = ROOT / "models" / "best.pt"
FIXTURES = ROOT / "tests" / "fixtures"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not WEIGHTS.exists(), reason="trained weights not present"),
    pytest.mark.skipif(
        not (FIXTURES / "eval_arch1.png").exists(), reason="fixtures not extracted"
    ),
]


@pytest.fixture(scope="module")
def client():
    from strideai.api.main import create_app
    from strideai.detection.detector import ComponentDetector

    app = create_app(detector=ComponentDetector(weights_path=str(WEIGHTS)))
    return TestClient(app)


def _analyze(client, fixture: str) -> set[str]:
    data = (FIXTURES / fixture).read_bytes()
    r = client.post("/analyze", files={"file": (fixture, io.BytesIO(data), "image/png")})
    assert r.status_code == 200
    return {d["component_type"] for d in r.json()["detections"]}


def test_arch1_aws_key_components(client):
    found = _analyze(client, "eval_arch1.png")
    expected = {"user", "load_balancer", "database", "firewall_waf"}
    missing = expected - found
    assert not missing, f"missing key components in AWS figure: {missing} (found: {found})"


def test_arch2_azure_key_components(client):
    found = _analyze(client, "eval_arch2.png")
    expected = {"user", "api_gateway", "external_service"}
    missing = expected - found
    assert not missing, f"missing key components in Azure figure: {missing} (found: {found})"


def test_reports_generated_for_both(client):
    for fixture in ("eval_arch1.png", "eval_arch2.png"):
        data = (FIXTURES / fixture).read_bytes()
        r = client.post("/analyze", files={"file": (fixture, io.BytesIO(data), "image/png")})
        assert "Relatório de Modelagem de Ameaças" in r.json()["report_markdown"]
