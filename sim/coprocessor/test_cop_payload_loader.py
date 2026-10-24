#!/usr/bin/env python3
"""Offline, reproducible checks for tools/cop_payload_loader.py."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import cop_payload_loader as loader


def write_hwh(path, length_bits):
    path.write_text(f"""<SYSTEM><MODULES>
<MODULE INSTANCE="dma"><PARAMETERS>
<PARAMETER NAME="C_M_AXIS_MM2S_TDATA_WIDTH" VALUE="64"/>
<PARAMETER NAME="C_SG_LENGTH_WIDTH" VALUE="{length_bits}"/>
</PARAMETERS></MODULE></MODULES><MEMRANGES>
<MEMRANGE INSTANCE="pl" BASEVALUE="0x40000000"/>
<MEMRANGE INSTANCE="dma" BASEVALUE="0x40010000"/>
<MEMRANGE INSTANCE="dma_control" BASEVALUE="0x40020000"/>
</MEMRANGES></SYSTEM>\n""", encoding="ascii")


def make_package(output, generated, network):
    if output.exists(): shutil.rmtree(output)
    model = output / "payload/provisional-model"
    golden = output / "golden"
    model.mkdir(parents=True); golden.mkdir()
    for name in ("manifest.json", "payload.bin"):
        shutil.copy2(generated / name, model / name)
    for case in ("pattern", "zero"):
        (golden / case).mkdir()
        shutil.copy2(network / case / "input.hex", golden / case / "input.hex")
    (output / "EXPECTED_OUTPUTS.tsv").write_bytes(
        b"case\tclass_id\tmargin_q\tscore_q15\tlow_conf\tlogits\n"
        b"pattern\t0\t0\t0\t1\t1,-3,1\nzero\t2\t2\t258\t1\t2,-3,4\n")
    return model.parent / "pynq_cop_40mhz.hwh"


class FakeMMIO:
    def __init__(self):
        self.values = {loader.REG["STATUS"]: loader.STATUS["ACCEPTED"] |
                       loader.STATUS["DONE"] | loader.STATUS["RESULT_VALID"],
                       loader.REG["RESULT_SEQ"]: 9,
                       loader.REG["RESULT_META"]: (1 << 24) | (1 << 25) | (2 << 16),
                       loader.REG["RESULT_LOGITS"]: 0x04fd02,
                       loader.REG["RESULT_SCORE"]: (2 << 16) | 258,
                       loader.REG["FW_DECISION"]: (9 << 16) | 1}
    def read(self, offset): return self.values.get(offset, 0)
    def write(self, offset, value): self.values[offset] = value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--network", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    hwh = make_package(args.output, args.generated, args.network)

    write_hwh(hwh, 14)
    try:
        loader.preflight(args.output, "zero")
        raise AssertionError("14-bit DMA length did not reject 36,032 bytes")
    except loader.LoaderError as error:
        assert "DMA_LENGTH_BLOCKED" in str(error) and "16383" in str(error)

    write_hwh(hwh, 16)
    manifest, payload, roi, expected, caps = loader.preflight(args.output, "zero")
    assert manifest["kind"] == "PROVISIONAL" and len(payload) == 36032 and len(roi) == 4096
    assert expected["score_q15"] == "258" and caps["stream_bits"] == 64

    measured = loader.read_result(FakeMMIO(), expected, 8, 0.01)
    assert measured["matches_expected"] and measured["result_seq"] == 9
    assert measured["logits"] == [2, -3, 4]

    payload_path = args.output / "payload/provisional-model/payload.bin"
    original = payload_path.read_bytes()
    payload_path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    try:
        loader.preflight(args.output, "zero")
        raise AssertionError("tampered payload was accepted")
    except loader.LoaderError as error:
        assert "SHA256" in str(error)
    payload_path.write_bytes(original)

    fake_pynq = types.ModuleType("pynq")
    class Clocks: fclk1_mhz = 142.857
    class StatusMMIO:
        def __init__(self, base, size): assert (base, size) == (loader.COP_BASE, 0x1000)
        def read(self, offset): assert offset == loader.REG["STATUS"]; return 1
    fake_pynq.Clocks, fake_pynq.MMIO = Clocks, StatusMMIO
    sys.modules["pynq"] = fake_pynq
    loader.set_and_measure_clock(3)
    assert Clocks.fclk1_mhz == 40.0
    print("PASS: payload_loader manifest/SHA256/CRC/HWH/address/result/clock guards; "
          "14-bit DMA rejects 36032 before MMIO")


if __name__ == "__main__": main()
