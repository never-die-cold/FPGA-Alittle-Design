"""Build reproducible synthetic YOLO scenes from Solidworks fastener crops."""

import argparse
from pathlib import Path

from localization_data import cache_split_crops, generate_yolo_scenes_from_cache


CLASS_TO_ID = {"bolt": 0, "nut": 1, "washer": 2, "locatingpin": 3}
SPLITS = ("train", "val", "test")


def generate_dataset(dataset_root, cache_root, output_root, seed=2026,
                     per_class_crops=100, scenes_per_split=100,
                     objects_per_scene=6, canvas_size=(1280, 720),
                     class_to_id=None):
    """Cache each source split, generate balanced scenes, and write YOLO config."""
    class_to_id = class_to_id or CLASS_TO_ID
    if min(seed, per_class_crops, scenes_per_split, objects_per_scene, *canvas_size) < 1:
        raise ValueError("seed, counts, and image dimensions must be positive")
    cache_root, run_root = Path(cache_root), Path(output_root) / f"seed-{seed}"
    for split_index, split in enumerate(SPLITS):
        cache_seed = seed + split_index
        cache_dir = cache_root / split / f"seed-{cache_seed}"
        counts = {name: len(list((cache_dir / name).glob("*.png"))) for name in class_to_id}
        if all(count >= per_class_crops for count in counts.values()):
            print(f"{split}: reusing crop cache")
        else:
            counts = cache_split_crops(dataset_root, cache_root, split, per_class_crops, cache_seed)
        missing = set(class_to_id) - set(counts)
        if missing:
            raise ValueError(f"{split} split has no crops for classes: {sorted(missing)}")
        stems = generate_yolo_scenes_from_cache(
            cache_root, run_root, split, cache_seed, seed + split_index * scenes_per_split,
            scenes_per_split, objects_per_scene, class_to_id, canvas_size)
        print(f"{split}: cached={counts}, generated={len(stems)} scenes")

    names = "\n".join(f"  {class_id}: {name}" for name, class_id in class_to_id.items())
    run_root.mkdir(parents=True, exist_ok=True)
    dataset_path = run_root.resolve().as_posix().replace("'", "''")
    config = f"path: '{dataset_path}'\ntrain: train/images\nval: val/images\ntest: test/images\nnames:\n{names}\n"
    (run_root / "dataset.yaml").write_text(config, encoding="utf-8")
    return run_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, help="Solidworks dataset directory")
    parser.add_argument("--cache-root", required=True, help="where extracted RGBA crops are stored")
    parser.add_argument("--output-root", required=True, help="where the synthetic YOLO dataset is stored")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--per-class-crops", type=int, default=100)
    parser.add_argument("--scenes-per-split", type=int, default=100)
    parser.add_argument("--objects-per-scene", type=int, default=6)
    parser.add_argument("--classes", nargs="+", choices=tuple(CLASS_TO_ID), default=None)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()
    classes = args.classes or list(CLASS_TO_ID)
    class_to_id = {name: index for index, name in enumerate(classes)}
    result = generate_dataset(args.dataset_root, args.cache_root, args.output_root,
                              args.seed, args.per_class_crops, args.scenes_per_split,
                              args.objects_per_scene, (args.width, args.height), class_to_id)
    print(f"YOLO dataset config: {result / 'dataset.yaml'}")


if __name__ == "__main__":
    main()
