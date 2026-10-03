#!/usr/bin/env python3
"""文件输入 ARM 定位基线；计时仅覆盖定位/裁剪，不含文件 I/O。"""
import argparse
import hashlib
import json
import platform
import sys
import tempfile
import time
from pathlib import Path

reference_dir = Path(__file__).resolve().parents[2] / "data/golden/vision/localize"
if not (reference_dir / "reference.py").is_file():
    reference_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(reference_dir))
import reference


def export_crops(crops, output):
    """保存独立批次目录；仅结果 JSON 清单中的文件属于本次结果。"""
    if not crops:
        return []
    folder = Path(tempfile.mkdtemp(prefix=output.stem + "-crops-", dir=output.parent))
    artifacts = []
    for target in crops:
        width, height = target["input_size"]
        pixels = bytes(p for row in target["pixels"] for p in row)
        pgm = f"P5\n{width} {height}\n255\n".encode("ascii") + pixels
        hex_data = "".join(f"{p:02x}\n" for p in pixels).encode("ascii")
        files = {}
        for extension, content in (("pgm", pgm), ("hex", hex_data)):
            path = folder / f"target_{target['target_id']:03d}.{extension}"
            path.write_bytes(content)
            files[extension] = {"path": path.relative_to(output.parent).as_posix(),
                                "sha256": hashlib.sha256(content).hexdigest()}
        artifacts.append({"target_id": target["target_id"], "frame_id": target["frame_id"],
                          "config_id": target["config_id"], "bbox": target["bbox"],
                          "pixel_format": "GRAY8", "size": [width, height], **files})
    return artifacts


def run(source, output, size=(64, 64), frame_id=1, config_id=0,
        threshold=96, min_area=8, max_targets=16):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("input and output must differ")
    if min(size) < 1 or frame_id < 0 or config_id < 0:
        raise ValueError("invalid output size or frame/config ID")
    raw = source.read_bytes()
    image = json.loads(raw)["pixels"]
    if not isinstance(image, list) or any(
            not isinstance(row, list) or any(type(p) is not int for p in row) for row in image):
        raise ValueError("GRAY8 pixels must be integer rows")
    start = time.perf_counter_ns()
    result = reference.locate(image, frame_id, config_id, threshold, min_area, max_targets)
    located = time.perf_counter_ns()
    crops = reference.prepare_targets(image, result, *size) if result["status"] == "LOCATION_ONLY" else []
    finished = time.perf_counter_ns()
    result.update(
        schema_version=1, mode="FILE_REFERENCE", crops=crops, crop_size=list(size),
        source={"name": source.name, "sha256": hashlib.sha256(raw).hexdigest()},
        parameters={"threshold": threshold, "min_area": min_area, "max_targets": max_targets},
        runtime={"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()},
        reference_sha256=hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
        timing_ms={"locate": (located-start)/1e6, "crop": (finished-located)/1e6})
    output.parent.mkdir(parents=True, exist_ok=True)
    result["artifacts"] = export_crops(crops, output)
    pending_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         prefix=output.name + "-", suffix=".pending", delete=False) as pending:
            pending_path = Path(pending.name)
            pending.write(json.dumps(result, indent=2) + "\n")
        pending_path.replace(output)
    finally:
        if pending_path is not None:
            pending_path.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, nargs=2, default=(64, 64), metavar=("WIDTH", "HEIGHT"))
    for name, default in (("frame-id", 1), ("config-id", 0), ("threshold", 96), ("min-area", 8), ("max-targets", 16)):
        parser.add_argument("--" + name, type=int, default=default)
    try:
        result = run(**vars(parser.parse_args()))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: file reference status={result['status']} targets={len(result['targets'])} crops={len(result['crops'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
