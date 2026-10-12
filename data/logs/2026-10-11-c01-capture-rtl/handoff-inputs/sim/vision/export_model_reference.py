"""Export the received prototype as an FP32 software reference, not INT8 RTL data."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from reference_package import export_reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--weights", type=Path, default=ROOT / "models/cnn-border-fill-best.pt")
    args = parser.parse_args()
    try:
        manifest = export_reference(args.weights, args.output)
    except (OSError, ValueError, RuntimeError, AssertionError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: FP32 software reference exported; MAC/ROI={manifest['audit']['macs_per_roi']}; output={args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
