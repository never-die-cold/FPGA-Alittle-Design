"""Freeze exact ROI bytes and integer expectations for a board comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from compare_cop_rois import layers_from_payload, predict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/coprocessor"))
from int8_reference import classify_logits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.comparison = args.comparison.resolve()
    output = args.output.resolve()
    if ROOT not in output.parents or output.exists():
        parser.error("output must be new and inside the repository")
    model = args.model / "payload/provisional-model"
    digest = hashlib.sha256((model / "payload.bin").read_bytes()).hexdigest()
    source = json.loads((args.comparison / "comparison.json").read_bytes())
    if source["payload_sha256"] != digest:
        raise ValueError("comparison payload differs from frozen model")
    layers = layers_from_payload(model)
    output.mkdir(parents=True)
    cases, rows = {}, []
    inputs = [("roi_001", bytes(int(v, 16) for v in
               (args.model / "golden/roi_001/input.hex").read_text().split()), None)]
    for item in source["rois"]:
        raw = (args.comparison / f"roi-{item['index']:02d}.bin").read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["roi_sha256"]:
            raise ValueError("ROI provenance mismatch")
        inputs.append((f"scene_{item['index']:02d}", raw, item["int8_logits"]))
    for name, raw, previous in inputs:
        if len(raw) != 4096:
            raise ValueError("ROI must contain 4096 bytes")
        logits = predict(raw, layers)
        if previous is not None and logits != previous:
            raise ValueError("integer reference changed")
        folder = output / name
        folder.mkdir()
        (folder / "input.bin").write_bytes(raw)
        (folder / "input.hex").write_text("".join(f"{v:02x}\n" for v in raw), encoding="ascii")
        result = classify_logits(logits, 5)
        (folder / "result.txt").write_text(
            f"{result['class_id']} {result['margin_q']} {result['score_q15']} {int(result['low_conf'])} 5\n",
            encoding="ascii")
        cases[name] = {"result": result, "logits": logits}
        rows.append({"name": name, "path": f"{name}/input.bin", "logits": logits,
                     "roi_sha256": hashlib.sha256(raw).hexdigest()})
    manifest = {"kind": "DEVELOPMENT_BOARD_NUMERIC_VECTORS", "payload_sha256": digest,
                "comparison": str(args.comparison.relative_to(ROOT)), "cases": cases, "rois": rows}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(f"BOARD_VECTORS_READY cases={len(cases)} payload_sha256={digest}")


if __name__ == "__main__":
    main()
