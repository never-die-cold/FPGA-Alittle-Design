"""C03 §4 register-model contract test (sim-only, no board).

Covers config receipt, atomic result window, sticky/W1C, busy-commit SLVERR,
watchdog, ABORT, SOFT_RESET, descriptor validation and fault injection.
"""
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
import cop_regs as R
from cop_mmio_sim import CopBusError, CopSim, SimFaults, scripted_compute

PAYLOAD = b"COP-SIM-DIAGNOSTIC-MODEL"
ADDRS = {"WEIGHT_ADDR": 0x1000, "TARGET_DESC_ADDR": 0x2000, "ROI_ADDR": 0x3000,
         "RESULT_ADDR": 0x9000}


def write(sim, name, value):
    sim.write32(R.OFFSETS[name], value)


def read(sim, name):
    return sim.read32(R.OFFSETS[name])


def descriptors(count):
    return [{"target_id": index, "flags": 0, "roi_index": index, "reserved": 0}
            for index in range(count)]


def configure(sim, count=2, expected=(1, 1, 0), seq=1, timeout=100_000_000,
              classes=("bolt", "nut", "washer"), min_margin=203):
    write(sim, "MODEL_ID", 0x51A1)
    write(sim, "WEIGHT_CRC32", R.crc32(PAYLOAD))
    write(sim, "ROI_COUNT", count)
    write(sim, "TIMEOUT_CYCLES", timeout)
    write(sim, "WORK_ORDER", R.pack_work_order(
        {"bolt": expected[0], "nut": expected[1], "washer": expected[2], "policy_max": 10}))
    write(sim, "WORK_ORDER_REV", seq)
    write(sim, "JOB_ID", 100 + seq)
    write(sim, "CAPTURE_ID", 7)
    write(sim, "SOURCE_CONFIG_ID", 3)
    write(sim, "WEIGHT_BYTES", len(PAYLOAD))
    for name, value in ADDRS.items():
        write(sim, name, value)
    write(sim, "ROI_STRIDE", R.ROI_BYTES)
    write(sim, "RESULT_STRIDE", R.RESULT_BYTES)
    write(sim, "MIN_MARGIN_Q", min_margin)
    sim.load_weights(ADDRS["WEIGHT_ADDR"], PAYLOAD)
    sim.load_rois(ADDRS["ROI_ADDR"], [bytes([index + 1]) * R.ROI_BYTES
                                      for index in range(count)])
    sim.load_descriptors(ADDRS["TARGET_DESC_ADDR"], descriptors(count))
    write(sim, "CFG_SEQ", seq)
    write(sim, "CFG_COMMIT", 1)


