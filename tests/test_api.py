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


def test_analyze_rejects_decompression_bomb_sized_image(client, monkeypatch):
    """Regression test: a decompression-bomb-sized image must be rejected
    gracefully (422), not disable Pillow's guard or crash the process.

    An earlier fix for a 500-on-oversized-upload bug disabled Pillow's
    decompression-bomb guard entirely (Image.MAX_IMAGE_PIXELS = None). Code
    review caught that this removed the only protection against a maliciously
    crafted small-file/huge-declared-dimensions image: with the guard
    disabled, Image.open() would happily accept it and image.load() would
    then try to allocate/decode the full declared pixel buffer (potentially
    many GB) *before* the MAX_IMAGE_SIDE thumbnail check ever runs -- turning
    a contained per-request 500 into an uncontained process-wide OOM.

    The corrected fix keeps Pillow's guard active (default MAX_IMAGE_PIXELS)
    and instead catches Image.DecompressionBombError alongside the other
    invalid-image errors, so such uploads are rejected early with the same
    422 response as any other invalid/corrupt image.

    To make this deterministic without allocating a genuinely huge image, we
    use monkeypatch to dial Image.MAX_IMAGE_PIXELS down to a tiny value,
    which makes an ordinary small PNG "look like" an oversized image to
    Pillow's guard -- reproducing the exact same code path a real bomb-sized
    upload would hit.
    """
    from PIL import Image as PILImage

    # Sanity check that the fix is actually in place: strideai.api.main must
    # NOT have disabled Pillow's guard at import time. If this assertion
    # fails, the rest of this test would be exercising a scenario we rigged
    # ourselves rather than verifying the production behavior.
    assert PILImage.MAX_IMAGE_PIXELS is not None

    png_bytes = _png_bytes()  # 200x200 = 40_000 pixels

    # Dial the guard's threshold down far below our test image's pixel
    # count, so Pillow raises DecompressionBombError from Image.open() just
    # as it would for a real bomb-sized upload. The endpoint must catch this
    # and respond with a graceful 422, not crash with a 500.
    monkeypatch.setattr(PILImage, "MAX_IMAGE_PIXELS", 1000)
    r = client.post("/analyze", files={"file": ("d.png", png_bytes, "image/png")})
    assert r.status_code == 422
