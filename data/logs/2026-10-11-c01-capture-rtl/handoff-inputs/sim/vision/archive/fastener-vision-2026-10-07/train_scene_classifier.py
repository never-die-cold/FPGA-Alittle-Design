"""Train the hardware-sized crop CNN using crops from composite scenes."""

import argparse
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from train_fastener_classifier import CLASSES, FastenerCNN


def preprocess(image, box, input_size, mode='opposite'):
    x0, y0, x1, y1 = box
    crop = cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    height, width = crop.shape
    object_size = round(input_size * 0.65625)
    scale = min(object_size / width, object_size / height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    crop = cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
    level = 50 if float(crop.mean()) > 128 else 205
    if mode == 'border':
        level = int(np.median(np.concatenate((crop[0], crop[-1], crop[:,0], crop[:,-1]))))
    elif mode != 'opposite':
        raise ValueError(f'unknown preprocessing: {mode}')
    canvas = np.full((input_size, input_size), level, dtype=np.uint8)
    y, x = (input_size-size[1])//2, (input_size-size[0])//2
    canvas[y:y+size[1], x:x+size[0]] = crop
    return canvas, level


class SceneCrops(Dataset):
    def __init__(self, root, split, augment=False, input_size=64, mode='opposite'):
        self.items, self.augment, self.input_size = [], augment, input_size
        for path in sorted((root / split / "images").glob("*.png")):
            image = cv2.imread(str(path))
            height, width = image.shape[:2]
            label_path = root / split / "labels" / f"{path.stem}.txt"
            for line in label_path.read_text(encoding="utf-8").splitlines():
                class_id, cx, cy, bw, bh = map(float, line.split())
                class_id = int(class_id)
                if class_id >= len(CLASSES):
                    continue
                box = (round((cx-bw/2)*width), round((cy-bh/2)*height),
                       round((cx+bw/2)*width), round((cy+bh/2)*height))
                canvas, level = preprocess(image, box, input_size, mode)
                self.items.append((canvas, class_id, level))
        if not self.items:
            raise ValueError(f"no target crops in {split}")

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        pixels, label, level = self.items[index]
        image = Image.fromarray(pixels)
        if self.augment:
            if random.random() < 0.5:
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            image = image.rotate(random.uniform(0, 360), fillcolor=level)
            image = ImageEnhance.Brightness(image).enhance(random.uniform(0.8, 1.2))
        array = np.asarray(image, dtype=np.float32) / 255
        return torch.from_numpy(array[None]), label


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--input-size", type=int, choices=(64, 96), default=64)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    random.seed(2026)
    torch.manual_seed(2026)
    torch.set_num_threads(4)
    train = DataLoader(SceneCrops(args.dataset, "train", True, args.input_size), 32, shuffle=True)
    val = DataLoader(SceneCrops(args.dataset, "val", input_size=args.input_size), 64)
    test = DataLoader(SceneCrops(args.dataset, "test", input_size=args.input_size), 64)
    model = FastenerCNN()
    optimizer, loss_fn = torch.optim.AdamW(model.parameters(), lr=0.001), nn.CrossEntropyLoss()
    best, best_state = -1.0, None
    for epoch in range(args.epochs):
        model.train()
        for images, labels in train:
            optimizer.zero_grad()
            loss_fn(model(images), labels).backward()
            optimizer.step()
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for images, labels in val:
                correct += (model(images).argmax(1) == labels).sum().item()
                total += labels.numel()
        accuracy = correct / total
        print(f"epoch={epoch+1}/{args.epochs} val_accuracy={accuracy:.4f}")
        if accuracy > best:
            best, best_state = accuracy, {key: value.clone() for key, value in model.state_dict().items()}
    model.load_state_dict(best_state)
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for images, labels in test:
            correct += (model(images).argmax(1) == labels).sum().item()
            total += labels.numel()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"classes": CLASSES, "input_size": args.input_size,
                "state_dict": model.state_dict()}, args.output)
    print(f"test_accuracy={correct/total:.4f} best_val_accuracy={best:.4f} weights={args.output.resolve()}")


if __name__ == "__main__":
    main()
