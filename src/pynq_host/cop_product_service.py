"""Real C01 capture -> PS localization/ROI -> PL CNN -> CPU rules -> LIVE API.

The raw_capture bitstream preserves color HDMI display. Its optional PL image
analysis outputs are pruned; localization and ROI preprocessing execute on PS.
"""
import argparse
import fcntl
import hashlib
import json
import sys
import time
from pathlib import Path

import cop_regs as R
from c01_backend import C01Captures
from c01_capture import QUARANTINE
from c01_park_capture import ParkFrameCapture
from cop_driver import CopDriver, PynqDmaPlane, PynqMmio
from cop_engine import CopEngine, trained_quantize_roi
from vision_live_service import make_server
from vision_regs import VisionRegs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--order", help="optional explicit bolt,nut,washer order; default waits for web input")
    parser.add_argument("--min-score", type=float, default=0.8)
    parser.add_argument("--color-threshold", type=float, default=20)
    parser.add_argument("--min-area-ratio", type=float, default=0.00008)
    parser.add_argument("--background-mode", choices=("corners", "local"), default="local")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--min-free-mib", type=int, default=256)
    args = parser.parse_args()
    if args.min_free_mib < 0:
        parser.error("min-free-mib must be nonnegative")
    package = args.package.resolve()
    order = None
    if args.order is not None:
        try:
            order_values = [int(value) for value in args.order.split(",")]
        except ValueError:
            parser.error("order must contain three nonnegative counts")
        if len(order_values) != 3 or any(value < 0 for value in order_values):
            parser.error("order must contain three nonnegative counts")
        order = dict(zip(R.CLASSES, order_values))
    lock = Path("/home/xilinx/fpga-product.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    sys.path.insert(0, str(package / "payload/tools"))
    from cop_payload_loader import preflight, prepare_board
    from pynq import MMIO, PL, allocate
    manifest, payload, _, _, _ = preflight(package, "roi_001")
    prepare_board(package, 1)
    vision = VisionRegs(0x41000000)
    vision.apply_preset("GRAY")
    config = vision.commit(wait=False)
    vision.wait_applied(config, timeout=30, poll=0.02)
    cop = PynqMmio(MMIO(0x40000000, 4096), 0x40000000)
    plane = PynqDmaPlane(MMIO(0x40010000, 65536), MMIO(0x40020000, 65536), cop, allocate,
                         max_targets=10, timeout=15)
    driver = CopDriver(cop, plane, order, args.min_score, 10, 10,
                       model_payload=payload, model_id=manifest["model_id"],
                       addresses=plane.addresses, dma_after_commit=True,
                       job_timeout_s=15, accept_timeout_s=5)
    engine = CopEngine(order, args.min_score, 10, 10, driver=driver, simulated=False,
                       compute_label="PL_CNN_FASTENER", quantizer=trained_quantize_roi,
                       quantization_label="TRAINED_PTQ round_even(pixel*127/255); S_input=1/127",
                       color_threshold=args.color_threshold, min_area_ratio=args.min_area_ratio,
                       background_mode=args.background_mode)
    vdma, status = MMIO(0x43000000, 65536), MMIO(0x42000000, 65536)

    def identity():
        return (Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                PL.bitfile_name, str(PL.timestamp))

    class Captures(C01Captures):
        def health(self):
            flags = status.read(0x04)
            return bool(flags & 1) and not bool(flags & 4)

        def configure(self, control):
            if control != 0:
                raise ValueError("raw_capture supports control=0; analysis preprocessing runs on PS")
            vision.apply_preset("GRAY")
            applied = vision.commit(wait=False)
            try:
                vision.wait_applied(applied, timeout=30, poll=0.02)
            except TimeoutError as exc:
                raise RuntimeError("video configuration did not reach a frame boundary") from exc
            return applied

        def capture(self, round_dir):
            owner = ParkFrameCapture(vdma, status, allocate, identity, timeout=5)
            try:
                frame = owner.capture()
                path = Path(round_dir) / "capture.png"
                self._save_png(path, frame)
                self.seq += 1
                return path
            finally:
                (Path(round_dir) / "capture-dma.json").write_text(json.dumps(owner.evidence, indent=2))

    captures = Captures(None)
    args.root.mkdir(parents=True, exist_ok=True)
    provenance = {"bit_sha256": hashlib.sha256((package/"payload/pynq_cop_40mhz.bit").read_bytes()).hexdigest(),
                  "payload_sha256": manifest["payload_sha256"], "model_id": manifest["model_id"],
                  "model_status": manifest["kind"], "order": order,
                  "localization": vars(args) | {"package": str(package), "root": str(args.root)}}
    (args.root/"hardware.json").write_text(json.dumps(provenance, indent=2))
    server = make_server(args.host, args.port, args.root, captures, engine, order,
                         archive_every_round=True, initial_config_id=config,
                         min_free_bytes=args.min_free_mib * 1024 * 1024)
    print("PRODUCT_SERVICE_READY " + json.dumps({"engine": engine.label, "capture": "C01_PARK",
                                                "port": args.port, "order": order}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        while QUARANTINE:
            print("DMA STOP UNCONFIRMED: retaining buffers; board reset required", flush=True)
            time.sleep(5)
        plane.free()


if __name__ == "__main__":
    main()
