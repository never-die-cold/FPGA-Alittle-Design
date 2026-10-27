"""Collect distinct stable single-class layouts; labels come from the user's scene."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sim/vision"))
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from localization_opencv import detect_boxes
from roi_preprocess import preprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=("bolt", "nut", "washer"), required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--seconds", type=float, default=25)
    parser.add_argument("--max-motion", type=float, default=2.0)
    parser.add_argument("--skip-initial-pose", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT not in output.parents or output.exists() or args.count < 1 or args.seconds <= 0:
        parser.error("use a new directory inside the repository and positive options")
    devices = subprocess.check_output(["powershell.exe", "-NoProfile", "-File", str(ROOT / "sim/scripts/list_dshow_video.ps1")])
    try:
        listing = devices.decode("utf-8")
    except UnicodeDecodeError:
        listing = devices.decode("gbk", errors="replace")
    indexes = [int(s.split("\t")[0]) for s in listing.splitlines() if s.split("\t")[-1] == "USB Video"]
    if len(indexes) != 1:
        raise RuntimeError("USB Video enumeration ambiguous")
    output.mkdir(parents=True)
    (output / "devices.txt").write_text(listing, encoding="utf-8")
    cap = cv2.VideoCapture(indexes[0], cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("capture device did not open")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FPS, 30)
    start, due, previous, saved_boxes, baseline_boxes = time.monotonic(), 0, None, None, None
    frames, candidates, rejected, motion_samples = [], 0, {"motion": 0, "count": 0, "duplicate_pose": 0}, []
    try:
        while time.monotonic() - start < args.seconds:
            ok, frame = cap.read()
            if not ok or frame.shape != (720, 1280, 3):
                raise RuntimeError("720p BGR frame unavailable")
            small = cv2.cvtColor(cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY)
            delta = None if previous is None else small.astype(np.int16)-previous.astype(np.int16)
            motion = 100 if delta is None else float(np.abs(delta-np.median(delta)).mean())
            previous = small
            if time.monotonic() < due:
                continue
            due = time.monotonic() + 0.5
            candidates += 1
            motion_samples.append(motion)
            if motion > args.max_motion:
                rejected["motion"] += 1
                continue
            boxes = detect_boxes(frame, 25, 0.00008, "local")
            if args.label in ("washer", "nut"):
                boxes = [b for b in boxes if 0.3 <= (b[2]-b[0])/(b[3]-b[1]) <= 3]
            if len(boxes) != args.count or any((c-a)*(d-b) > 30000 for a,b,c,d in boxes):
                rejected["count"] += 1
                if rejected["count"] % 10 == 1:
                    quarantine = output / f"rejected-count-{rejected['count']:03d}.png"
                    if not cv2.imwrite(str(quarantine), frame):
                        raise RuntimeError("quarantine PNG save failed")
                continue
            if args.skip_initial_pose:
                if baseline_boxes is None:
                    baseline_boxes = np.array(boxes)
                if np.max(np.abs(np.array(boxes)-baseline_boxes)) < 15:
                    rejected["duplicate_pose"] += 1
                    continue
            if saved_boxes is not None and np.max(np.abs(np.array(boxes)-saved_boxes)) < 15:
                rejected["duplicate_pose"] += 1
                continue
            folder = output / f"pose-{len(frames)+1:03d}"
            folder.mkdir()
            if not cv2.imwrite(str(folder / "raw.png"), frame):
                raise RuntimeError("raw PNG save failed")
            targets = []
            for index, box in enumerate(boxes):
                canvas, _ = preprocess(frame, box)
                if not cv2.imwrite(str(folder / f"roi-{index:02d}.png"), canvas):
                    raise RuntimeError("ROI save failed")
                raw = np.clip(np.rint(canvas.astype(np.float64)*127/255), -127, 127).astype(np.int8).tobytes()
                targets.append({"index": index, "bbox": list(box), "class_label": args.label,
                                "roi_sha256": hashlib.sha256(raw).hexdigest()})
            report = {"frame_sha256": hashlib.sha256((folder / "raw.png").read_bytes()).hexdigest(), "rois": targets}
            (folder / "comparison.json").write_text(json.dumps(report, indent=2)+"\n")
            frames.append({"layout": folder.name, "comparison_source": (folder/"comparison.json").relative_to(ROOT).as_posix(),
                           "frame_sha256": report["frame_sha256"], "targets": targets})
            saved_boxes = np.array(boxes)
            print(f"SAVED_LAYOUT {len(frames)} objects={len(targets)}", flush=True)
    finally:
        cap.release()
    result = {"annotation_status": "DRAFT_SINGLE_CLASS_REQUIRES_VISUAL_BOX_REVIEW", "user_scene_class": args.label,
              "user_scene_count": args.count, "split": "TRAIN_DEVELOPMENT_ONLY", "frames": frames,
              "seconds": round(time.monotonic()-start, 2), "candidates": candidates, "rejected": rejected,
              "motion_samples": motion_samples, "max_motion": args.max_motion}
    result["skip_initial_pose"] = args.skip_initial_pose
    (output / "annotations-draft.json").write_text(json.dumps(result, indent=2)+"\n")
    print("COLLECTION_COMPLETE " + json.dumps({"layouts": len(frames), "objects": sum(len(f["targets"]) for f in frames), "rejected": rejected}), flush=True)


if __name__ == "__main__":
    main()
