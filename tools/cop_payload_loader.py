#!/usr/bin/env python3
"""PYNQ-side loader for the PROVISIONAL coprocessor diagnostic payload."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import zlib

COP_BASE = 0x40000000
DMA_BASE = 0x40010000
GPIO_BASE = 0x40020000
REG = {"CTRL": 0x00C, "STATUS": 0x010, "ERROR_CODE": 0x014,
       "CFG_SEQ": 0x01C, "CFG_APPLIED": 0x020, "MODEL_ID": 0x024,
       "WEIGHT_CRC32": 0x028, "ROI_COUNT": 0x02C, "TIMEOUT_CYCLES": 0x030,
       "WORK_ORDER": 0x034, "WORK_ORDER_REV": 0x038, "JOB_ID": 0x03C,
       "CAPTURE_ID": 0x040, "SOURCE_CONFIG_ID": 0x044, "WEIGHT_ADDR": 0x048,
       "WEIGHT_BYTES": 0x04C, "TARGET_DESC_ADDR": 0x050, "ROI_ADDR": 0x054,
       "ROI_STRIDE": 0x058, "RESULT_ADDR": 0x05C, "RESULT_STRIDE": 0x060,
       "MIN_MARGIN_Q": 0x064, "CFG_COMMIT": 0x068, "RESULT_INDEX": 0x06C,
       "RESULT_META": 0x070, "RESULT_LOGITS": 0x074, "RESULT_SCORE": 0x078,
       "RESULT_SEQ": 0x07C, "DMA_BYTES": 0x084, "FW_DECISION": 0x08C}
STATUS = {"READY": 1 << 0, "BUSY": 1 << 1, "DONE": 1 << 2,
          "ERROR": 1 << 3, "TIMEOUT": 1 << 4, "MODEL_VALID": 1 << 6,
          "RESULT_VALID": 1 << 7, "DMA_BUSY": 1 << 8,
          "ACCEPTED": 1 << 11, "UNCONSUMED": 1 << 12}
DMA_DMACR, DMA_DMASR, DMA_SA, DMA_LENGTH = 0x00, 0x04, 0x18, 0x28
GPIO_DATA, GPIO_TRI, GPIO2_DATA, GPIO2_TRI = 0x00, 0x04, 0x08, 0x0C


class LoaderError(RuntimeError):
    pass


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_inputs(root, case):
    root = Path(root).resolve()
    payload_dir = root / "payload"
    manifest_path = payload_dir / "provisional-model/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    payload_path = manifest_path.parent / manifest["payload_file"]
    payload = payload_path.read_bytes()
    if manifest.get("kind") != "PROVISIONAL":
        raise LoaderError("this J08-lite loader accepts only kind=PROVISIONAL")
    if len(payload) != manifest["total_bytes"]:
        raise LoaderError("payload length differs from manifest total_bytes")
    if sha256(payload_path) != manifest["payload_sha256"]:
        raise LoaderError("payload SHA256 differs from manifest")
    if zlib.crc32(payload) & 0xffffffff != int(manifest["crc32"], 0):
        raise LoaderError("payload CRC32 differs from manifest")
    for tensor in manifest["tensors"]:
        start, length, align = tensor["offset"], tensor["length"], tensor["alignment"]
        if align != 64 or start % align or length <= 0 or start + length > len(payload):
            raise LoaderError("invalid tensor range/alignment: " + tensor["name"])
    hwh = payload_dir / "pynq_cop_40mhz.hwh"
    roi_hex = root / "golden" / case / "input.hex"
    roi = bytes(int(line, 16) for line in roi_hex.read_text(encoding="ascii").splitlines())
    if len(roi) != 4096:
        raise LoaderError("ROI must contain exactly 4096 bytes")
    with (root / "EXPECTED_OUTPUTS.tsv").open(newline="", encoding="utf-8") as stream:
        rows = {row["case"]: row for row in csv.DictReader(stream, delimiter="\t")}
    return manifest, payload, roi, rows[case], hwh


def hwh_capabilities(path):
    root = ET.parse(path).getroot()
    module = next((node for node in root.iter("MODULE") if node.get("INSTANCE") == "dma"), None)
    if module is None:
        raise LoaderError("HWH has no dma instance")
    params = {p.get("NAME"): p.get("VALUE") for p in module.iter("PARAMETER")}
    ranges = {m.get("INSTANCE"): int(m.get("BASEVALUE"), 0)
              for m in root.iter("MEMRANGE") if m.get("BASEVALUE")}
    needed = {"pl": COP_BASE, "dma": DMA_BASE, "dma_control": GPIO_BASE}
    if any(ranges.get(name) != base for name, base in needed.items()):
        raise LoaderError("HWH address map differs from the three pinned base addresses")
    return {"stream_bits": int(params["C_M_AXIS_MM2S_TDATA_WIDTH"]),
            "length_bits": int(params["C_SG_LENGTH_WIDTH"]), "bases": needed}


def preflight(root, case):
    manifest, payload, roi, expected, hwh = package_inputs(root, case)
    caps = hwh_capabilities(hwh)
    if caps["stream_bits"] != 64:
        raise LoaderError("DMA MM2S stream is not 64-bit")
    maximum = (1 << caps["length_bits"]) - 1
    if len(payload) > maximum:
        raise LoaderError(f"DMA_LENGTH_BLOCKED: payload={len(payload)} max_single_packet={maximum} "
                          f"(C_SG_LENGTH_WIDTH={caps['length_bits']}); do not split because TLAST ends a load")
    return manifest, payload, roi, expected, caps


def set_and_measure_clock(reads):
    from pynq import Clocks, MMIO
    if reads < 1:
        raise LoaderError("--reads must be positive")
    Clocks.fclk1_mhz = 40.0
    actual = float(Clocks.fclk1_mhz)
    values = [MMIO(COP_BASE, 0x1000).read(REG["STATUS"]) for _ in range(reads)]
    print(f"measured_fclk1_mhz={actual:.6f}")
    print("status_first_reads=" + ",".join(f"0x{value:08x}" for value in values))
    if abs(actual - 40.0) > 0.001:
        raise LoaderError("FCLK1 readback is not 40 MHz")
    if any(value != STATUS["READY"] for value in values):
        raise LoaderError("STATUS first-read criterion not met: every sample must be 0x00000001")


def wait_for(predicate, timeout, message):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value is not None:
            return value
    raise LoaderError(message)


def read_mask(mmio, offset, mask, asserted=True):
    value = mmio.read(offset)
    return value if bool(value & mask) == asserted else None


def dma_send(dma, gpio, cop, buffer, length, kind, timeout):
    control = (kind << 1)
    if not gpio.read(GPIO2_DATA) & 1:
        raise LoaderError("start_ready is 0 before dma_start")
    gpio.write(GPIO_TRI, 0)
    gpio.write(GPIO2_TRI, 0xffffffff)
    gpio.write(GPIO_DATA, control | 1)  # accepted high level toggles the CDC request
    gpio.write(GPIO_DATA, control)      # drop immediately; leaving it high retriggers after ack
    wait_for(lambda: read_mask(cop, REG["STATUS"], STATUS["DMA_BUSY"]),
             timeout, "start_ready request was not accepted (DMA_BUSY stayed 0)")
    buffer.flush()
    dma.write(DMA_DMACR, 4)
    wait_for(lambda: 1 if not dma.read(DMA_DMACR) & 4 else None, timeout, "AXI DMA reset timeout")
    dma.write(DMA_DMACR, 1)
    dma.write(DMA_SA, int(buffer.physical_address))
    dma.write(DMA_LENGTH, length)
    seen_payload_error = False
    def transfer_done():
        nonlocal seen_payload_error
        seen_payload_error |= bool(gpio.read(GPIO2_DATA) & 2)
        status = dma.read(DMA_DMASR)
        if status & 0x770:
            raise LoaderError(f"AXI DMA MM2S error status=0x{status:08x}")
        return status if status & 2 else None
    transfer_status = wait_for(transfer_done, timeout, "AXI DMA MM2S timeout")
    wait_for(lambda: read_mask(cop, REG["STATUS"], STATUS["DMA_BUSY"], False),
             timeout, "coprocessor DMA loader did not finish")
    gpio_status = gpio.read(GPIO2_DATA)
    if seen_payload_error or gpio_status & 2:
        raise LoaderError("payload_error observed")
    if not gpio_status & 1:
        raise LoaderError("start_ready did not return")
    if cop.read(REG["DMA_BYTES"]) != length:
        raise LoaderError("DMA_BYTES differs from submitted byte count")
    return transfer_status


def write_configuration(cop, manifest, case, buffers, sequence):
    expected_class = 0 if case == "pattern" else 2
    work_order = (10 << 24) | (1 << (8 * expected_class))
    values = {"CFG_SEQ": sequence, "MODEL_ID": manifest["model_id"],
              "WEIGHT_CRC32": int(manifest["crc32"], 0), "ROI_COUNT": 1,
              "TIMEOUT_CYCLES": 100000000, "WORK_ORDER": work_order,
              "WORK_ORDER_REV": 1, "JOB_ID": sequence, "CAPTURE_ID": sequence,
              "SOURCE_CONFIG_ID": 1, "WEIGHT_ADDR": int(buffers["payload"].physical_address),
              "WEIGHT_BYTES": manifest["total_bytes"],
              "TARGET_DESC_ADDR": int(buffers["targets"].physical_address),
              "ROI_ADDR": int(buffers["roi"].physical_address), "ROI_STRIDE": 4096,
              "RESULT_ADDR": int(buffers["results"].physical_address), "RESULT_STRIDE": 16,
              "MIN_MARGIN_Q": 5}
    for name, value in values.items():
        if name.endswith("ADDR") and value & 63:
            raise LoaderError(name + " is not 64-byte aligned")
        cop.write(REG[name], value)
    cop.write(REG["CFG_COMMIT"], 1)
    if cop.read(REG["CFG_APPLIED"]) != sequence:
        raise LoaderError("CFG_APPLIED did not acknowledge CFG_SEQ")


def signed8(value):
    return value - 256 if value & 0x80 else value


def read_result(cop, expected, sequence_before, timeout):
    accepted = wait_for(lambda: read_mask(cop, REG["STATUS"], STATUS["ACCEPTED"]),
                        timeout, "NO_ACK: firmware did not assert ACCEPTED")
    terminal = STATUS["DONE"] | STATUS["ERROR"] | STATUS["TIMEOUT"]
    status = wait_for(lambda: read_mask(cop, REG["STATUS"], terminal),
                      timeout, "HW_TIMEOUT: no terminal status")
    if status & (STATUS["ERROR"] | STATUS["TIMEOUT"]):
        raise LoaderError(f"hardware terminal error status=0x{status:08x} code=0x{cop.read(REG['ERROR_CODE']):08x}")
    if not status & STATUS["RESULT_VALID"]:
        raise LoaderError("DONE without RESULT_VALID")
    sequence = cop.read(REG["RESULT_SEQ"])
    if sequence != (sequence_before + 1) & 0xffffffff:
        raise LoaderError(f"stale RESULT_SEQ: before={sequence_before} after={sequence}")
    cop.write(REG["RESULT_INDEX"], 0)
    meta, logits_word, score_word = (cop.read(REG[name]) for name in
                                      ("RESULT_META", "RESULT_LOGITS", "RESULT_SCORE"))
    if cop.read(REG["RESULT_SEQ"]) != sequence:
        raise LoaderError("RESULT_SEQ changed during result read")
    def current_decision():
        value = cop.read(REG["FW_DECISION"])
        return value if ((value >> 16) & 0xffff) == (sequence & 0xffff) else None
    fw_decision = wait_for(current_decision, timeout,
                           "firmware decision did not bind the current RESULT_SEQ")
    measured = {"class_id": (meta >> 16) & 0xff, "valid": (meta >> 24) & 1,
                "low_conf": (meta >> 25) & 1,
                "logits": [signed8((logits_word >> shift) & 0xff) for shift in (0, 8, 16)],
                "margin_q": (score_word >> 16) & 0xff, "score_q15": score_word & 0x7fff,
                "result_seq": sequence, "fw_decision": fw_decision,
                "accepted_snapshot": accepted}
    wanted = {"class_id": int(expected["class_id"]), "margin_q": int(expected["margin_q"]),
              "score_q15": int(expected["score_q15"]),
              "low_conf": int(expected["low_conf"]), "valid": 1,
              "logits": [int(item) for item in expected["logits"].split(",")]}
    measured["matches_expected"] = all(measured[key] == value for key, value in wanted.items())
    return measured


def run_board(args):
    manifest, payload, roi, expected, caps = preflight(args.package, args.case)
    from pynq import Clocks, MMIO, allocate
    actual = float(Clocks.fclk1_mhz)
    if abs(actual - 40.0) > 0.001:
        raise LoaderError(f"FCLK1 is {actual:.6f} MHz, not 40 MHz")
    cop, dma, gpio = MMIO(COP_BASE, 0x1000), MMIO(DMA_BASE, 0x10000), MMIO(GPIO_BASE, 0x10000)
    initial_status = cop.read(REG["STATUS"])
    if initial_status & STATUS["UNCONSUMED"]:
        raise LoaderError(f"STALE_RESULT: consume or preserve prior terminal evidence, status=0x{initial_status:08x}")
    buffers = {name: allocate(shape=(size,), dtype="u1") for name, size in
               (("payload", len(payload)), ("roi", len(roi)), ("targets", 64), ("results", 256))}
    try:
        buffers["payload"][:] = list(payload); buffers["roi"][:] = list(roi)
        buffers["targets"][:] = 0; buffers["results"][:] = 0
        result_sequence_before = cop.read(REG["RESULT_SEQ"])
        sequence = int(time.time()) & 0xffffffff or 1
        write_configuration(cop, manifest, args.case, buffers, sequence)
        dma_send(dma, gpio, cop, buffers["payload"], len(payload), 0, args.timeout)
        dma_send(dma, gpio, cop, buffers["roi"], len(roi), 1, args.timeout)
        measured = read_result(cop, expected, result_sequence_before, args.timeout)
        measured.update({"case": args.case, "fclk1_mhz": actual,
                         "payload_bytes": len(payload), "payload_crc32": manifest["crc32"],
                         "dma_stream_bits": caps["stream_bits"]})
        output = Path(args.measurement).resolve()
        temporary = output.with_name(output.name + ".tmp")
        with temporary.open("wb") as stream:
            stream.write((json.dumps(measured, sort_keys=True) + "\n").encode("utf-8"))
            stream.flush(); os.fsync(stream.fileno())
        temporary.replace(output)
        print(json.dumps(measured, sort_keys=True))
        print("measurement_file=" + str(output))
        if not measured["matches_expected"]:
            raise LoaderError("measured result differs from EXPECTED_OUTPUTS.tsv")
        cop.write(REG["CTRL"], 1 << 6)
    finally:
        for buffer in buffers.values():
            buffer.freebuffer()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    clock = sub.add_parser("clock", help="set FCLK1=40 MHz and measure STATUS first reads")
    clock.add_argument("--reads", type=int, default=20)
    run = sub.add_parser("run", help="load one diagnostic case and print measured fields")
    run.add_argument("--package", required=True); run.add_argument("--case", choices=("pattern", "zero"), required=True)
    run.add_argument("--timeout", type=float, default=10.0); run.add_argument("--measurement", required=True)
    args = parser.parse_args()
    try:
        if args.command == "clock": set_and_measure_clock(args.reads)
        else: run_board(args)
    except (LoaderError, FileNotFoundError, KeyError, ValueError) as error:
        parser.exit(1, "BLOCKED: " + str(error) + "\n")


if __name__ == "__main__":
    main()
