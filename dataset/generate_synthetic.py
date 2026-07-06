"""Synthetic architecture-diagram generator.

Places real cloud-provider icons (dropped into dataset/icons/<class>/ by the team)
on a canvas with connector lines and labels. Because the script chooses the
positions, YOLO bounding-box labels are exact and free.
"""
import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw

from strideai.core.models import COMPONENT_CLASSES

BACKGROUNDS = ["#ffffff", "#fafaf7", "#f4f6f8", "#eef2f5"]


def load_icon_library(icons_dir: Path) -> dict[str, list[Path]]:
    library = {}
    for class_dir in sorted(Path(icons_dir).iterdir()):
        if class_dir.is_dir() and class_dir.name in COMPONENT_CLASSES:
            files = sorted(p for p in class_dir.glob("*.png"))
            if files:
                library[class_dir.name] = files
    if not library:
        raise SystemExit(f"no icons found under {icons_dir} — see dataset/icons/README.md")
    return library


def generate_diagram(
    library: dict[str, list[Path]],
    rng: random.Random,
    canvas_size: tuple[int, int] = (1280, 960),
) -> tuple[Image.Image, list[str]]:
    width, height = canvas_size
    image = Image.new("RGB", canvas_size, rng.choice(BACKGROUNDS))
    draw = ImageDraw.Draw(image)

    # grid with jitter: 3-4 columns x 2-3 rows, each cell may hold one icon
    cols, rows = rng.randint(3, 4), rng.randint(2, 3)
    cell_w, cell_h = width // cols, height // rows
    n_components = rng.randint(max(3, min(4, len(library))), cols * rows)

    cells = [(c, r) for c in range(cols) for r in range(rows)]
    rng.shuffle(cells)

    placed: list[tuple[str, tuple[int, int, int, int]]] = []
    labels: list[str] = []
    class_names = list(library.keys())

    for col, row in cells[:n_components]:
        name = rng.choice(class_names)
        icon = Image.open(rng.choice(library[name])).convert("RGBA")
        size = rng.randint(56, min(128, cell_w - 20, cell_h - 20))
        icon = icon.resize((size, size))
        x = col * cell_w + rng.randint(10, max(11, cell_w - size - 10))
        y = row * cell_h + rng.randint(10, max(11, cell_h - size - 10))
        image.paste(icon, (x, y), icon)
        placed.append((name, (x, y, x + size, y + size)))

        cls_idx = COMPONENT_CLASSES.index(name)
        cx, cy = (x + size / 2) / width, (y + size / 2) / height
        labels.append(f"{cls_idx} {cx:.6f} {cy:.6f} {size / width:.6f} {size / height:.6f}")

    # connector lines between consecutive components (drawn under labels)
    for (_, a), (_, b) in zip(placed, placed[1:]):
        ax, ay = (a[0] + a[2]) // 2, (a[1] + a[3]) // 2
        bx, by = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
        draw.line((ax, ay, bx, by), fill="#8a8a8a", width=2)

    # short text captions under icons for realism
    for name, (x1, y1, x2, y2) in placed:
        draw.text((x1, min(height - 12, y2 + 4)), name.replace("_", " "), fill="#333333")

    return image, labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icons", type=Path, default=Path("dataset/icons"))
    parser.add_argument("--out", type=Path, default=Path("dataset/synthetic"))
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    library = load_icon_library(args.icons)
    rng = random.Random(args.seed)
    images_dir, labels_dir = args.out / "images", args.out / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, args.count + 1):
        image, labels = generate_diagram(library, rng)
        stem = f"synth_{i:05d}"
        image.save(images_dir / f"{stem}.jpg", quality=rng.randint(75, 95))
        (labels_dir / f"{stem}.txt").write_text("\n".join(labels), encoding="utf-8")

    print(f"generated {args.count} images in {args.out}")


if __name__ == "__main__":
    main()
