"""Wraps a trained YOLO model; converts raw results to DetectedComponent."""
from PIL import Image

from strideai.core.models import DetectedComponent


class ComponentDetector:
    def __init__(self, weights_path: str | None = None, model=None, conf_threshold: float = 0.4):
        if model is not None:
            self._model = model
        elif weights_path is not None:
            from ultralytics import YOLO  # imported lazily: slow import, heavy deps

            self._model = YOLO(weights_path)
        else:
            raise ValueError("either weights_path or model must be provided")
        self.conf_threshold = conf_threshold

    def detect(self, image: Image.Image, conf: float | None = None) -> list[DetectedComponent]:
        threshold = self.conf_threshold if conf is None else conf
        result = self._model.predict(image, conf=threshold, verbose=False)[0]
        names = result.names
        detections = []
        for xyxy, score, cls_idx in zip(
            result.boxes.xyxy.tolist(),
            result.boxes.conf.tolist(),
            result.boxes.cls.tolist(),
        ):
            detections.append(
                DetectedComponent(
                    component_type=names[int(cls_idx)],
                    confidence=round(float(score), 4),
                    bbox=tuple(round(v, 1) for v in xyxy),
                )
            )
        return detections