def wait_status(sim, mask, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = read(sim, "STATUS")
        if status & mask:
            return status
        time.sleep(0.002)
    raise AssertionError(f"status 0x{mask:x} not reached, last 0x{status:x}")


def result_words(sim, index):
    write(sim, "RESULT_INDEX", index)
    return read(sim, "RESULT_META"), read(sim, "RESULT_LOGITS"), read(sim, "RESULT_SCORE")


def test_identity_and_access(sim):
    assert read(sim, "IP_ID") == R.IP_ID
    assert read(sim, "VERSION") == read(sim, "CAPABILITY") == read(sim, "ERROR_CODE") == 0
    assert read(sim, "STATUS") == 0 and read(sim, "CTRL") == 0
    try:
        write(sim, "FW_DECISION", 1)
        raise AssertionError("PS write to FW_DECISION accepted")
    except CopBusError:
        pass
    assert read(sim, "FW_DECISION") == 0
    try:
        sim.read32(0x0FC)
        raise AssertionError("unmapped read accepted")
    except CopBusError:
        pass
    try:
        sim.read32(0x002)
        raise AssertionError("unaligned read accepted")
    except CopBusError:
        pass


def test_normal_job(sim):
    configure(sim)
    status = wait_status(sim, R.STATUS_DONE)
    assert status & R.STATUS_RESULT_VALID and status & R.STATUS_CFG_VALID
    assert status & R.STATUS_MODEL_VALID and status & R.STATUS_READY
    assert not status & (R.STATUS_BUSY | R.STATUS_ERROR | R.STATUS_TIMEOUT)
    seq = read(sim, "RESULT_SEQ")
    assert seq == 1
    decision = R.decode_fw_decision(read(sim, "FW_DECISION"))
    assert decision == {"result_seq": 1, "reasons": 0, "verdict_id": 1,
                        "verdict": "CHECK_PASS"}, decision
    assert R.unpack_actual(read(sim, "FW_ACTUAL_COUNTS")) == [1, 1, 0]
    meta0, logits0, score0 = result_words(sim, 0)
    assert meta0 & 0xFFFF == 0 and (meta0 >> 16) & 0xFF == 0
    assert (meta0 >> 24) & 0x7 == 1  # valid=1, low_conf=0, error=0
    assert logits0 & 0xFF == 0x7F and (logits0 >> 8) & 0xFF == 0x81  # +127 / -127 int8
    assert score0 & 0xFFFF == 32767 and (score0 >> 16) & 0xFF == 254
    meta1 = result_words(sim, 1)[0]
    assert meta1 & 0xFFFF == 1 and (meta1 >> 16) & 0xFF == 1
    # W1C: clear done+result_valid, keep config/model
    write(sim, "CTRL", R.CTRL_CLEAR_DONE)
    status = read(sim, "STATUS")
    assert not status & (R.STATUS_DONE | R.STATUS_RESULT_VALID)
    assert status & (R.STATUS_CFG_VALID | R.STATUS_MODEL_VALID | R.STATUS_READY)
    # Second job: new work order and ROIs, result seq advances.
    configure(sim, count=2, expected=(2, 0, 0), seq=2)
    wait_status(sim, R.STATUS_DONE)
    assert read(sim, "RESULT_SEQ") == 2
    decision = R.decode_fw_decision(read(sim, "FW_DECISION"))
    assert (decision["verdict"], decision["reasons"]) == ("CHECK_FAIL", 0)
    assert R.unpack_actual(read(sim, "FW_ACTUAL_COUNTS")) == [1, 1, 0]


def test_busy_commit_and_abort():
    sim = CopSim(scripted_compute(["bolt", "nut"]), SimFaults(delay_s=0.03))
    try:
        configure(sim, timeout=3_000_000_000)
        wait_status(sim, R.STATUS_BUSY)
        try:
            write(sim, "CFG_COMMIT", 1)
            raise AssertionError("busy commit accepted")
        except CopBusError:
            pass
        write(sim, "CTRL", R.CTRL_ABORT)
        status = read(sim, "STATUS")
        assert status & R.STATUS_ERROR and not status & R.STATUS_BUSY
        assert not status & R.STATUS_RESULT_VALID
        assert sim.error_name == "ABORTED"
        write(sim, "CTRL", R.CTRL_CLEAR_ERROR)
        assert not read(sim, "STATUS") & R.STATUS_ERROR
        # OPEN-10: idle ABORT sets ERROR in J04; recovery is the same W1C.
        write(sim, "CTRL", R.CTRL_ABORT)
        assert read(sim, "STATUS") & R.STATUS_ERROR
        write(sim, "CTRL", R.CTRL_CLEAR_ERROR)
        assert not read(sim, "STATUS") & R.STATUS_ERROR
    finally:
        sim.close()


def test_timeout_and_soft_reset():
    sim = CopSim(scripted_compute(["bolt", "nut"]), SimFaults(delay_s=0.01))
    try:
        configure(sim, timeout=1000)  # 10 us at 100 MHz
        status = wait_status(sim, R.STATUS_TIMEOUT)
        assert status & R.STATUS_ERROR and not status & R.STATUS_DONE
        assert not status & R.STATUS_RESULT_VALID and not status & R.STATUS_BUSY
        assert sim.error_name == "WATCHDOG" and read(sim, "RESULT_SEQ") == 0
        # SOFT_RESET clears run state, keeps config/model (C03-P10).
        write(sim, "CTRL", R.CTRL_SOFT_RESET)
        status = read(sim, "STATUS")
        assert not status & (R.STATUS_ERROR | R.STATUS_TIMEOUT | R.STATUS_DONE)
        assert status & (R.STATUS_CFG_VALID | R.STATUS_MODEL_VALID | R.STATUS_READY)
        assert read(sim, "FW_DECISION") == 0
    finally:
        sim.close()


def test_model_faults_and_descriptors():
    sim = CopSim(scripted_compute(["bolt", "nut"]), SimFaults(crc_mismatch=True))
    try:
        configure(sim)
        status = read(sim, "STATUS")
        assert status & R.STATUS_ERROR and not status & R.STATUS_MODEL_VALID
        assert not status & R.STATUS_CFG_VALID
        assert sim.error_name == "BAD_MODEL"
        write(sim, "CTRL", R.CTRL_CLEAR_ERROR)
        assert not read(sim, "STATUS") & R.STATUS_ERROR
    finally:
        sim.close()
    sim = CopSim(scripted_compute(["bolt", "nut"]), SimFaults(short_payload=True))
    try:
        configure(sim)
        assert read(sim, "STATUS") & R.STATUS_ERROR
        assert sim.error_name == "DMA_SHORT"
    finally:
        sim.close()
    sim = CopSim(scripted_compute(["bolt", "nut"]))
    try:
        configure(sim)
        wait_status(sim, R.STATUS_DONE)
        write(sim, "CTRL", R.CTRL_CLEAR_DONE)
        bad = descriptors(2)
        bad[1]["roi_index"] = 0
        sim.load_descriptors(ADDRS["TARGET_DESC_ADDR"], bad)
        write(sim, "CFG_SEQ", 2)
        write(sim, "CFG_COMMIT", 1)
        status = read(sim, "STATUS")
        assert status & R.STATUS_ERROR and not status & R.STATUS_CFG_VALID
        assert sim.error_name == "BAD_CONFIG"
    finally:
        sim.close()


def test_stale_result_is_visible():
    sim = CopSim(scripted_compute(["bolt", "nut"]), SimFaults(stale_result=True))
    try:
        configure(sim)
        wait_status(sim, R.STATUS_DONE)
        assert read(sim, "RESULT_SEQ") == 0
        assert R.decode_fw_decision(read(sim, "FW_DECISION"))["result_seq"] == 0
    finally:
        sim.close()


def main():
    sim = CopSim(scripted_compute(["bolt", "nut"]))
    try:
        test_identity_and_access(sim)
        test_normal_job(sim)
    finally:
        sim.close()
    test_busy_commit_and_abort()
    test_timeout_and_soft_reset()
    test_model_faults_and_descriptors()
    test_stale_result_is_visible()
    print("PASS: cop register model (config/result/sticky/W1C/busy/timeout/abort/reset/faults)")


if __name__ == "__main__":
    main()
