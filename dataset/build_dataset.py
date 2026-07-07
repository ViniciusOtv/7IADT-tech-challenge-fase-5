"""Merges synthetic + real annotated data into the final YOLO dataset.

Split policy (per the design spec): synthetic images go to train; real
hand-annotated images are split 50/50 into val and test so reported metrics
reflect grader-style diagrams.
"""
import argparse
import shutil
from pathlib import Path

import yaml

from strideai.core.models import COMPONENT_CLASSES


def remap_label_line(line: str, mapping: dict[int, str]) -> str | None:
    parts = line.split()
    src_idx = int(parts[0])
    target = mapping.get(src_idx)
    if target is None:
        return None
    return " ".join([str(COMPONENT_CLASSES.index(target)), *parts[1:]])


def _copy_pairs(src: Path, dst: Path, stems: list[str], mapping: dict[int, str] | None) -> None:
    (dst / "images").mkdir(parents=True, exist_ok=True)
    (dst / "labels").mkdir(parents=True, exist_ok=True)
    for stem in stems:
        image = next((src / "images").glob(f"{stem}.*"))
        shutil.copy2(image, dst / "images" / image.name)
        label_file = src / "labels" / f"{stem}.txt"
        if not label_file.exists():
            raise SystemExit(
                f"missing label file for image '{stem}' (expected {label_file}) — "
                f"every image must have a matching .txt label; if this is meant to be "
                f"a background/negative image, create an empty {label_file.name}"
            )
        lines = label_file.read_text(encoding="utf-8").splitlines()
        if mapping is not None:
            lines = [remapped for line in lines if (remapped := remap_label_line(line, mapping))]
        (dst / "labels" / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")


def _stems(root: Path) -> list[str]:
    return sorted(p.stem for p in (root / "images").iterdir())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", type=Path, default=Path("dataset/synthetic"))
    parser.add_argument("--real", type=Path, default=Path("dataset/external"))
    parser.add_argument("--out", type=Path, default=Path("dataset/final"))
    args = parser.parse_args()

    mapping = None
    mapping_file = args.real / "mapping.yaml"
    if mapping_file.exists():
        mapping = {int(k): v for k, v in yaml.safe_load(mapping_file.read_text()).items()}

    _copy_pairs(args.synthetic, args.out / "train", _stems(args.synthetic), mapping=None)

    real_stems = _stems(args.real)
    half = len(real_stems) // 2
    _copy_pairs(args.real, args.out / "val", real_stems[:half], mapping)
    _copy_pairs(args.real, args.out / "test", real_stems[half:], mapping)

    data = {
        "path": str(args.out.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(COMPONENT_CLASSES),
        "names": COMPONENT_CLASSES,
    }
    (args.out / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"dataset written to {args.out}")


if __name__ == "__main__":
    main()
