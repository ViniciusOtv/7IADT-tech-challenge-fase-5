from PIL import Image

from strideai.core.models import DetectedComponent
from strideai.detection.annotate import draw_detections


def test_draw_detections_returns_new_image_with_boxes():
    img = Image.new("RGB", (300, 300), "white")
    dets = [DetectedComponent(component_type="database", confidence=0.9, bbox=(50, 50, 150, 150))]
    out = draw_detections(img, dets)
    assert out is not img
    assert out.size == img.size
    # box edge pixel is no longer white
    assert out.getpixel((50, 100)) != (255, 255, 255)


def test_draw_detections_handles_empty_list():
    img = Image.new("RGB", (100, 100), "white")
    out = draw_detections(img, [])
    assert out.size == (100, 100)
