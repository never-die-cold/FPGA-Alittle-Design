"""MMIO service engine over the register sim: localization/ROI/rules/trace.

Covers PASS/FAIL, target_limit/empty PS gates, touch-border, low confidence,
target error, and a stale-result failure trace.
"""
import json
import sys
from pathlib import Path

import cv2

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
import cop_engine
import cop_regs as R
from cop_driver import CopDriver, CopProtocolError, SimDmaPlane
from cop_engine import CopEngine
from cop_mmio_sim import CopSim, SimFaults

FIXTURE = root / "data/evidence/2026-10-10-offline-inspection/fixtures/synthetic.png"
ORDER = {"bolt": 1, "nut": 1, "washer": 1}
OUT = root / "sim/build/vision/cop-engine-test"


def load_frame():
    frame = cv2.imread(str(FIXTURE))
    assert frame is not None and frame.shape == (720, 1280, 3)
    return frame


def make_engine(classes=("bolt", "nut", "washer"), faults=None, order=None):
    return CopEngine(order or ORDER, 0.8, 16, classes=tuple(classes), faults=faults)


def finish(engine):
    """Tests persist the trace, then consume; the service does the same."""
    engine.consume()
    status = engine.driver.status()
    assert not status & (R.STATUS_UNCONSUMED | R.STATUS_ACCEPTED | R.STATUS_RESULT_VALID), hex(status)


def test_pass_and_trace():
    engine = make_engine()
    try:
        round_dir = OUT / "pass"
        fields = engine(FIXTURE, round_dir, "chk000001")
        assert fields["status"] == "CHECK_PASS", fields["decision"]
        assert [t["class"] for t in fields["targets"]] == ["bolt", "nut", "washer"]
        assert fields["decision"]["actual"] == dict(ORDER)
        trace = json.loads((round_dir / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["kind"] == "cop_job" and trace["simulated"] is True
        assert trace["driver"]["fw"]["verdict"] == "CHECK_PASS"
        assert trace["driver"]["result_seq"] == 1 and trace["decision"] == fields["decision"]
        assert trace["compute_backend"].startswith("SCRIPTED")
        assert "SIM_ONLY" in trace["roi_quantization"]
        assert len(trace["frame"]["pixel_sha256"]) == 64
        assert len(trace["rois"]) == 3
        assert len((round_dir / trace["rois"][0]["path"]).read_bytes()) == 4096
        finish(engine)
        # Memory rounds use the same driver and produce the same verdict.
        memory = engine.inspect_frame(load_frame())
        assert memory["status"] == fields["status"] and memory["decision"] == fields["decision"]
        assert engine.driver.read("FW_DECISION") != 0
        finish(engine)
    finally:
        engine.close()


def test_count_mismatch():
    engine = make_engine(order={"bolt": 2, "nut": 1, "washer": 1})
    try:
        fields = engine(FIXTURE, OUT / "fail", "chk000001")
        assert fields["status"] == "CHECK_FAIL"
        assert fields["decision"]["missing"] == {"bolt": 1, "nut": 0, "washer": 0}
        finish(engine)
    finally:
        engine.close()


def test_ps_gates():
    engine = make_engine()
    original = cop_engine.detect_boxes
    try:
        cop_engine.detect_boxes = lambda frame: [(10 + 40 * i, 10, 40 + 40 * i, 60)
                                                 for i in range(12)]
        fields = engine.inspect_round(load_frame(), OUT / "limit", "chk000001")
        assert fields["status"] == "RECHECK" and fields["decision"]["reasons"] == ["target_limit"]
        assert engine.sim.jobs == 0
        trace = json.loads((OUT / "limit" / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["kind"] == "target_limit"
        cop_engine.detect_boxes = lambda frame: []
        fields = engine.inspect_round(load_frame(), OUT / "empty", "chk000002")
        assert fields["status"] == "CHECK_FAIL" and fields["targets"] == []
        assert fields["decision"]["actual"] == {"bolt": 0, "nut": 0, "washer": 0}
        trace = json.loads((OUT / "empty" / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["kind"] == "empty_scene_ps_gate" and trace["open"] == "OPEN-11"
    finally:
        cop_engine.detect_boxes = original
        engine.close()


def test_touch_border_is_stricter_than_firmware():
    engine = make_engine(classes=("bolt",), order={"bolt": 1, "nut": 0, "washer": 0})
    original = cop_engine.detect_boxes
    try:
        cop_engine.detect_boxes = lambda frame: [(0, 10, 40, 60)]
        fields = engine.inspect_round(load_frame(), OUT / "border", "chk000001")
        assert fields["status"] == "RECHECK"
        assert "touches_border" in fields["decision"]["reasons"]
        trace = json.loads((OUT / "border" / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["driver"]["fw"]["verdict"] == "CHECK_PASS"  # firmware lacks the border rule
        finish(engine)
    finally:
        cop_engine.detect_boxes = original
        engine.close()


def test_low_confidence():
    def low_margin(target_id, roi):
        margin = 100  # below MIN_MARGIN_Q=203 for min_score=0.8
        return {"class_id": target_id % 3, "logits": [0, 0, 0], "margin_q": margin,
                "score_q15": (margin * 32767 + 127) // 254}
    sim = CopSim(low_margin)
    driver = CopDriver(sim, SimDmaPlane(sim), dict(ORDER), 0.8, 16, 10)
    engine = CopEngine(ORDER, 0.8, 16, driver=driver, sim=sim)
    try:
        fields = engine(FIXTURE, OUT / "lowconf", "chk000001")
        assert fields["status"] == "RECHECK" and "low_score" in fields["decision"]["reasons"]
        trace = json.loads((OUT / "lowconf" / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["driver"]["fw"]["reasons_names"] == ["low_score"]
        finish(engine)
    finally:
        sim.close()


def test_target_error():
    engine = make_engine(faults=SimFaults(target_error=0))
    try:
        fields = engine(FIXTURE, OUT / "target-error", "chk000001")
        assert fields["status"] == "RECHECK"
        assert fields["targets"][0]["class"] == "bolt"  # count parity with cop_judge
        assert fields["targets"][0]["score"] == 0.0
        trace = json.loads((OUT / "target-error" / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["driver"]["fw"]["reasons_names"] == ["low_score"]
        finish(engine)
    finally:
        engine.close()


def test_failure_trace_and_recovery():
    engine = make_engine(faults=SimFaults(stale_result=True))
    try:
        try:
            engine(FIXTURE, OUT / "stale", "chk000001")
            raise AssertionError("stale result became a packet")
        except CopProtocolError:
            pass
        trace = json.loads((OUT / "stale" / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["kind"] == "cop_failure" and "RESULT_SEQ" in trace["error"]
        engine.sim.faults.stale_result = False
        fields = engine(FIXTURE, OUT / "recovered", "chk000002")
        assert fields["status"] == "CHECK_PASS"
        finish(engine)
    finally:
        engine.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    test_pass_and_trace()
    test_count_mismatch()
    test_ps_gates()
    test_touch_border_is_stricter_than_firmware()
    test_low_confidence()
    test_target_error()
    test_failure_trace_and_recovery()
    print("PASS: cop engine (localize/ROI/sim submit/rules/trace/border/low-conf/error/recovery)")


if __name__ == "__main__":
    main()
