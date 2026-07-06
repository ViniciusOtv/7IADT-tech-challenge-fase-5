"""Draws labeled bounding boxes on a copy of the input image."""
from PIL import Image, ImageDraw

from strideai.core.models import COMPONENT_CLASSES, DetectedComponent

# one deterministic color per class index
_PALETTE = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#46f0f0", "#f032e6", "#bcf60c", "#008080", "#9a6324",
    "#800000", "#808000", "#000075", "#e67e22", "#2c3e50",
]


def draw_detections(image: Image.Image, detections: list[DetectedComponent]) -> Image.Image:
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    for d in detections:
        color = _PALETTE[COMPONENT_CLASSES.index(d.component_type)]
        x1, y1, x2, y2 = d.bbox
        draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
        label = f"{d.component_type} {d.confidence:.2f}"
        draw.text((x1 + 2, max(0, y1 - 14)), label, fill=color)
    return out
