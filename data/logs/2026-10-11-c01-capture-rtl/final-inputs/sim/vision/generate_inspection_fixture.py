"""Generate geometric SYNTHETIC fixtures; they are not real fastener data."""
import argparse
from pathlib import Path
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    frame = np.full((720, 1280, 3), 220, np.uint8)
    frame[180:300, 160:230] = (40, 50, 60)
    cv2.circle(frame, (650, 350), 65, (65, 65, 65), -1)
    cv2.circle(frame, (650, 350), 25, (220, 220, 220), -1)
    cv2.rectangle(frame, (940, 410), (1039, 489), (40, 70, 60), -1)
    if not cv2.imwrite(str(args.output / "synthetic.png"), frame):
        raise OSError("fixture write failed")
    if not cv2.imwrite(str(args.output / "empty.png"), np.full_like(frame, 220)):
        raise OSError("empty fixture write failed")
    print("PASS: SYNTHETIC geometry and empty fixtures; no classification truth asserted")


if __name__ == "__main__":
    main()
