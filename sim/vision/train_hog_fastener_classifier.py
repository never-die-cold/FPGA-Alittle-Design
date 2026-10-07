"""Tune an OpenCV HOG+SVM crop classifier on validation scenes."""

import argparse
from pathlib import Path

import cv2
import numpy as np

from train_scene_classifier import CLASSES, preprocess


def load_features(root, split, hog):
    features, labels = [], []
    for path in sorted((root / split / "images").glob("*.png")):
        image = cv2.imread(str(path)); height, width = image.shape[:2]
        label_path = root / split / "labels" / f"{path.stem}.txt"
        for line in label_path.read_text(encoding="utf-8").splitlines():
            class_id, cx, cy, bw, bh = map(float, line.split()); class_id = int(class_id)
            if class_id >= len(CLASSES):
                continue
            box = (round((cx-bw/2)*width), round((cy-bh/2)*height),
                   round((cx+bw/2)*width), round((cy+bh/2)*height))
            crop, _ = preprocess(image, box, 64)
            features.append(hog.compute(crop).reshape(-1))
            labels.append(class_id)
    return np.asarray(features, np.float32), np.asarray(labels, np.int32)


def fit(features, labels, c_value, gamma):
    model = cv2.ml.SVM_create()
    model.setType(cv2.ml.SVM_C_SVC); model.setKernel(cv2.ml.SVM_RBF)
    model.setC(c_value); model.setGamma(gamma)
    model.train(features, cv2.ml.ROW_SAMPLE, labels)
    return model


def accuracy(model, features, labels):
    predicted = model.predict(features)[1].reshape(-1).astype(np.int32)
    return float(np.mean(predicted == labels)), predicted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    hog = cv2.HOGDescriptor((64,64), (16,16), (8,8), (8,8), 9)
    train_x, train_y = load_features(args.train, "train", hog)
    val_x, val_y = load_features(args.train, "val", hog)
    test_x, test_y = load_features(args.test, "test", hog)
    best, best_params = -1.0, None
    for c_value in (1.0, 10.0, 100.0):
        for gamma in (0.0003, 0.0006, 0.0012):
            candidate = fit(train_x, train_y, c_value, gamma)
            score, _ = accuracy(candidate, val_x, val_y)
            print(f"C={c_value:g} gamma={gamma:g} val_accuracy={score:.4f}")
            if score > best:
                best, best_params = score, (c_value, gamma)
    final = fit(np.concatenate((train_x, val_x)), np.concatenate((train_y, val_y)), *best_params)
    score, predicted = accuracy(final, test_x, test_y)
    confusion = np.zeros((len(CLASSES), len(CLASSES)), dtype=np.int64)
    np.add.at(confusion, (test_y, predicted), 1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    final.save(str(args.output))
    print(f"test_accuracy={score:.4f} val_best={best:.4f} params={best_params}")
    print("confusion rows=true cols=predicted:", confusion.tolist())


if __name__ == "__main__":
    main()
