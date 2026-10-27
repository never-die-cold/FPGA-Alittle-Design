"""Run one inspection round on the coexistence bitstream (video + CNN in one PL).

Flow: load package payload -> configure cop -> localize the captured frame on PS
-> crop/quantize each ROI -> DMA into the CNN -> read the hardware result ->
apply the RUL order.  The driver uses the hardware data-plane order
(dma_after_commit) because the firmware accounts DMA_BYTES against ROI_COUNT.

Run on the board as root with the PYNQ venv, e.g.

    sudo -E /usr/local/share/pynq-venv/bin/python3 sim/scripts/cop_hw_round.py \
        --package /home/xilinx/cop-pkg-product --image /home/xilinx/frame.png \
        --round-dir /home/xilinx/round-001 --order 3,2,1
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))

import cop_regs as R  # noqa: E402
from cop_driver import CopDriver, PynqDmaPlane, PynqMmio  # noqa: E402
from cop_engine import CopEngine, trained_quantize_roi  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--round-dir", type=Path, required=True)
    parser.add_argument("--order", default="3,2,1", help="bolt,nut,washer counts")
    parser.add_argument("--min-score", type=float, default=0.8)
    parser.add_argument("--max-targets", type=int, default=15)
    parser.add_argument("--color-threshold", type=float, default=22)
    parser.add_argument("--min-area-ratio", type=float, default=0.00008)
    parser.add_argument("--cop-base", type=lambda t: int(t, 0), default=0x4000_0000)
    parser.add_argument("--dma-base", type=lambda t: int(t, 0), default=0x4001_0000)
    parser.add_argument("--gpio-base", type=lambda t: int(t, 0), default=0x4002_0000)
    parser.add_argument("--no-overlay", action="store_true",
                        help="PL already configured by the boot unit; skip download")
    parser.add_argument("--crop", default=None,
                        help="x0,y0,x1,y1 framing crop applied before localization")
    args = parser.parse_args()

    from pynq import MMIO, allocate
    sys.path.insert(0, str(args.package / "payload/tools"))
    from cop_payload_loader import preflight, prepare_board
    preflight(args.package, "roi_001")

    payload_dir = args.package / "payload" / "provisional-model"
    manifest = json.loads((payload_dir / "manifest.json").read_text())
    payload = (payload_dir / manifest["payload_file"]).read_bytes()
    if len(payload) != manifest["total_bytes"]:
        raise SystemExit("payload length differs from manifest")

    if not args.no_overlay:
        prepare_board(args.package, 1)

    cop = PynqMmio(MMIO(args.cop_base, 0x1000), args.cop_base)
    dma = MMIO(args.dma_base, 0x10000)
    gpio = MMIO(args.gpio_base, 0x10000)
    plane = PynqDmaPlane(dma, gpio, cop, allocate, max_targets=args.max_targets)
    order = dict(zip(R.CLASSES, (int(v) for v in args.order.split(","))))
    driver = CopDriver(cop, plane, order, args.min_score, args.max_targets, None,
                       model_payload=payload, model_id=manifest["model_id"],
                       addresses=plane.addresses, dma_after_commit=True)
    engine = CopEngine(order, args.min_score, args.max_targets, None,
                       driver=driver, compute_label="PL_CNN_FASTENER", simulated=False,
                       quantizer=trained_quantize_roi,
                       quantization_label="TRAINED_PTQ round_even(pixel*127/255); S_input=1/127",
                       color_threshold=args.color_threshold, min_area_ratio=args.min_area_ratio)

    args.round_dir.mkdir(parents=True, exist_ok=True)
    if args.crop:
        import cv2
        import numpy as np
        x0, y0, x1, y1 = (int(v) for v in args.crop.split(","))
        frame = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
        if frame is None or not (0 <= x0 < x1 <= frame.shape[1] and 0 <= y0 < y1 <= frame.shape[0]):
            raise SystemExit("invalid crop or unreadable image")
        framed = args.round_dir / "framed.png"
        cv2.imwrite(str(framed), frame[y0:y1, x0:x1])
        image = framed
    else:
        image = args.image
    fields = engine(image, args.round_dir, args.round_dir.name)
    (args.round_dir / "fields.json").write_text(json.dumps(fields, indent=2) + "\n")
    summary = {
        "status": fields.get("status"),
        "targets": [{"class": t.get("class"), "score": t.get("score"),
                     "bbox": t.get("bbox")} for t in fields.get("targets", [])],
        "decision": fields.get("decision"),
        "trace": engine.last_trace,
    }
    (args.round_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    engine.consume()
    plane.free()


if __name__ == "__main__":
    main()
