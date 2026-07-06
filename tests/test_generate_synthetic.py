import random
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dataset"))
from generate_synthetic import generate_diagram, load_icon_library  # noqa: E402

from strideai.core.models import COMPONENT_CLASSES  # noqa: E402


def _make_icons(tmp_path: Path) -> Path:
    icons = tmp_path / "icons"
    for name, color in [("user", "blue"), ("database", "red"), ("api_gateway", "green")]:
        d = icons / name
        d.mkdir(parents=True)
        Image.new("RGB", (64, 64), color).save(d / "icon1.png")
    return icons


def test_load_icon_library_only_known_classes(tmp_path):
    icons = _make_icons(tmp_path)
    (icons / "mainframe").mkdir()  # unknown class dir must be ignored
    lib = load_icon_library(icons)
    assert set(lib.keys()) == {"user", "database", "api_gateway"}
    assert all(len(v) == 1 for v in lib.values())


def test_generate_diagram_produces_valid_yolo_labels(tmp_path):
    lib = load_icon_library(_make_icons(tmp_path))
    rng = random.Random(42)
    image, labels = generate_diagram(lib, rng, canvas_size=(800, 600))
    assert image.size == (800, 600)
    assert len(labels) >= 3
    for line in labels:
        parts = line.split()
        assert len(parts) == 5
        cls_idx = int(parts[0])
        assert 0 <= cls_idx < len(COMPONENT_CLASSES)
        cx, cy, w, h = map(float, parts[1:])
        assert 0.0 < cx < 1.0 and 0.0 < cy < 1.0
        assert 0.0 < w <= 1.0 and 0.0 < h <= 1.0


def test_generate_diagram_deterministic_with_seed(tmp_path):
    lib = load_icon_library(_make_icons(tmp_path))
    _, labels_a = generate_diagram(lib, random.Random(7), canvas_size=(800, 600))
    _, labels_b = generate_diagram(lib, random.Random(7), canvas_size=(800, 600))
    assert labels_a == labels_b
