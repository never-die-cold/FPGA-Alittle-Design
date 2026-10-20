"""PS driver tests over the C03 register sim: happy/duplicate/stale/timeout/CRC.

Every failure path asserts that no result is returned as CHECK_PASS.
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
from cop_driver import (CopConfigError, CopDriver, CopProtocolError, CopTimeoutError,
                        PynqDmaPlane, SimDmaPlane)
from cop_mmio_sim import CopSim, SimFaults, scripted_compute

ORDER = {"bolt": 1, "nut": 1, "washer": 1}


def make_job(job_id, rev=1, count=3):
    return {"targets": [{"target_id": index, "roi": bytes([index + 1]) * 4096,
                         "flags": 0} for index in range(count)],
            "job_id": job_id, "work_order_rev": rev, "capture_id": 10 + job_id,
            "source_config_id": 4}


def build(faults=None, classes=("bolt", "nut", "washer"), timeout_s=2.0):
    sim = CopSim(scripted_compute(list(classes)), faults)
    driver = CopDriver(sim, SimDmaPlane(sim), dict(ORDER), 0.8, 16, 10,
                       job_timeout_s=timeout_s, config_timeout_s=0.5)
    return sim, driver


def test_happy_and_duplicate():
    sim, driver = build()
    try:
        result = driver.run(make_job(1))
        assert result["decision"]["verdict"] == "CHECK_PASS"
        assert [t["class"] for t in result["targets"]] == ["bolt", "nut", "washer"]
        assert result["decision"]["actual"] == dict(ORDER)
        assert result["trace"]["fw"]["verdict"] == "CHECK_PASS"
        assert result["trace"]["fw"]["reasons_names"] == []
        assert result["result_seq"] == 1 and result["cfg_seq"] == 1
        assert sim.jobs == 1 and driver.read("RESULT_SEQ") == 1
        # Same JOB_ID returns the cached final verdict without a second hardware run.
        again = driver.run(make_job(1))
        assert again["duplicate"] is True and again["result_seq"] == 1 and sim.jobs == 1
        # Reusing the key for different targets is forbidden (C03 §8).
        changed = make_job(1)
        changed["targets"][0]["roi"] = b"\x7f" * 4096
        try:
            driver.run(changed)
            raise AssertionError("JOB_ID reuse with different targets accepted")
        except CopProtocolError:
            pass
        # A new job advances RESULT_SEQ and CFG_SEQ.
        second = driver.run(make_job(2, rev=2))
        assert second["result_seq"] == 2 and second["cfg_seq"] == 2
        assert sim.jobs == 2
    finally:
        sim.close()


def test_safety_gate():
    sim, driver = build()
    try:
        driver.run(make_job(1))
        ps = {"verdict": "RECHECK", "actual": dict(ORDER), "reasons": ["touches_border"]}
        fw = {"verdict": "CHECK_PASS", "actual": [1, 1, 1], "reasons": 0}
        driver._check_safety(fw, ps, [])
        ps_pass = {"verdict": "CHECK_PASS", "actual": dict(ORDER), "reasons": []}
        fw_recheck = {"verdict": "RECHECK", "actual": [1, 1, 1], "reasons": 2}
        try:
            driver._check_safety(fw_recheck, ps_pass, [])
            raise AssertionError("more permissive PS verdict accepted")
        except CopProtocolError:
            pass
        fw_bad_count = {"verdict": "CHECK_PASS", "actual": [2, 0, 1], "reasons": 0}
        try:
            driver._check_safety(fw_bad_count, ps_pass, [])
            raise AssertionError("count mismatch accepted")
        except CopProtocolError:
            pass
    finally:
        sim.close()


def test_timeout_then_recovery():
    sim, driver = build(SimFaults(delay_s=0.02))
    try:
        job = make_job(1)
        job["timeout_cycles"] = 1000  # 10 us at 100 MHz; job sleeps ~60 ms
        try:
            driver.run(job)
            raise AssertionError("simulated watchdog accepted")
        except CopTimeoutError as error:
            assert error.error_name == "WATCHDOG", error.error_name
        sim.faults.timeout = False
        sim.faults.delay_s = 0.0
        result = driver.run(make_job(2, rev=2))
        assert result["decision"]["verdict"] == "CHECK_PASS" and result["result_seq"] == 1
        assert sim.error_name is None
    finally:
        sim.close()


def test_stale_result_never_passes():
    sim, driver = build(SimFaults(stale_result=True))
    try:
        try:
            driver.run(make_job(1))
            raise AssertionError("stale RESULT_SEQ accepted")
        except CopProtocolError as error:
            assert "RESULT_SEQ" in str(error), error
        sim.faults.stale_result = False
        result = driver.run(make_job(2, rev=2))
        assert result["decision"]["verdict"] == "CHECK_PASS" and result["result_seq"] == 1
        # Now a *second* job whose seq does not advance is rejected too.
        sim.faults.stale_result = True
        try:
            driver.run(make_job(3, rev=3))
            raise AssertionError("non-advancing RESULT_SEQ accepted")
        except CopProtocolError:
            pass
        sim.faults.stale_result = False
        third = driver.run(make_job(4, rev=4))
        assert third["result_seq"] == 2
    finally:
        sim.close()


def test_model_fault_and_reload():
    sim, driver = build(SimFaults(crc_mismatch=True))
    try:
        try:
            driver.run(make_job(1))
            raise AssertionError("CRC-mismatched model accepted")
        except CopConfigError as error:
            assert "BAD_MODEL" in str(error), error
        assert driver._model_loaded is None  # failed config forces a fresh load
        sim.faults.crc_mismatch = False
        result = driver.run(make_job(2, rev=2))
        assert result["decision"]["verdict"] == "CHECK_PASS"
        assert sim.jobs == 1
    finally:
        sim.close()


def test_real_dma_plane_is_not_pretended():
    try:
        PynqDmaPlane()
        raise AssertionError("unimplemented J08 data plane constructed")
    except NotImplementedError as error:
        assert "J08" in str(error)


def main():
    test_happy_and_duplicate()
    test_safety_gate()
    test_timeout_then_recovery()
    test_stale_result_never_passes()
    test_model_fault_and_reload()
    test_real_dma_plane_is_not_pretended()
    print("PASS: PS driver (submit/done/result window/FW parity/duplicate/stale/timeout/CRC recovery)")


if __name__ == "__main__":
    main()
