"""Generate golden crops + PC torch softmax oracle for the board numpy check.

Draws two 64x64 uint8 crops from the frozen dataset fixture (dataset/seed-7
cached crops if present, else deterministic synthetic gradients repeated
across class channels), runs them through the real FastenerCNN in eval mode
(PrototypeClassifier path), saves crops+names into NPZ and the checkpoint
sha/class/score/probabilities into gold JSON. The NPZ and JSON are UART-
uploaded to the board where c01_board_cnn.py reproduces the same softmax with
pure NumPy folded layers and asserts agreement within rtol 2e-5 / atol 1e-4.
"""
import hashlib
import io
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'sim/vision'))
sys.path.insert(0, str(ROOT / 'src/pynq_host'))
import torch
from train_fastener_classifier import CLASSES, FastenerCNN
from roi_preprocess import PREPROCESS_VERSION

WEIGHTS = ROOT / 'models/cnn-border-fill-best.pt'
OUTPUT = Path(__file__).resolve().parent / 'cnn_board_package.npz'
CROPS_NPZ = Path(__file__).resolve().parent / 'golden_crops.npz'
CROPS_META = Path(__file__).resolve().parents[0] / 'golden_crops_meta.json'
BOARDDIR = Path(str(ROOT)) / 'data/logs/2026-10-16-c01-park-first-board'


def build_crops():
    paths = [path for name in CLASSES for path in
             sorted((ROOT / 'dataset/crops/train/seed-7' / name).glob('*.png'))]
    if not paths:
        # Four structurally distinct 64x64 crops at realistic gray levels:
        # mid-level gradient, dark disk on mid background, bright hexagon on
        # mid background, high-frequency noise; the model must place them
        # somewhere and PC/board must agree regardless of correctness.
        y, x = np.mgrid[0:64, 0:64].astype(np.float32)
        gradient = (y * 2 + x).astype(np.uint8)
        disk = np.full((64, 64), 128, np.uint8)
        disk[(y - 32) ** 2 + (x - 32) ** 2 < 400] = 24
        hexagon = disk.copy()
        hexagon[(np.abs(x - 32) * 0.9 + np.abs(y - 32)) < 18] = 210
        rng = np.random.default_rng(20261016)
        noise = rng.integers(48, 208, size=(64, 64), dtype=np.uint8)
        images = np.stack([gradient, disk, hexagon, noise])
        names = ['gradient', 'dark_disk', 'bright_hexagon', 'mid_noise']
    else:
        from PIL import Image
        picks = [paths[i] for i in (0, len(paths)//2, -1)][:3]
        names = [p.parent.name + '/' + p.name for p in picks]
        images = [np.asarray(Image.open(p).convert('L'), dtype=np.uint8) for p in picks]
    return np.asarray(images, dtype=np.uint8), names


def main():
    raw = WEIGHTS.read_bytes()
    checkpoint = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
    model = FastenerCNN()
    model.load_state_dict(checkpoint['state_dict'], strict=True)
    model.eval()
    crops, names = build_crops()
    package = np.load(OUTPUT)
    if package['checkpoint_sha256'].item() != hashlib.sha256(raw).hexdigest():
        raise RuntimeError('NPZ/exported checkpoint identity differs; regenerate both')
    images = torch.from_numpy(crops.astype(np.float32)[:, None] / 255)
    with torch.inference_mode():
        probabilities = model(images).softmax(dim=1)
    if not torch.isfinite(probabilities).all():
        raise RuntimeError('nonfinite torch output')
    results = [{'name': names[i], 'class': CLASSES[int(row.argmax())],
                'score': float(row.max()), 'probabilities': [float(v) for v in row]}
               for i, row in enumerate(probabilities)]
    np.savez(CROPS_NPZ, crops=crops, names=np.array(names, dtype='U64'))
    CROPS_META.write_text(json.dumps({
        'checkpoint_sha256': hashlib.sha256(raw).hexdigest(),
        'architecture': checkpoint['architecture'],
        'preprocess': str(PREPROCESS_VERSION),
        'classes': list(CLASSES),
        'results': results}, indent=2))
    print(json.dumps(results, indent=2))
    print('NPZ:', CROPS_NPZ, CROPS_NPZ.stat().st_size, hashlib.sha256(CROPS_NPZ.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
