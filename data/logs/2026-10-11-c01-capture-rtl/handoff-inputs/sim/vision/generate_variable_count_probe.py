"""Development-only variable-count scenes and empty backgrounds from val crops."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from localization_data import compose_scene, save_yolo_scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True, help='val/seed-53 directory')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(20261007)
    classes = {'bolt': 0, 'nut': 1, 'washer': 2}
    pools = {c: sorted((args.cache/c).glob('*.png')) for c in classes}
    manifest = []
    for index in range(60):
        parts, sources = [], []
        if index >= 20:
            for _ in range(int(rng.integers(1,9))):
                label = str(rng.choice(list(classes)))
                path = pools[label][int(rng.integers(len(pools[label])))]
                with Image.open(path) as image:
                    parts.append((label, np.asarray(image.convert('RGBA'))))
                sources.append(str(path))
            pixels, labels = compose_scene(parts, seed=80000+index)
            group = 'variable'
        else:
            level = int(rng.integers(24,180))
            background = np.full((720,1280), level, dtype=np.float32)
            if index >= 10:
                background += np.linspace(-20,50,1280)[None,:]
            pixels = np.repeat(np.clip(background, 0,255).astype(np.uint8)[:,:,None], 3, axis=2)
            labels = []
            group = 'empty-gradient' if index >= 10 else 'empty-uniform'
        stem = f'{group}-{index:03d}'
        save_yolo_scene(args.output, stem, pixels, labels, classes)
        manifest.append({'stem': stem, 'group': group, 'objects': len(labels), 'sources': sources})
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Generated {len(manifest)} development scenes; never use as independent final test.')


if __name__ == '__main__':
    main()
