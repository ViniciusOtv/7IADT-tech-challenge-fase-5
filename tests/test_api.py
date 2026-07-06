import base64
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from strideai.api.main import create_app
from strideai.core.models import DetectedComponent


class _StubDetector:
    def __init__(self, detections):
        self._detections = detections

    def detect(self, image, conf=None):
        return self._detections


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # force template path
    detections = [
        DetectedComponent(component_type="database", confidence=0.9, bbox=(10, 10, 60, 60)),
        DetectedComponent(component_type="user", confidence=0.8, bbox=(100, 100, 150, 150)),
    ]
    app = create_app(detector=_StubDetector(detections))
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_happy_path(client):
    r = client.post("/analyze", files={"file": ("d.png", _png_bytes(), "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert {d["component_type"] for d in body["detections"]} == {"database", "user"}
    assert body["report_source"] == "template"
    assert "Relatório de Modelagem de Ameaças" in body["report_markdown"]
    assert len(body["threat_model"]["components"]) == 2
    # annotated image decodes as a PNG
    img = Image.open(io.BytesIO(base64.b64decode(body["annotated_image_base64"])))
    assert img.size == (200, 200)


def test_analyze_rejects_non_image(client):
    r = client.post("/analyze", files={"file": ("x.txt", b"not an image", "text/plain")})
    assert r.status_code == 422


def test_analyze_zero_detections_is_honest(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = create_app(detector=_StubDetector([]))
    client = TestClient(app)
    r = client.post("/analyze", files={"file": ("d.png", _png_bytes(), "image/png")})
    assert r.status_code == 200
    assert "Nenhum componente reconhecido" in r.json()["report_markdown"]


def test_analyze_survives_decompression_bomb_guard(client, monkeypatch):
    """Regression test for PIL.Image.DecompressionBombError crashing /analyze.

    Pillow raises DecompressionBombError (a plain Exception, not an OSError)
    from Image.open() whenever a decoded image's pixel count exceeds roughly
    2x Image.MAX_IMAGE_PIXELS. strideai.api.main disables that guard at
    import time (Image.MAX_IMAGE_PIXELS = None) because this service is
    trusted-context and relies on its own MAX_IMAGE_SIDE thumbnail step as
    the real safety net.

    To make this deterministic without allocating a genuinely huge image, we
    use monkeypatch to dial Image.MAX_IMAGE_PIXELS down to a tiny value,
    which makes an ordinary small PNG "look like" an oversized image to
    Pillow's guard -- reproducing the exact same code path a real oversized
    upload would hit.
    """
    from PIL import Image as PILImage

    # Sanity check that the fix is actually in place: strideai.api.main must
    # have disabled the guard at import time. If this assertion fails, the
    # rest of this test would be exercising a scenario we rigged ourselves
    # rather than verifying the production fix.
    assert PILImage.MAX_IMAGE_PIXELS is None

    png_bytes = _png_bytes()  # 200x200 = 40_000 pixels

    # 1) Simulate the pre-fix state: the decompression-bomb guard is active
    #    with a threshold far below our test image's pixel count. This is
    #    what the buggy code did for any genuinely oversized upload -- it
    #    crashed with an unhandled DecompressionBombError (-> 500), because
    #    the endpoint's except clause only caught UnidentifiedImageError/OSError.
    monkeypatch.setattr(PILImage, "MAX_IMAGE_PIXELS", 1000)
    unsafe_client = TestClient(client.app, raise_server_exceptions=False)
    r = unsafe_client.post("/analyze", files={"file": ("d.png", png_bytes, "image/png")})
    assert r.status_code == 500

    # 2) Undo *only* our own patch from step 1 (not a fresh hardcoded value):
    #    this restores whatever strideai.api.main actually set at import
    #    time. If the fix were absent, this would restore Pillow's real
    #    default (~89M pixels) rather than None, and the assertion above
    #    would already have failed. Confirm the very same upload now
    #    succeeds instead of crashing.
    monkeypatch.undo()
    assert PILImage.MAX_IMAGE_PIXELS is None
    r = client.post("/analyze", files={"file": ("d.png", png_bytes, "image/png")})
    assert r.status_code == 200
