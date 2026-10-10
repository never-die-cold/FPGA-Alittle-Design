"""Repository file replay runner with source/model/config/code provenance."""
import json
import argparse
import platform
import re
import sys
import time
from pathlib import Path
import cv2
import numpy as np

from inspection_artifacts import digest, save_bytes, save_png, load_existing
from inspection_model import PrototypeClassifier
from inspection_replay import inspect_frame, annotate
from inspection_rules import judge


def run(source, weights, order, output, request_id, min_score, max_targets=16):
    if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", request_id):
        raise ValueError("request ID must contain 1-64 ASCII letters, digits, hyphens or underscores")
    judge([], order, min_score, max_targets)
    source, output = Path(source).resolve(), Path(output).resolve()
    raw = source.read_bytes()
    classifier = PrototypeClassifier(weights)
    root = Path(__file__).resolve().parents[2]
    code_paths = ["src/pynq_host/" + name + ".py" for name in
                  ("inspection_run", "inspection_replay", "inspection_rules", "inspection_model",
                   "inspection_artifacts", "roi_preprocess")]
    code_paths += ["sim/vision/localization_opencv.py", "sim/vision/train_fastener_classifier.py"]
    provenance = {"source_sha256": digest(raw), "model": classifier.metadata,
                  "order": order, "min_score": min_score, "max_targets": max_targets,
                  "code_sha256": {name: digest((root / name).read_bytes()) for name in code_paths},
                  "runtime": {"python": platform.python_version(), "opencv": cv2.__version__,
                              "numpy": np.__version__, "torch": str(sys.modules["torch"].__version__)}}
    fingerprint = digest(json.dumps(provenance, sort_keys=True).encode())
    folder = output / request_id
    if folder.exists():
        return load_existing(folder, fingerprint)
    frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("source file is not a decodable color image")
    start = time.perf_counter_ns()
    result, crops = inspect_frame(frame, classifier, order, min_score, max_targets)
    result.update(request_id=request_id, request_fingerprint=fingerprint, provenance=provenance,
                  source_name=source.name, replay_elapsed_ms=(time.perf_counter_ns() - start) / 1e6,
                  timing_scope="localization/ROI/inference/rules; excludes load and file IO")
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = [save_bytes(folder, "source.bin", raw), save_png(folder, "frame.png", frame),
                 save_png(folder, "annotated.png", annotate(frame, result))]
    for target, crop in zip(result["targets"], crops):
        name = f"roi_{target['target_id']:03d}"
        artifacts.append(save_png(folder, name + ".png", crop))
        artifacts.append(save_bytes(folder, name + ".hex", "".join(f"{p:02x}\n" for p in crop.flat).encode()))
        target.update(roi_path=name + ".png", roi_pixels_sha256=digest(crop.tobytes()))
    result["artifacts"] = artifacts
    payload = (json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    (folder / "result.pending").write_bytes(payload)
    (folder / "result.sha256").write_text(digest(payload) + "\n", encoding="ascii")
    (folder / "result.pending").replace(folder / "result.json")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="each request creates one checked subdirectory")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--order", type=int, nargs=3, required=True, metavar=("BOLT", "NUT", "WASHER"))
    parser.add_argument("--min-score", type=float, required=True, help="candidate threshold, not validated accuracy")
    parser.add_argument("--max-targets", type=int, default=16)
    args = vars(parser.parse_args())
    args["order"] = dict(zip(("bolt", "nut", "washer"), args["order"]))
    try:
        result = run(**args)
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    decision = result["decision"]
    print(f"FILE_REPLAY: {decision['verdict']} targets={result['target_count']} actual={decision['actual']}")
    print(f"result={args['output'] / args['request_id'] / 'result.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
