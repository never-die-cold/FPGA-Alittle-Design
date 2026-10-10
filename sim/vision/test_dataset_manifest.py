"""Repository-local manifest contract tests; no real capture or label claim."""
import csv
import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from dataset_manifest import validate_row, load_manifest, contained


def sample():
    return dict(frame_id="frame_00001", session="sess-20261010-a", split="train", light="L0",
                bg="gray", spacing="1D", obj_id="obj01", **{"class": "bolt"},
                x0="10", y0="20", x1="11", y1="21", notes="TEST_FIXTURE", specimen_id="bolt-a")


def rejected(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("invalid collection manifest accepted")


def fixture(root, rows):
    assert root.resolve().is_relative_to(ROOT), "fixtures must stay in the repository"
    root.mkdir(parents=True, exist_ok=True)
    for path in (root / "raw").rglob("*.png"):
        path.unlink()
    with (root / "manifest.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for index, (session, frame) in enumerate(sorted({(row["session"], row["frame_id"]) for row in rows})):
        path = root / "raw" / session / (frame + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        assert cv2.imwrite(str(path), np.full((720, 1280, 3), 31 * index + 10, np.uint8))


def check_frames():
    build = ROOT / "sim/build/vision/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as temporary:
        root, row = Path(temporary), sample()
        fixture(root, [row])
        assert b"\r\n" not in (root / "manifest.csv").read_bytes()
        assert len(load_manifest(root)["frames"]) == 1
        rejected(lambda: contained(root, "../outside.png"))
        for second in (row, {**row, "obj_id": "obj02"}, {**row, "split": "test"}):
            fixture(root, [row, second])
            rejected(lambda: load_manifest(root))
        fixture(root, [row, {**row, "obj_id": "obj02", "specimen_id": "bolt-b", "x0": "11", "x1": "12"}])
        assert len(load_manifest(root)["frames"][0]["targets"]) == 2
        rejected(lambda: load_manifest(root, max_targets=1))
        path = root / "raw" / row["session"] / (row["frame_id"] + ".png")
        assert cv2.imwrite(str(path), np.zeros((24, 32, 3), np.uint8))
        rejected(lambda: load_manifest(root))
        path.unlink()
        try:
            load_manifest(root)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("missing frame accepted")
        fixture(root, [row])
        for image in (np.zeros((720, 1280), np.uint8), np.zeros((720, 1280, 3), np.uint16)):
            assert cv2.imwrite(str(path), image)
            rejected(lambda: load_manifest(root))
        path.write_bytes(b"")
        rejected(lambda: load_manifest(root))
        fixture(root, [row])
        orphan = path.with_name("frame_00002.png")
        orphan.write_bytes(path.read_bytes())
        rejected(lambda: load_manifest(root))
        fixture(root, [row, {**row, "obj_id": "obj02", "x0": "11", "x1": "12"}])
        rejected(lambda: load_manifest(root))
        fixture(root, [row])
        manifest = root / "manifest.csv"
        raw = manifest.read_text(encoding="utf-8")
        manifest.write_text(raw.replace("frame_id,session", "frame_id,frame_id", 1), encoding="utf-8")
        rejected(lambda: load_manifest(root))
    print("PASS: collection frames, paths, identities, overlap, limits, raw omissions and PNG format")


def main():
    row = sample()
    assert validate_row(row)["bbox"] == [10, 20, 11, 21]
    empty = {**row, "split": "test", "obj_id": "", "class": "", "specimen_id": "",
             **dict.fromkeys(("x0", "y0", "x1", "y1"), "")}
    assert validate_row(empty) is None
    for key, value in (("session", "../escape"), ("frame_id", "../../other"), ("split", "validation"),
                       ("class", "pin"), ("x0", "-1"), ("x1", "10"), ("y1", "721"),
                       ("x1", "11.0"), ("light", "L4"), ("extra", "field"), ("x0", None)):
        rejected(lambda: validate_row({**row, key: value}))
    rejected(lambda: validate_row(None))
    rejected(lambda: validate_row({**empty, "split": "train"}))
    rejected(lambda: validate_row({**empty, "obj_id": "obj01"}))
    print("PASS: collection rows, half-open boxes, explicit empty scenes and invalid fields")


if __name__ == "__main__":
    main()
    check_frames()
