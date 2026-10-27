"""PS driver A1/A2 tests: submit -> ACCEPTED -> terminal -> persist -> CONSUME.

Covers NO_ACK/HW_TIMEOUT software watchdogs, mutually exclusive terminals,
CONSUME atomicity, stale-result rejection, CRC recovery, duplicate jobs, and
the explicit PS AXI base rule.
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
import cop_regs as R
from cop_regs import CopBusError
from cop_driver import (CopConfigError, CopDriver, CopHardwareTimeout, CopNoAck,
                        CopProtocolError, CopStaleResult, CopTimeoutError,
                        PynqDmaPlane, PynqMmio, SimDmaPlane)
from cop_mmio_sim import CopSim, SimFaults, scripted_compute

ORDER = {"bolt": 1, "nut": 1, "washer": 1}


def make_job(job_id, rev=1, count=3):
    return {"targets": [{"target_id": index, "roi": bytes([index + 1]) * 4096,
                         "flags": 0} for index in range(count)],
            "job_id": job_id, "work_order_rev": rev, "capture_id": 10 + job_id,
            "source_config_id": 4}


def build(faults=None, classes=("bolt", "nut", "washer"), job_timeout=2.0,
          accept_timeout=0.5):
    sim = CopSim(scripted_compute(list(classes)), faults)
    driver = CopDriver(sim, SimDmaPlane(sim), dict(ORDER), 0.8, 16, 10,
                       job_timeout_s=job_timeout, accept_timeout_s=accept_timeout,
                       config_timeout_s=0.5)
    return sim, driver


def clean(driver):
    status = driver.status()
    return not status & (R.STATUS_UNCONSUMED | R.STATUS_ACCEPTED
                         | R.STATUS_RESULT_VALID | R.STATUS_ERROR
                         | R.STATUS_DONE | R.STATUS_TIMEOUT)


def test_happy_consume_duplicate():
    sim, driver = build()
    try:
        result = driver.run(make_job(1))
        assert result["decision"]["verdict"] == "CHECK_PASS"
        assert [t["class"] for t in result["targets"]] == ["bolt", "nut", "washer"]
        assert result["trace"]["fw"]["verdict"] == "CHECK_PASS"
        assert result["trace"]["accepted"] is True
        assert result["trace"]["unconsumed"] is True
        assert result["result_seq"] == 1 and result["cfg_seq"] == 1
        assert driver.status() & R.STATUS_UNCONSUMED
        # A2: a new submit is rejected while the result is unconsumed.
        try:
            driver.run(make_job(2, rev=2))
            raise AssertionError("submit accepted with UNCONSUMED result")
        except CopStaleResult:
            pass
        assert sim.jobs == 1
        # Persist done -> CONSUME clears receipt/terminal/result, keeps seq.
        driver.consume(result)
        assert clean(driver) and driver.read("RESULT_SEQ") == 1
        assert driver.read("ERROR_CODE") == 0
        ops = sim.trace()["ops"]
        assert ("W", "CTRL", R.CTRL_CONSUME) in ops
        assert not any(op == "W" and name == "CTRL" and value in
                       (R.CTRL_CLEAR_DONE, R.CTRL_CLEAR_ERROR,
                        R.CTRL_CLEAR_DONE | R.CTRL_CLEAR_ERROR)
                       for op, name, value in ops)
        # Next job advances RESULT_SEQ and is cached by JOB_ID after CONSUME.
        second = driver.run(make_job(2, rev=2))
        assert second["result_seq"] == 2 and second["cfg_seq"] == 2
        driver.consume(second)
        again = driver.run(make_job(2, rev=2))
        assert again["duplicate"] is True and again["result_seq"] == 2
        assert sim.jobs == 2
        changed = make_job(2, rev=2)
        changed["targets"][0]["roi"] = b"\x7f" * 4096
        try:
            driver.run(changed)
            raise AssertionError("JOB_ID reuse with different targets accepted")
        except CopProtocolError:
            pass
    finally:
        sim.close()


def test_consume_validation():
    sim, driver = build()
    try:
        result = driver.run(make_job(1))
        wrong = {"result_seq": 999}
        try:
            driver.consume(wrong)
            raise AssertionError("CONSUME with a wrong seq accepted")
        except CopProtocolError:
            pass
        assert driver.status() & R.STATUS_UNCONSUMED
        driver.consume(result)
        try:
            driver.consume(result)
            raise AssertionError("CONSUME without a terminal accepted")
        except CopProtocolError:
            pass
    finally:
        sim.close()


def test_safety_gate():
    sim, driver = build()
    try:
        result = driver.run(make_job(1))
        driver.consume(result)
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


def test_hardware_timeout_and_recovery():
    sim, driver = build(SimFaults(delay_s=0.01))
    try:
        job = make_job(1)
        job["timeout_cycles"] = 1000  # 10 us; hardware watchdog wins
        try:
            driver.run(job)
            raise AssertionError("hardware watchdog accepted")
        except CopTimeoutError as error:
            assert error.error_code == 13 and error.error_name == "WATCHDOG", error
        assert clean(driver)
        sim.faults.timeout = False
        sim.faults.delay_s = 0.0
        result = driver.run(make_job(2, rev=2))
        assert result["decision"]["verdict"] == "CHECK_PASS" and result["result_seq"] == 1
        driver.consume(result)
    finally:
        sim.close()


def test_ps_hw_timeout():
    sim, driver = build(SimFaults(hang=True), job_timeout=0.1, accept_timeout=0.5)
    try:
        try:
            driver.run(make_job(1))
            raise AssertionError("accepted-but-hung job passed")
        except CopHardwareTimeout as error:
            assert error.error_name == "HW_TIMEOUT", error
        assert clean(driver)
        sim.faults.hang = False
        result = driver.run(make_job(2, rev=2))
        assert result["result_seq"] == 1
        driver.consume(result)
    finally:
        sim.close()


def test_no_ack():
    sim, driver = build(SimFaults(no_ack=True), accept_timeout=0.1)
    try:
        try:
            driver.run(make_job(1))
            raise AssertionError("missing ACCEPTED passed")
        except CopNoAck as error:
            assert error.error_name == "NO_ACK", error
        assert clean(driver)
        sim.faults.no_ack = False
        result = driver.run(make_job(2, rev=2))
        assert result["result_seq"] == 1
        driver.consume(result)
    finally:
        sim.close()


def test_stale_result_and_recovery():
    sim, driver = build(SimFaults(stale_result=True))
    try:
        try:
            driver.run(make_job(1))
            raise AssertionError("stale RESULT_SEQ accepted")
        except CopProtocolError as error:
            assert "RESULT_SEQ" in str(error), error
        assert driver.status() & R.STATUS_UNCONSUMED
        driver.consume_current("stale")
        assert clean(driver)
        sim.faults.stale_result = False
        result = driver.run(make_job(2, rev=2))
        assert result["result_seq"] == 1
        driver.consume(result)
        # A stale second result is rejected and recoverable.
        sim.faults.stale_result = True
        try:
            driver.run(make_job(3, rev=3))
            raise AssertionError("non-advancing RESULT_SEQ accepted")
        except CopProtocolError:
            pass
        driver.consume_current("stale")
        sim.faults.stale_result = False
        third = driver.run(make_job(4, rev=4))
        assert third["result_seq"] == 2
        driver.consume(third)
    finally:
        sim.close()


def test_model_fault_and_reload():
    sim, driver = build(SimFaults(crc_mismatch=True))
    try:
        try:
            driver.run(make_job(1))
            raise AssertionError("CRC-mismatched model accepted")
        except CopConfigError as error:
            assert "error_code=1" in str(error), error
        assert clean(driver)
        sim.faults.crc_mismatch = False
        result = driver.run(make_job(2, rev=2))
        assert result["decision"]["verdict"] == "CHECK_PASS"
        driver.consume(result)
        assert sim.jobs == 1
    finally:
        sim.close()


def test_pynq_transport_round():
    sim = CopSim(scripted_compute(["bolt", "nut", "washer"]))
    class WindowMmio:
        def __init__(self, backing, size=0x1000):
            self.backing, self.size = backing, size
        def _offset(self, offset):
            if not 0 <= offset < self.size:
                raise ValueError(f"MMIO offset 0x{offset:x} outside window")
            return offset
        def read(self, offset):
            return self.backing.read32(self._offset(offset))
        def write(self, offset, value):
            self.backing.write32(self._offset(offset), value)
    base = 0x40000000
    transport = PynqMmio(WindowMmio(sim), base)
    driver = CopDriver(transport, SimDmaPlane(sim), dict(ORDER), 0.8, 16, 10,
                       job_timeout_s=2.0, accept_timeout_s=0.5, config_timeout_s=0.5)
    try:
        info = driver.probe()
        assert info["ip_id"] == R.IP_ID and info["ready"] is True
        assert info["unconsumed"] is False and info["busy"] is False
        result = driver.run(make_job(1))
        driver.consume(result)
        assert sim.jobs == 1
    finally:
        sim.close()


class _FakeMmio:
    def __init__(self):
        self.calls = []

    def read(self, addr):
        self.calls.append(("r", addr))
        return 0

    def write(self, addr, value):
        self.calls.append(("w", addr, value))


class _FakeBuffer:
    def __init__(self, size, base):
        self.data = bytearray(size)
        self.physical_address = base

    @property
    def nbytes(self):
        return len(self.data)

    def __setitem__(self, key, value):
        self.data[key] = bytes(value)

    def flush(self):
        pass

    def freebuffer(self):
        pass


def test_real_dma_plane_guards():
    buffers = []

    def allocate(shape, dtype):
        buffer = _FakeBuffer(shape[0], 0x40000000 + 0x10000 * len(buffers))
        buffers.append(buffer)
        return buffer

    plane = PynqDmaPlane(PynqMmio(_FakeMmio(), 0x40010000),
                         PynqMmio(_FakeMmio(), 0x40020000),
                         PynqMmio(_FakeMmio(), 0x40000000), allocate)
    assert plane.addresses["weight"] == 0x40000000
    assert plane.addresses["roi"] == 0x40010000
    try:
        PynqDmaPlane(None, None, None, allocate, max_targets=16)
        raise AssertionError("ROI packet above 15 targets accepted")
    except ValueError:
        pass
    try:
        plane.load_model(0x1234, b"\x01")
        raise AssertionError("weight load accepted a foreign address")
    except CopBusError:
        pass
    try:
        plane.load_rois(plane.addresses["roi"], [bytes(4096)] * 16, 4096)
        raise AssertionError("16 ROIs overran the 16-bit DMA length")
    except CopBusError:
        pass
    assert plane.load_descriptors(plane.addresses["descriptor"], [{"target_id": 0}]) is None


def test_hardware_commit_revalidates_model():
    class Hardware:
        def __init__(self):
            self.values = {}
            self.events = []
        def read32(self, offset):
            return self.values.get(offset, 0)
        def write32(self, offset, value):
            self.values[offset] = value
            if offset == R.OFFSETS["CFG_COMMIT"]:
                self.values[R.OFFSETS["CFG_APPLIED"]] = self.values[R.OFFSETS["CFG_SEQ"]]
                self.events.append("commit")
    class Plane:
        def load_model(self, addr, payload):
            hardware.events.append("model")
        def load_rois(self, addr, rois, stride):
            hardware.events.append("roi")
        def load_descriptors(self, addr, descriptors):
            pass
    hardware = Hardware()
    driver = CopDriver(hardware, Plane(), dict(ORDER), 0.8, dma_after_commit=True)
    for job_id in (1, 2):
        driver._configure(make_job(job_id), 3)
    assert hardware.events == ["commit", "model", "roi", "commit", "model", "roi"]


def test_ps_base_rule():
    try:
        PynqMmio(object())
        raise AssertionError("PynqMmio accepted a default base")
    except TypeError:
        pass
    try:
        PynqMmio(object(), None)
        raise AssertionError("PynqMmio accepted a missing base")
    except ValueError:
        pass
    class FakeMmio:
        def __init__(self):
            self.calls = []
        def read(self, addr):
            self.calls.append(("r", addr))
            return 0
        def write(self, addr, value):
            self.calls.append(("w", addr, value))
    fake = FakeMmio()
    transport = PynqMmio(fake, 0x40000000)
    transport.write32(0x10, 7)
    assert fake.calls == [("w", 0x10, 7)]  # PYNQ MMIO already applies the base


def main():
    test_happy_consume_duplicate()
    test_consume_validation()
    test_safety_gate()
    test_hardware_timeout_and_recovery()
    test_ps_hw_timeout()
    test_no_ack()
    test_stale_result_and_recovery()
    test_model_fault_and_reload()
    test_pynq_transport_round()
    test_real_dma_plane_guards()
    test_hardware_commit_revalidates_model()
    test_ps_base_rule()
    print("PASS: PS driver A1/A2 (accepted/unconsumed/consume/NO_ACK/HW_TIMEOUT/stale/CRC/PynqMmio)")


if __name__ == "__main__":
    main()
