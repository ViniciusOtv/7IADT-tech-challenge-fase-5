"""FastAPI service: upload a diagram image, receive the STRIDE analysis."""
import base64
import io
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from strideai.core.models import AnalysisResponse
from strideai.detection.annotate import draw_detections
from strideai.report.generator import generate_report
from strideai.stride.engine import analyze

MAX_IMAGE_SIDE = 2560  # downscale huge uploads before inference


def create_app(detector=None) -> FastAPI:
    app = FastAPI(title="STRIDE Threat Modeling API", version="0.1.0")
    app.state.detector = detector

    @app.get("/health")
    def health():
        return {"status": "ok", "detector_loaded": app.state.detector is not None}

    @app.post("/analyze", response_model=AnalysisResponse)
    def analyze_diagram(
        file: UploadFile = File(...),
        conf_threshold: float = Form(0.4),
    ):
        if app.state.detector is None:
            raise HTTPException(status_code=503, detail="detector not loaded")
        try:
            image = Image.open(io.BytesIO(file.file.read()))
            image.load()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise HTTPException(status_code=422, detail="arquivo enviado não é uma imagem válida")

        if max(image.size) > MAX_IMAGE_SIDE:
            image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))

        detections = app.state.detector.detect(image, conf=conf_threshold)
        threat_model = analyze(detections)
        report_md, source = generate_report(threat_model)

        annotated = draw_detections(image, detections)
        buf = io.BytesIO()
        annotated.save(buf, format="PNG")

        return AnalysisResponse(
            detections=detections,
            threat_model=threat_model,
            report_markdown=report_md,
            report_source=source,
            annotated_image_base64=base64.b64encode(buf.getvalue()).decode("ascii"),
        )

    return app


def _default_app() -> FastAPI:
    weights = os.environ.get("STRIDEAI_WEIGHTS", "models/best.pt")
    detector = None
    if os.path.exists(weights):
        from strideai.detection.detector import ComponentDetector

        detector = ComponentDetector(weights_path=weights)
    return create_app(detector=detector)


app = _default_app()
