"""Board-only CPU stage profile on an archived frame; no MMIO or model changes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--mode", choices=("local", "local-fast"), default="local")
    args = parser.parse_args()
    sys.path[:0] = [str(args.app_root / "sim/vision"), str(args.app_root / "src/pynq_host")]
    from localization_opencv import detect_boxes, contrast_mask
    from roi_preprocess import preprocess
    raw = args.frame.read_bytes()
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None or args.repeats < 1:
        parser.error("valid archived frame and positive repeats required")
    report = {"frame_sha256":hashlib.sha256(raw).hexdigest(), "opencv":cv2.__version__, "mode":args.mode,
              "threads":cv2.getNumThreads(), "samples":[]}
    for _ in range(args.repeats):
        row = {}
        def timed(name, operation):
            started = time.perf_counter()
            result = operation()
            row[name] = round((time.perf_counter()-started)*1000, 3)
            return result
        timed("decode_ms", lambda:cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR))
        boxes = timed("locate_ms", lambda:detect_boxes(image,25,.00008,args.mode))
        timed("roi_ms", lambda:[preprocess(image,b) for b in boxes])
        encoded = timed("encode_default_ms", lambda:cv2.imencode(".png",image))
        quick = timed("encode_zero_ms", lambda:cv2.imencode(".png",image,[cv2.IMWRITE_PNG_COMPRESSION,0]))
        assert encoded[0] and quick[0]
        assert np.array_equal(cv2.imdecode(quick[1],cv2.IMREAD_COLOR),image)
        row.update(targets=len(boxes), default_bytes=int(encoded[1].nbytes), zero_bytes=int(quick[1].nbytes))
        report["samples"].append(row)
    row = {}
    lab = timed("lab_ms", lambda:cv2.cvtColor(image,cv2.COLOR_BGR2LAB))
    h,w = lab.shape[:2]
    factor,window = (8,15) if args.mode == "local-fast" else (4,31)
    small = timed("downsample_ms", lambda:cv2.resize(lab,(w//factor,h//factor),interpolation=cv2.INTER_AREA))
    small = timed("median_ms", lambda:cv2.medianBlur(small,window))
    bg = timed("background_ms", lambda:cv2.resize(small,(w,h),interpolation=cv2.INTER_LINEAR).astype(np.int16))
    mask = timed("contrast_ms", lambda:contrast_mask(lab,bg,25))
    mask = timed("close_ms", lambda:cv2.morphologyEx(mask,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))))
    mask = timed("open_ms", lambda:cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))))
    timed("components_ms", lambda:cv2.connectedComponentsWithStats(mask))
    report["localization_stages"] = row
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
