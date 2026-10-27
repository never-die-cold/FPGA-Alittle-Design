"""Assemble a board package for the coprocessor loader (trained or diagnostic).

Mirrors sim/scripts/package_coprocessor_nc.sh, but the case list comes from the
network manifest instead of the hardcoded pattern/zero pair, so a trained-weight
payload and real-image cases can be loaded by tools/cop_payload_loader.py.
"""
import argparse
import hashlib
import json
import shutil
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from cop_payload_loader import hwh_clock_plan


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_into(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bit", type=Path, required=True)
    parser.add_argument("--hwh", type=Path, required=True)
    parser.add_argument("--xsa", type=Path)
    parser.add_argument("--payload", type=Path, required=True, help="payload-v1 directory")
    parser.add_argument("--network", type=Path, required=True, help="network-vectors directory")
    parser.add_argument("--cases", required=True, help="comma separated case names")
    parser.add_argument("--output", type=Path, default=ROOT / "build/board-package")
    parser.add_argument("--version", default="trained-ptq-board")
    args = parser.parse_args()

    stage = args.output.resolve()
    if ROOT not in stage.parents:
        raise SystemExit("output must be inside the repository")
    if stage.exists():
        raise SystemExit("output already exists; use a new versioned directory")
    network = args.network.resolve()
    manifest = json.loads((network / "manifest.json").read_text())
    cases = [name.strip() for name in args.cases.split(",") if name.strip()]
    missing = [name for name in cases if name not in manifest["cases"]]
    if missing:
        raise SystemExit(f"cases missing from the network manifest: {missing}")

    for name in cases:
        copy_into(network / name / "input.hex", stage / "golden" / name / "input.hex")
    copy_into(args.payload / "payload.bin", stage / "payload/provisional-model/payload.bin")
    copy_into(args.payload / "manifest.json", stage / "payload/provisional-model/manifest.json")
    copy_into(args.bit, stage / "payload" / args.bit.name)
    copy_into(args.hwh, stage / "payload" / args.hwh.name)
    if args.xsa:
        # Never place the xsa next to the bit: PYNQ treats a sibling .xsa as an
        # XSA bitstream (embedded_device.is_xsa) and then fails to parse metadata.
        copy_into(args.xsa, stage / "xsa" / args.xsa.name)
    copy_into(ROOT / "tools/cop_payload_loader.py", stage / "payload/tools/cop_payload_loader.py")
    copy_into(ROOT / "sim/scripts/cop_fclk.py", stage / "payload/tools/cop_fclk.py")
    copy_into(ROOT / "sim/scripts/cop_board_fast_run.py", stage / "payload/tools/cop_board_fast_run.py")

    rows = ["case\tclass_id\tmargin_q\tscore_q15\tlow_conf\tlogits\tresult_crc32"]
    for name in cases:
        case = manifest["cases"][name]
        result = case["result"]
        result_bytes = (network / name / "result.txt").read_bytes()
        fields = (name, result["class_id"], result["margin_q"], result["score_q15"],
                  int(result["low_conf"]), ",".join(str(int(v)) for v in case["logits"]),
                  f"{zlib.crc32(result_bytes) & 0xffffffff:08x}")
        rows.append("\t".join(str(value) for value in fields))
    (stage / "EXPECTED_OUTPUTS.tsv").write_bytes(("\n".join(rows) + "\n").encode("utf-8"))

    payload_manifest = json.loads((args.payload / "manifest.json").read_text())
    topology, input_mhz = hwh_clock_plan(args.hwh)
    version = {
        "VERSION": args.version,
        "PAYLOAD_KIND": manifest["kind"],
        "MODEL_ID": hex(payload_manifest["model_id"]),
        "BOARD": "UNVERIFIED_NEEDS_NC",
        "BOARD_CLOCK": "UNVERIFIED_NEEDS_TOPOLOGY_READBACK",
        "CLOCK_TOPOLOGY": topology,
        "FCLK1_EXPECTED_MHZ": f"{input_mhz:.6f}",
        "COP_EXPECTED_MHZ": "40.000000",
        "BIT_SHA256": sha256(args.bit),
        "HWH_SHA256": sha256(args.hwh),
    }
    (stage / "VERSION").write_bytes(
        ("\n".join(f"{key}={value}" for key, value in version.items()) + "\n").encode("utf-8"))

    files = sorted(str(path.relative_to(stage)).replace("\\", "/")
                   for path in stage.rglob("*") if path.is_file())
    (stage / "FILES.txt").write_bytes(("\n".join(files) + "\n").encode("utf-8"))
    (stage / "SHA256SUMS").write_bytes(
        ("\n".join(f"{sha256(stage / name)}  {name}" for name in files) + "\n").encode("utf-8"))
    print(f"PASS: board package {stage}")
    print(f"cases={cases} model_id={version['MODEL_ID']} files={len(files)}")


if __name__ == "__main__":
    main()
