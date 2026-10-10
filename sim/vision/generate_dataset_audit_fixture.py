"""Create synthetic audit-only frames and fictional labels, not accuracy samples."""
import argparse
from pathlib import Path
from test_dataset_manifest import fixture, sample


def generate(output):
    output = Path(output)
    if output.exists():
        raise ValueError("fixture output already exists; choose a new directory")
    base = sample()
    rows = [{**base, "session": "sess-20261010-" + split, "split": split,
             "class": label, "specimen_id": label + "-fixture", "light": "L" + str(index)}
            for index, (split, label) in enumerate(zip(("train", "val", "test"), ("bolt", "nut", "washer")))]
    rows.append({**rows[-1], "frame_id": "frame_00002", "class": "", "obj_id": "", "specimen_id": "",
                 "spacing": "empty", **dict.fromkeys(("x0", "y0", "x1", "y1"), "")})
    fixture(output, rows)
    print("PASS: TEST_FIXTURE generated: four synthetic frames, three fictional targets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    generate(parser.parse_args().output)
