"""Audit collection structure and split leakage; never certify model accuracy."""
import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from dataset_audit import audit_dataset, SOURCE_KINDS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path, help="new JSON report; existing files are preserved")
    parser.add_argument("--source-kind", choices=SOURCE_KINDS, required=True)
    parser.add_argument("--max-targets", type=int, default=10, help="candidate collection limit (1-16)")
    args = parser.parse_args()
    pending = args.output.with_name(args.output.name + ".pending")
    try:
        if args.output.exists() or pending.exists():
            raise ValueError("audit report or pending file already exists")
        result = audit_dataset(args.dataset, args.source_kind, args.max_targets)
        sources = ("src/pynq_host/dataset_manifest.py", "src/pynq_host/dataset_audit.py",
                   "sim/vision/audit_fastener_dataset.py")
        result["code_sha256"] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
        result["runtime"] = {"python": platform.python_version(), "opencv": cv2.__version__, "numpy": np.__version__}
        payload = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with pending.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
        pending.replace(args.output)
    except (OSError, UnicodeError, ValueError, csv.Error, cv2.error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: DATASET_STRUCTURE_AUDIT source={args.source_kind} frames={result['frame_count']} targets={result['target_count']}")
    print("GAPS: " + json.dumps(result["missing_classes"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
