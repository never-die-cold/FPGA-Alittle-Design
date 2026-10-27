"""Small real-ROI development adaptation; training fit is not validation accuracy."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import cv2
import numpy as np
import torch
from export_trained_payload import load_weights, quantized_input

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--weights", type=Path, default=ROOT / "models/cnn-border-fill-best.pt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--balance-classes", action="store_true")
    parser.add_argument("--min-logit-margin", type=float, default=0.0)
    parser.add_argument("--camera-augment", action="store_true")
    parser.add_argument("--select-training-fit", action="store_true",
                        help="development checkpoint selection by training fit, not validation accuracy")
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT not in output.parents or output.exists() or args.epochs < 1 or args.lr <= 0:
        parser.error("use a new output directory inside the repository and positive training options")
    annotations = json.loads(args.annotations.read_text(encoding="utf-8"))
    if annotations["annotation_status"] != "HUMAN_CONFIRMED":
        parser.error("per-object labels require human confirmation")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(4)
    model, meta = load_weights(args.weights)
    pixels, labels, samples = [], [], []
    for frame in annotations["frames"]:
        folder = (ROOT / frame["comparison_source"]).resolve().parent
        if ROOT not in folder.parents:
            parser.error("ROI source escapes repository")
        for target in frame["targets"]:
            path = folder / f"roi-{target['index']:02d}.png"
            canvas = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if canvas is None or canvas.shape != (64, 64):
                raise ValueError(f"invalid preprocessed ROI: {path}")
            if hashlib.sha256(quantized_input(canvas).tobytes()).hexdigest() != target["roi_sha256"]:
                raise ValueError(f"ROI provenance mismatch: {path}")
            pixels.append(canvas)
            labels.append(meta["classes"].index(target["class_label"]))
            samples.append({"roi": path.relative_to(ROOT).as_posix(), "class": target["class_label"]})
    x = torch.from_numpy(np.asarray(pixels, np.float32)[:, None] / 255)
    y = torch.tensor(labels, dtype=torch.long)
    class_counts = np.bincount(labels, minlength=len(meta["classes"]))
    if args.balance_classes and np.any(class_counts == 0):
        raise ValueError("class balancing requires examples of all classes")
    class_weights = (torch.tensor(len(labels)/(len(class_counts)*class_counts), dtype=torch.float32)
                     if args.balance_classes else None)
    output.mkdir(parents=True)
    # Frozen BN running statistics avoid recalibrating from this tiny batch.
    model.eval()
    def measure():
        with torch.no_grad():
            clean_logits = model(x)
            prediction = clean_logits.argmax(1)
        return {"correct": int((prediction == y).sum()), "total": len(labels),
                "predictions": prediction.tolist(),
                "cross_entropy": float(torch.nn.functional.cross_entropy(clean_logits, y))}
    before = measure()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0001)
    loss_fn, history = torch.nn.CrossEntropyLoss(weight=class_weights), []
    best_state, best_key, selected_epoch = None, None, args.epochs
    for epoch in range(1, args.epochs + 1):
        augmented = []
        for canvas in pixels:
            matrix = cv2.getRotationMatrix2D((31.5, 31.5), random.uniform(-180, 180), 1.0)
            fill = int(np.median(np.concatenate((canvas[0], canvas[-1]))))
            sample = cv2.warpAffine(canvas, matrix, (64, 64), borderValue=fill)
            if args.camera_augment:
                sample = fill + (sample.astype(np.float32)-fill) * random.uniform(0.35, 1.2)
                if random.random() < 0.3:
                    sample = cv2.GaussianBlur(sample, (3, 3), 0)
            sample = np.clip(sample.astype(np.float32) * random.uniform(0.85, 1.15), 0, 255)
            augmented.append(sample)
        batch = torch.cat((x, torch.from_numpy(np.asarray(augmented)[:, None] / 255)))
        optimizer.zero_grad()
        batch_labels = torch.cat((y, y))
        logits = model(batch)
        loss = loss_fn(logits, batch_labels)
        if args.min_logit_margin > 0:
            correct = logits.gather(1, batch_labels[:, None]).squeeze(1)
            alternatives = logits.masked_fill(torch.nn.functional.one_hot(batch_labels, len(meta["classes"])).bool(), -1e9).max(1).values
            penalty = torch.relu(args.min_logit_margin - correct + alternatives)
            if class_weights is not None:
                penalty = penalty * class_weights[batch_labels]
            loss = loss + 0.25 * penalty.mean()
        loss.backward()
        optimizer.step()
        if epoch == 1 or epoch % 10 == 0 or epoch == args.epochs:
            row = {"epoch": epoch, "loss": float(loss.detach()), "training_fit": measure()}
            history.append(row)
            print(json.dumps(row), flush=True)
            key = (row["training_fit"]["correct"], -row["training_fit"]["cross_entropy"])
            if args.select_training_fit and (best_key is None or key > best_key):
                best_key, selected_epoch = key, epoch
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    last_fit = measure()
    if best_state is not None:
        model.load_state_dict(best_state)
    report = {"kind": "DEVELOPMENT_ADAPTATION", "formal_validation": False,
              "seed": args.seed, "epochs": args.epochs, "lr": args.lr, "bn_statistics": "FROZEN",
              "class_counts": class_counts.tolist(), "balanced_classes": args.balance_classes,
              "min_logit_margin": args.min_logit_margin,
              "camera_augmentation": args.camera_augment,
              "selected_epoch": selected_epoch, "selection": "TRAIN_FIT" if args.select_training_fit else "LAST_EPOCH",
              "last_epoch_training_fit": last_fit,
              "annotations_sha256": hashlib.sha256(args.annotations.read_bytes()).hexdigest(),
              "initial_weights_sha256": hashlib.sha256(args.weights.read_bytes()).hexdigest(),
              "samples": samples, "before": before, "after": measure(), "history": history}
    torch.save({**meta, "state_dict": model.state_dict(), "training": report}, output / "fp32.pt")
    report["weights_sha256"] = hashlib.sha256((output / "fp32.pt").read_bytes()).hexdigest()
    (output / "training.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("TRAINING_COMPLETE " + json.dumps({"before": before, "after": report["after"]}), flush=True)


if __name__ == "__main__":
    main()
