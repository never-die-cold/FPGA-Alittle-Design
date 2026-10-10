"""FP32/uint8 bit ordering, two-file consistency and integrity checks."""
import sys
import tempfile
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from reference_tensors import write_tensor, read_tensor, sha256


def main():
    build = ROOT / "sim/build/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as directory:
        folder = Path(directory)
        values = [np.array([0, 1, 255], np.uint8), np.array([0.0, -0.0, 1.0, -2.5], np.float32)]
        for number, value in enumerate(values):
            record = write_tensor(folder, f"tensor{number}", value, "VECTOR")
            assert read_tensor(folder, record).tobytes() == value.tobytes()
        assert (folder / "tensor1.hex").read_text().splitlines() == ["00000000", "80000000", "3f800000", "c0200000"]
        (folder / "tensor1.hex").write_bytes(b"00000000\n" * 4)
        for metadata in (record, {**record, "hex_sha256": sha256((folder / "tensor1.hex").read_bytes())},
                         {**record, "npy": "../escaped.npy"}):
            try:
                read_tensor(folder, metadata)
            except ValueError:
                pass
            else:
                raise AssertionError("altered or escaping tensor accepted")
    print("PASS: FP32/uint8 exact bits, row order, hash/format/path rejection")


if __name__ == "__main__":
    main()
