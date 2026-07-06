"""Downloads trained weights (best.pt) from a GitHub release asset URL."""
import argparse
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="direct URL to the best.pt release asset")
    parser.add_argument("--out", type=Path, default=Path("models/best.pt"))
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {args.url} -> {args.out}")
    urllib.request.urlretrieve(args.url, args.out)
    print(f"done ({args.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
