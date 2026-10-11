"""Train a small Ultralytics CNN detector on generated fastener scenes."""

import argparse
from pathlib import Path

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="dataset.yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="pretrained model or model yaml")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--name", default="fastener-cnn")
    args = parser.parse_args()
    if min(args.epochs, args.imgsz, args.batch) < 1:
        parser.error("epochs, imgsz, and batch must be positive")
    model = YOLO(args.model)
    run_dir = args.project.resolve() / args.name
    model.train(data=str(args.data.resolve()), epochs=args.epochs,
                imgsz=args.imgsz, batch=args.batch, device="cpu",
                project=str(args.project.resolve()), name=args.name,
                exist_ok=True, workers=0)
    print(f"best_weights={run_dir / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
