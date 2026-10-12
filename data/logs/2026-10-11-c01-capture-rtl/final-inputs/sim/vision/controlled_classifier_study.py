"""Train-only comparison; select on validation, never open the test split."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader

from train_fastener_classifier import CLASSES, FastenerCNN
from train_scene_classifier import SceneCrops
from train_hog_fastener_classifier import load_features, fit, accuracy


def digest_split(root, split):
    digest = hashlib.sha256()
    for path in sorted((root / split).rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engine', choices=['hog', 'cnn'], required=True)
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--augment', action='store_true')
    parser.add_argument('--schedule', choices=['constant', 'cosine'], default='cosine')
    parser.add_argument('--preprocess-mode', choices=['opposite', 'border'], default='opposite')
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error('epochs must be positive')
    if args.engine == 'hog' and args.preprocess_mode != 'opposite':
        parser.error('HOG currently supports opposite preprocessing only')
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    cv2.setNumThreads(1)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    report = {'config': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              'split_sha256': {s: digest_split(args.dataset, s) for s in ['train', 'val']},
              'classes': CLASSES, 'preprocess': f'scene-gray-{args.preprocess_mode}-padding-v1',
              'training_splits': ['train'], 'selection_split': 'val', 'test_read': False,
              'history': []}
    start = time.perf_counter()
    best = -1
    if args.engine == 'hog':
        hog = cv2.HOGDescriptor((64,64), (16,16), (8,8), (8,8), 9)
        train_x, train_y = load_features(args.dataset, 'train', hog)
        val_x, val_y = load_features(args.dataset, 'val', hog)
        for c in (1., 10., 100.):
            for gamma in (.0003, .0006, .0012):
                model = fit(train_x, train_y, c, gamma)
                score, predicted = accuracy(model, val_x, val_y)
                report['history'].append({'C': c, 'gamma': gamma, 'val_accuracy': score})
                if score > best:
                    best = score
                    model.save(str(args.output / 'best.yml'))
                    report['best_config'] = {'C': c, 'gamma': gamma}
        report['train_objects'], report['val_objects'] = len(train_y), len(val_y)
    else:
        train = DataLoader(SceneCrops(args.dataset, 'train', args.augment, 64, args.preprocess_mode), 32, shuffle=True)
        val = DataLoader(SceneCrops(args.dataset, 'val', False, 64, args.preprocess_mode), 64)
        report['train_objects'], report['val_objects'] = len(train.dataset), len(val.dataset)
        model = FastenerCNN()
        optimizer = torch.optim.AdamW(model.parameters(), lr=.001)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, args.epochs, eta_min=.00001)
        for epoch in range(args.epochs):
            model.train()
            for images, labels in train:
                optimizer.zero_grad()
                torch.nn.functional.cross_entropy(model(images), labels).backward()
                optimizer.step()
            model.eval()
            correct = 0
            with torch.no_grad():
                for images, labels in val:
                    correct += (model(images).argmax(1) == labels).sum().item()
            score = correct / len(val.dataset)
            report['history'].append({'epoch': epoch+1, 'val_accuracy': score,
                                      'lr': optimizer.param_groups[0]['lr']})
            if score > best:
                best = score
                report['best_epoch'] = epoch+1
                torch.save({'classes': CLASSES, 'input_size': 64,
                            'architecture': 'fastener-4conv-bn-v1',
                            'preprocess': report['preprocess'],
                            'preprocess_mode': args.preprocess_mode,
                            'state_dict': model.state_dict()}, args.output / 'best.pt')
            if args.schedule == 'cosine':
                scheduler.step()
            print(f'epoch={epoch+1} val_accuracy={score:.4f} best={best:.4f}', flush=True)
    report['best_val_accuracy'] = best
    report['elapsed_seconds'] = time.perf_counter() - start
    (args.output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'history'}), flush=True)


if __name__ == '__main__':
    main()
