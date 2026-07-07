"""Extracts the two evaluation architecture figures from the challenge PDF."""
from pathlib import Path

import fitz  # pymupdf

PDF = Path("doc/IADT - Fase 5 - Hackaton.pdf")
OUT = Path("tests/fixtures")

MIN_BYTES = 30_000  # skip logos/decoration; the figures are large embedded images


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[2]  # page 3 (0-indexed) holds Figura 1 and Figura 2
    saved = 0
    for xref, *_ in page.get_images(full=True):
        data = doc.extract_image(xref)
        if len(data["image"]) < MIN_BYTES:
            continue
        saved += 1
        out = OUT / f"eval_arch{saved}.png"
        out.write_bytes(data["image"])
        print(f"saved {out} ({len(data['image']) / 1024:.0f} KB)")
    if saved < 2:
        raise SystemExit(f"expected 2 figures, extracted {saved} — inspect the PDF pages")


if __name__ == "__main__":
    main()
