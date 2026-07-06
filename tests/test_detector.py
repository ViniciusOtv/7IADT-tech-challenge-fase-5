import numpy as np
from PIL import Image

from strideai.core.models import COMPONENT_CLASSES
from strideai.detection.detector import ComponentDetector


class _FakeBoxes:
    def __init__(self, xyxy, conf, cls):
        self.xyxy = np.array(xyxy, dtype=float)
        self.conf = np.array(conf, dtype=float)
        self.cls = np.array(cls, dtype=float)


class _FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes
        self.names = dict(enumerate(COMPONENT_CLASSES))


class _FakeModel:
    def __init__(self, result):
        self._result = result
        self.last_conf = None

    def predict(self, image, conf, verbose=False):
        self.last_conf = conf
        return [self._result]


def _image() -> Image.Image:
    return Image.new("RGB", (640, 480), "white")


def test_detect_maps_yolo_output_to_components():
    boxes = _FakeBoxes(
        xyxy=[[10, 20, 110, 120], [200, 200, 260, 260]],
        conf=[0.91, 0.55],
        cls=[COMPONENT_CLASSES.index("database"), COMPONENT_CLASSES.index("user")],
    )
    detector = ComponentDetector(model=_FakeModel(_FakeResult(boxes)))
    detections = detector.detect(_image())
    assert len(detections) == 2
    assert detections[0].component_type == "database"
    assert detections[0].confidence == 0.91
    assert detections[0].bbox == (10.0, 20.0, 110.0, 120.0)
    assert detections[1].component_type == "user"


def test_detect_uses_default_and_override_conf():
    boxes = _FakeBoxes(xyxy=np.empty((0, 4)), conf=[], cls=[])
    model = _FakeModel(_FakeResult(boxes))
    detector = ComponentDetector(model=model, conf_threshold=0.4)
    detector.detect(_image())
    assert model.last_conf == 0.4
    detector.detect(_image(), conf=0.7)
    assert model.last_conf == 0.7


def test_detect_empty_result():
    boxes = _FakeBoxes(xyxy=np.empty((0, 4)), conf=[], cls=[])
    detector = ComponentDetector(model=_FakeModel(_FakeResult(boxes)))
    assert detector.detect(_image()) == []
