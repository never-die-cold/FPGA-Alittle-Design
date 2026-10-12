"""Synthetic metadata fixtures exercise leakage gates, never classification accuracy."""
import shutil
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import cv2
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from dataset_audit import audit_dataset
from test_dataset_manifest import sample, fixture, rejected
from generate_dataset_audit_fixture import generate


def check_audit():
    build = ROOT / "sim/build/vision/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as temporary:
        root, row = Path(temporary), sample()
        other = {**row, "session": "sess-20261010-b", "split": "test", "class": "nut", "specimen_id": "nut-b"}
        fixture(root, [row, other])
        result = audit_dataset(root, "TEST_FIXTURE")
        assert result["frame_count"] == result["target_count"] == 2
        assert result["coverage"]["train"]["classes"]["bolt"] == 1
        assert result["missing_classes"]["test"] == ["bolt", "washer"]
        assert result["all_specimen_ids_present"] and not result["label_accuracy_verified"]
        rejected(lambda: audit_dataset(root, "LIVE"))
        for second in ({**other, "session": row["session"], "frame_id": "frame_00002"},
                       {**other, "class": "bolt", "specimen_id": row["specimen_id"]}):
            fixture(root, [row, second])
            rejected(lambda: audit_dataset(root, "TEST_FIXTURE"))
        fixture(root, [row, other])
        first = root / "raw" / row["session"] / "frame_00001.png"
        second = root / "raw" / other["session"] / "frame_00001.png"
        shutil.copyfile(first, second)
        rejected(lambda: audit_dataset(root, "TEST_FIXTURE"))
        image = cv2.imread(str(first))
        assert cv2.imwrite(str(second), image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        assert first.read_bytes() != second.read_bytes()
        rejected(lambda: audit_dataset(root, "TEST_FIXTURE"))
        fixture(root, [{**row, "specimen_id": ""}, other])
        assert audit_dataset(root, "PUBLIC")["missing_specimen_ids"] == 1
        assert not audit_dataset(root, "PUBLIC")["all_specimen_ids_present"]
        fixture(root, [row, {**other, "split": "train", "specimen_id": row["specimen_id"]}])
        rejected(lambda: audit_dataset(root, "TEST_FIXTURE"))
        fixture(root, [row, {**other, "split": "train"}])
        first = root / "raw" / row["session"] / "frame_00001.png"
        second = root / "raw" / other["session"] / "frame_00001.png"
        shutil.copyfile(first, second)
        assert audit_dataset(root, "TEST_FIXTURE")["duplicate_pixel_frames_within_splits"] == 1
    print("PASS: session/file/pixel/specimen leakage gates, coverage gaps and provenance limits")


def check_cli():
    with tempfile.TemporaryDirectory(dir=ROOT / "sim/build/vision/inspection") as temporary:
        root = Path(temporary)
        generate(root / "dataset")
        before = (root / "dataset/manifest.csv").read_bytes()
        rejected(lambda: generate(root / "dataset"))
        assert (root / "dataset/manifest.csv").read_bytes() == before
        output = root / "report.json"
        command = [sys.executable, "-I", str(ROOT / "sim/vision/audit_fastener_dataset.py"),
                   str(root / "dataset"), str(output), "--source-kind", "TEST_FIXTURE"]
        completed = subprocess.run(command, text=True, capture_output=True)
        assert completed.returncode == 0 and "PASS:" in completed.stdout, completed.stderr
        original = output.read_bytes()
        report = json.loads(original)
        assert report["status"] == "STRUCTURE_PASS" and report["source_kind"] == "TEST_FIXTURE"
        assert report["frame_count"] == 4 and report["target_count"] == 3
        assert report["coverage"]["test"]["empty_frames"] == 1
        assert report["coverage"]["test"]["frame_target_counts"] == {"0": 1, "1": 1}
        assert report["missing_classes"]["val"] == ["bolt", "washer"]
        assert not report["capture_origin_authenticated"] and len(report["code_sha256"]) == 3
        assert not output.with_name(output.name + ".pending").exists()
        assert subprocess.run(command, capture_output=True).returncode == 1
        assert output.read_bytes() == original
        output.unlink()
        pending = output.with_name(output.name + ".pending")
        pending.write_bytes(b"interrupted audit")
        assert subprocess.run(command, capture_output=True).returncode == 1
        assert pending.read_bytes() == b"interrupted audit" and not output.exists()
        pending.unlink()
        invalid = command[:-2]
        assert subprocess.run(invalid, capture_output=True).returncode != 0
        path = root / "dataset/raw/sess-20261010-train/frame_00001.png"
        path.unlink()
        completed = subprocess.run(command, text=True, capture_output=True)
        assert completed.returncode == 1 and "ERROR:" in completed.stderr and not output.exists()
    print("PASS: isolated audit CLI, explicit source, atomic report, refusal to overwrite and invalid dataset")


if __name__ == "__main__":
    check_audit()
    check_cli()
