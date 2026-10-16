"""Checked file snapshot inside the existing HUD; no camera/network or new batch."""
import json
from pathlib import Path
import cv2
from inspection_artifacts import load_existing
from hud import Hud, AMBER, MAIN
from hud_text import TextEngine


def render_manifest(path):
    path = Path(path)
    if path.name != "result.json":
        raise ValueError("replay requires a result.json manifest")
    result = json.loads(path.read_text(encoding="utf-8"))
    result = load_existing(path.parent, result["request_fingerprint"])
    if not {"frame.png", "annotated.png", "source.bin"} <= {item["path"] for item in result["artifacts"]}:
        raise ValueError("missing required replay images")
    frame = cv2.imread(str(path.parent / "annotated.png"))
    if frame is None or frame.shape[:2] != (result["height"], result["width"]):
        raise ValueError("invalid replay frame dimensions")
    actual = result["decision"]["actual"]
    expected = result["decision"]["expected"]
    counts = [(label.upper(), f"{actual[label] if actual is not None else '--'}/{expected[label]}", MAIN)
              for label in ("bolt", "nut", "washer")]
    state = {"badge": ("FILE REPLAY", AMBER), "clock": "OFFLINE SNAPSHOT",
             "status": ("PROTOTYPE / " + result["decision"]["verdict"], MAIN, "SemiBold"),
             "detail": result["request_id"], "cells": counts, "fresh": None,
             "counts_note": "ACTUAL / WORK ORDER",
             "boxes": None, "list": [tuple(target["bbox"]) for target in result["targets"]],
             "button": False}
    return Hud(TextEngine(), system=("OFFLINE FILE", AMBER)).render(frame, state)


def show_replay(args, work_area):
    canvas = render_manifest(args.replay)
    if args.save and not cv2.imwrite(str(args.save), canvas):
        raise OSError("replay preview save failed")
    if not args.headless:
        aw, ah = work_area()
        scale = min(aw / 1600, ah / 900, 2.0)
        display = cv2.resize(canvas, (int(1600 * scale) & ~1, int(900 * scale) & ~1))
        try:
            cv2.imshow("EdgeSight FILE REPLAY", display)
            while cv2.waitKey(30) & 255 not in (27, ord("q")):
                pass
        finally:
            cv2.destroyAllWindows()
    print("PASS: checked FILE REPLAY snapshot; no camera/network/batch creation")
