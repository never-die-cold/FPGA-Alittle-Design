"""Windows preview prototype. Mock frames are labeled; UVC has no frame association yet."""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pynq_host"))
from vision_protocol import mock_packet, validate_packet, is_current
import cv2
import numpy as np


def mock_frame(packet):
    frame = np.full((packet["height"], packet["width"], 3), (220, 230, 240), np.uint8)
    for target in packet["targets"]:
        x0, y0, x1, y1 = target["bbox"]
        cv2.rectangle(frame, (x0, y0), (x1, y1), (40, 50, 60), -1)
    return frame


def render(frame, packet=None, mock=False):
    frame = frame.copy()
    label = "VIDEO ONLY | UNASSOCIATED | no board recognition"
    if mock:
        validate_packet(packet)
        if not is_current(packet, packet["session_id"], packet["frame_id"], packet["config_id"]):
            raise ValueError("expired mock packet")
        for target in packet["targets"]:
            x0, y0, x1, y1 = target["bbox"]
            cv2.rectangle(frame, (x0, y0), (x1, y1), (40, 160, 30), 2)
            cv2.putText(frame, f"sample target {target['target_id']}", (x0, y0-8), 0, .6, (20, 80, 20), 2)
        label = f"MOCK ONLY | location samples | frame {packet['frame_id']} config {packet['config_id']}"
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 55), (35, 35, 35), -1)
    cv2.putText(frame, label, (16, 35), 0, .8, (255, 255, 255), 2)
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--endpoint", help="local mock service URL, e.g. http://127.0.0.1:8765")
    parser.add_argument("--source", type=int, default=0, help="UVC capture device index")
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--save", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        p = mock_packet("selftest", 1, 0)
        assert render(mock_frame(p), p, True).shape == (720, 1280, 3)
        print("PASS: preview mock renderer packaged runtime")
        return
    if args.headless and args.frames < 1:
        parser.error("headless requires --frames > 0")
    capture = None if args.mock else cv2.VideoCapture(args.source, cv2.CAP_DSHOW)
    try:
        i = 0
        while not args.frames or i < args.frames:
            i += 1
            if args.mock:
                if args.endpoint:
                    with urllib.request.urlopen(args.endpoint.rstrip("/")+"/v1/latest", timeout=1) as response:
                        packet = validate_packet(json.loads(response.read(65537)))
                else:
                    packet = mock_packet("local-preview", i, 0)
                frame = render(mock_frame(packet), packet, True)
            else:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("UVC frame unavailable")
                frame = render(frame)  # Never overlay unmatched network results onto capture frames.
            if args.save and not cv2.imwrite(str(args.save), frame):
                raise RuntimeError("preview image save failed")
            if not args.headless:
                cv2.imshow("M2 vision preview", frame)
                if cv2.waitKey(33) & 255 in (27, ord("q")):
                    break
    finally:
        if capture is not None:
            capture.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
