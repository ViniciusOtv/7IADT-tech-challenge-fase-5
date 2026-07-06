"""Fine-tunes YOLO11s on the architecture-component dataset.

Run locally with a GPU or on Google Colab (see training/README.md).
Settings follow the design spec: high imgsz (small icons), no vertical flips,
no heavy HSV shifts (icons are orientation- and color-meaningful).
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="dataset/final/data.yaml")
    parser.add_argument("--model", default="yolo11s.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--name", default="strideai")
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        name=args.name,
        patience=20,          # early stopping
        flipud=0.0,           # no vertical flips: icons are orientation-meaningful
        hsv_h=0.005,          # minimal hue shift: icon colors carry meaning
        hsv_s=0.2,
        close_mosaic=10,      # disable mosaic for the final epochs
    )
    metrics = model.val(data=args.data, split="test", imgsz=args.imgsz)
    print(f"test mAP50: {metrics.box.map50:.4f}")
    print("weights at:", f"runs/detect/{args.name}/weights/best.pt")


if __name__ == "__main__":
    main()
