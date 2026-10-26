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
    (model.parent / "pynq_cop_40mhz.bit").write_bytes(b"offline-test-bit")
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
        raise AssertionError("14-bit DMA length capability was accepted")
    except loader.LoaderError as error:
        assert "DMA_LENGTH_WIDTH_MISMATCH" in str(error) and "16383" in str(error)

    write_hwh(hwh, 16)
    manifest, payload, roi, expected, caps = loader.preflight(args.output, "zero")
    assert manifest["kind"] == "PROVISIONAL" and len(payload) == 36032 and len(roi) == 4096
    assert expected["score_q15"] == "258" and caps["stream_bits"] == 64
    class NoMMIO:
        def read(self, offset): raise AssertionError("oversize check touched MMIO")
        def write(self, offset, value): raise AssertionError("oversize check touched MMIO")
    try:
        loader.dma_send(NoMMIO(), NoMMIO(), NoMMIO(), object(), 65536, 0, 0.01)
        raise AssertionError("17-bit DMA length was accepted")
    except loader.LoaderError as error:
        assert "16-bit" in str(error)

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

    fake_pynq = types.ModuleType("pynq"); events = []
    class Clocks: fclk1_mhz = 142.857
    class Overlay:
        def __init__(self, bit, download):
            assert Path(bit).is_file() and download and Clocks.fclk1_mhz == 40.0
            events.append("overlay")
        def is_loaded(self): return True
    class BoardMMIO:
        def __init__(self, base, size): self.base = base
        def read(self, offset):
            if self.base == loader.SLCR_BASE:
                assert offset == loader.FPGA_RST_CTRL
                return 0
            assert self.base == loader.COP_BASE and "reset_release" in events
            if offset == loader.REG["STATUS"]: return loader.STATUS["READY"]
            if offset == loader.REG["FW_DECISION"]: return 1
            return 0
        def write(self, offset, value):
            if self.base != loader.SLCR_BASE: return
            if offset == loader.FPGA_RST_CTRL:
                events.append("reset_assert" if value & 2 else "reset_release")
    fake_pynq.Clocks, fake_pynq.MMIO, fake_pynq.Overlay = Clocks, BoardMMIO, Overlay
    sys.modules["pynq"] = fake_pynq
    loader.set_and_measure_clock(args.output, 3, api=fake_pynq, sleeper=lambda _: None)
    assert Clocks.fclk1_mhz == 40.0
    assert events.index("overlay") < events.index("reset_assert") < events.index("reset_release")
    for actual, statuses, marker in ((40.000001, [1], "FCLK1_MISMATCH"),
                                     (40.0, [0, 1], "FIRST_STATUS_INVALID")):
        try:
            loader.validate_clock_status(actual, statuses)
            raise AssertionError("invalid clock/status evidence was accepted")
        except loader.LoaderError as error:
            assert marker in str(error) and "next=" in str(error)
    class NoAccess:
        def __init__(self, *args): raise AssertionError("guard failure touched cop MMIO")
    try:
        loader.cop_mmio_after_reconfigure(NoAccess, None)
        raise AssertionError("clock-without-reconfigure state was accepted")
    except loader.LoaderError as error:
        assert "CLOCK_SEQUENCE_INCOMPLETE" in str(error)
    class ZeroCop:
        def read(self, offset): return 0
    try:
        loader.firmware_smoke(ZeroCop(), 0)
        raise AssertionError("silent firmware was accepted")
    except loader.LoaderError as error:
        assert "FIRMWARE_NO_ACTIVITY" in str(error)
    print("PASS: payload_loader DMA16 plus clock->PL reload->FCLKRESET1->STATUS ordering; "
          "unreconfigured access and silent firmware fail closed")


if __name__ == "__main__": main()
