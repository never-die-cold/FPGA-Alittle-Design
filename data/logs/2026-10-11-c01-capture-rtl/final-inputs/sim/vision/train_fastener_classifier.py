"""Train the planned 4-convolution, 64x64 grayscale fastener classifier."""

import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

CLASSES = ("bolt", "nut", "washer")


class CachedCrops(Dataset):
    def __init__(self, root, split, seed, augment=False):
        self.files = [(path, label) for label, name in enumerate(CLASSES)
                      for path in sorted((root / split / f"seed-{seed}" / name).glob("*.png"))]
        self.augment = augment
        if not self.files:
            raise ValueError(f"no cached crops for {split}")

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        path, label = self.files[index]
        rgba = Image.open(path).convert("RGBA")
        if self.augment:
            factor = random.uniform(0.55, 0.90)
            rgba.thumbnail((round(54 * factor), round(54 * factor)), Image.Resampling.LANCZOS)
            rgba = rgba.rotate(random.uniform(0, 360), resample=Image.Resampling.BICUBIC, expand=True)
            if max(rgba.size) > 60:
                rgba.thumbnail((60, 60), Image.Resampling.LANCZOS)
            pixels = np.asarray(rgba)
            gray = np.asarray(rgba.convert("L"), dtype=np.float32)
            mean = gray[pixels[:, :, 3] > 127].mean()
            level = random.randint(24, 84) if mean > 128 else random.randint(168, 232)
            background = Image.new("RGBA", (64, 64), (level, level, level, 255))
            rgba = ImageEnhance.Brightness(rgba).enhance(random.uniform(0.8, 1.2))
            background.alpha_composite(rgba, ((64-rgba.width)//2, (64-rgba.height)//2))
        else:
            rgba.thumbnail((42, 42), Image.Resampling.LANCZOS)
            pixels = np.asarray(rgba)
            gray = np.asarray(rgba.convert("L"), dtype=np.float32)
            mean = gray[pixels[:, :, 3] > 127].mean()
            level = 50 if mean > 128 else 205
            background = Image.new("RGBA", (64, 64), (level, level, level, 255))
            rgba.thumbnail((60, 60), Image.Resampling.LANCZOS)
            background.alpha_composite(rgba, ((64-rgba.width)//2, (64-rgba.height)//2))
        pixels = np.asarray(background.convert("L"), dtype=np.float32) / 255
        return torch.from_numpy(pixels[None]), label


class FastenerCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(16), nn.ReLU(),
            nn.Conv2d(16, 32, 3, padding=1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, 3))

    def forward(self, image):
        return self.features(image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("epochs must be positive")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(4)
    train = DataLoader(CachedCrops(args.cache_root, "train", args.seed, True), 32, shuffle=True)
    val = DataLoader(CachedCrops(args.cache_root, "val", args.seed + 1), 64)
    test = DataLoader(CachedCrops(args.cache_root, "test", args.seed + 2), 64)
    model = FastenerCNN()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0005)
    loss_fn = nn.CrossEntropyLoss()
    best, best_state = -1.0, None
    for epoch in range(args.epochs):
        model.train()
        train_correct = train_total = 0
        for images, labels in train:
            optimizer.zero_grad()
            logits = model(images)
            loss_fn(logits, labels).backward()
            optimizer.step()
            train_correct += (logits.argmax(1) == labels).sum().item()
            train_total += labels.numel()
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for images, labels in val:
                correct += (model(images).argmax(1) == labels).sum().item()
                total += labels.numel()
        accuracy = correct / total
        print(f"epoch={epoch+1}/{args.epochs} train_accuracy={train_correct/train_total:.4f} val_accuracy={accuracy:.4f}")
        if accuracy > best:
            best, best_state = accuracy, {key: value.clone() for key, value in model.state_dict().items()}
    model.load_state_dict(best_state)
    model.eval()
    correct = total = 0
    confusion = torch.zeros(len(CLASSES), len(CLASSES), dtype=torch.int64)
    with torch.no_grad():
        for images, labels in test:
            predictions = model(images).argmax(1)
            correct += (predictions == labels).sum().item()
            for truth, prediction in zip(labels, predictions):
                confusion[truth, prediction] += 1
            total += labels.numel()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"classes": CLASSES, "state_dict": model.state_dict()}, args.output)
    print(f"test_accuracy={correct/total:.4f} best_val_accuracy={best:.4f} weights={args.output.resolve()}")
    print("test_confusion_rows=true_cols=predicted:", confusion.tolist())


if __name__ == "__main__":
    main()
