import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dataset"))
from build_dataset import remap_label_line  # noqa: E402

from strideai.core.models import COMPONENT_CLASSES  # noqa: E402


def test_remap_label_line():
    mapping = {0: "database", 3: "user"}
    assert remap_label_line("0 0.5 0.5 0.1 0.1", mapping).startswith(
        str(COMPONENT_CLASSES.index("database"))
    )
    assert remap_label_line("3 0.2 0.2 0.1 0.1", mapping).startswith(
        str(COMPONENT_CLASSES.index("user"))
    )
    assert remap_label_line("7 0.2 0.2 0.1 0.1", mapping) is None  # unmapped -> dropped


def _mk_yolo_dir(root: Path, stems: list[str], cls_line: str) -> None:
    (root / "images").mkdir(parents=True)
    (root / "labels").mkdir(parents=True)
    for s in stems:
        Image.new("RGB", (64, 64), "white").save(root / "images" / f"{s}.jpg")
        (root / "labels" / f"{s}.txt").write_text(cls_line, encoding="utf-8")


def test_cli_builds_split_structure(tmp_path):
    synthetic = tmp_path / "synthetic"
    real = tmp_path / "external"
    out = tmp_path / "final"
    _mk_yolo_dir(synthetic, ["s1", "s2"], "5 0.5 0.5 0.2 0.2")  # already canonical indices
    _mk_yolo_dir(real, ["r1", "r2", "r3", "r4"], "0 0.5 0.5 0.2 0.2")
    (real / "mapping.yaml").write_text("0: database\n", encoding="utf-8")

    script = Path(__file__).resolve().parents[1] / "dataset" / "build_dataset.py"
    subprocess.run(
        [sys.executable, str(script), "--synthetic", str(synthetic),
         "--real", str(real), "--out", str(out)],
        check=True,
    )

    assert len(list((out / "train" / "images").iterdir())) == 2
    assert len(list((out / "val" / "images").iterdir())) == 2
    assert len(list((out / "test" / "images").iterdir())) == 2
    # remap applied: real labels now use the canonical database index
    remapped = (out / "val" / "labels").glob("*.txt")
    for f in remapped:
        assert f.read_text().startswith(str(COMPONENT_CLASSES.index("database")))
    data = yaml.safe_load((out / "data.yaml").read_text())
    assert data["names"] == COMPONENT_CLASSES
    assert data["nc"] == 15


def test_cli_missing_label_file_fails_clearly(tmp_path):
    synthetic = tmp_path / "synthetic"
    real = tmp_path / "external"
    out = tmp_path / "final"
    _mk_yolo_dir(synthetic, ["s1", "s2"], "5 0.5 0.5 0.2 0.2")
    _mk_yolo_dir(real, ["r1", "r2", "r3", "r4"], "0 0.5 0.5 0.2 0.2")
    (real / "mapping.yaml").write_text("0: database\n", encoding="utf-8")

    # Simulate a Roboflow-style background/negative image with no matching label file.
    Image.new("RGB", (64, 64), "white").save(real / "images" / "r5.jpg")

    script = Path(__file__).resolve().parents[1] / "dataset" / "build_dataset.py"
    result = subprocess.run(
        [sys.executable, str(script), "--synthetic", str(synthetic),
         "--real", str(real), "--out", str(out)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "missing label file for image 'r5'" in result.stderr
    assert "Traceback" not in result.stderr
