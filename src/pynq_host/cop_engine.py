"""LIVE service engine backed by the PS MMIO driver (sim now, real MMIO later).

Flow per round: capture frame -> localization -> scene-gray-border-padding-v1 ROI
-> SIM INT8 quantization -> C03 config/data/submit -> result window -> PS rules.
Every hardware round writes ``cop_trace.json`` next to packet.json for audit.

Honesty boundary: the compute backend is a simulated register model and a
scripted/image-derived classifier.  ``prototype`` remains true in the service;
this path is 模拟跑通, never 板上跑通 and never a validated recognition result.
The ROI quantization uses S_input=1/127 only because the sim needs bytes; C02
requires S_input from a formal manifest, which J05/J06 has not produced.
"""
import hashlib
import json
import re
from pathlib import Path

import cv2
import numpy as np

import cop_regs as R
from cop_driver import CopDriver, CopError, CopProtocolError, SimDmaPlane
from cop_mmio_sim import CopSim, SimFaults, scripted_compute
from inspection_rules import effective_policy, judge

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sim/vision"))
from localization_opencv import detect_boxes
from roi_preprocess import PREPROCESS_VERSION, preprocess

MODEL_PAYLOAD = b"COP-SIM-DIAGNOSTIC-MODEL-V1"  # not a formal C02 payload
SIM_S_INPUT = 1.0 / 127.0  # SIM ONLY: C02 §3.2 requires this from a manifest


def quantize_roi(canvas):
    """SIM-ONLY symmetric quantization: q = round((p/255)/S_input), clamp [-127,127]."""
    scaled = np.floor(canvas.astype(np.float32) / 255.0 / SIM_S_INPUT + 0.5)
    return np.clip(scaled, -127, 127).astype(np.int8).tobytes()


def atomic_json(path, payload):
    pending = path.with_name(path.name + ".pending")
    pending.write_bytes(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                   allow_nan=False, indent=1).encode("utf-8"))
    pending.replace(path)


class CopEngine:
    label = "COP_SIM"

    def __init__(self, order, min_score, max_targets=16, policy_max=None,
                 classes=("bolt", "nut", "washer"), faults=None, delay_s=0.0,
                 driver=None, sim=None, compute_label=None, source_config_id=None):
        self.order = dict(order)
        self.min_score = float(min_score)
        self.max_targets = max_targets
        self.policy = effective_policy(max_targets, policy_max)
        self.faults = faults or SimFaults()
        self.compute_label = compute_label or (
            "SCRIPTED " + "/".join(classes) if classes else "SYNTHETIC_ROI")
        self._owns_sim = sim is None
        if driver is None:
            if delay_s and not self.faults.delay_s:
                self.faults.delay_s = delay_s
            compute = scripted_compute(list(classes)) if classes else None
            sim = CopSim(compute, self.faults)
            driver = CopDriver(sim, SimDmaPlane(sim), self.order, self.min_score,
                               max_targets, policy_max, model_payload=MODEL_PAYLOAD)
        self.sim = sim if sim is not None else getattr(driver, "sim", None)
        self.driver = driver
        self.source_config_id = source_config_id if source_config_id is not None else \
            (R.crc32(PREPROCESS_VERSION.encode()) & 0xFFFFFFFF)
        self.job_id = 0
        self.last_trace = None
        self._pending_consume = None
        self._last_round_dir = None

    def close(self):
        if self._owns_sim and self.sim is not None:
            self.sim.close()

    def consume(self):
        """Called by the service after the packet is persisted (A2 order)."""
        if self._pending_consume is None:
            return
        result = self._pending_consume
        try:
            status_after = self.driver.consume(result)
            if self.last_trace is not None and self.last_trace.get("kind") == "cop_job":
                self.last_trace["consume"] = {
                    "result_seq": result["result_seq"], "status_after": status_after,
                    "unconsumed": bool(status_after & R.STATUS_UNCONSUMED)}
                self._write_trace(self._last_round_dir, self.last_trace)
        finally:
            self._pending_consume = None

    def __call__(self, capture_path, round_dir, request_id):
        raw = Path(capture_path).read_bytes()
        frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("capture is not a decodable color image")
        fields = self._fields(frame, Path(round_dir), request_id)
        return fields

    def inspect_frame(self, frame):
        return self._fields(frame, None, None)

    def inspect_round(self, frame, round_dir, request_id):
        """Same as __call__ but with an already-decoded frame (tests/diagnostics)."""
        return self._fields(frame, Path(round_dir), request_id)

    def _fields(self, frame, round_dir, request_id):
        if (not isinstance(frame, np.ndarray) or frame.dtype != np.uint8
                or frame.ndim != 3 or frame.shape[2] != 3 or min(frame.shape[:2]) < 1):
            raise ValueError("frame must be nonempty uint8 BGR")
        self._last_round_dir = round_dir
        height, width = frame.shape[:2]
        frame_meta = {"width": width, "height": height,
                      "pixel_sha256": hashlib.sha256(frame.tobytes()).hexdigest()}
        boxes = detect_boxes(frame)
        empty = judge([], self.order, self.min_score, self.max_targets, self.policy)
        if len(boxes) > self.policy:
            decision = {**empty, "verdict": "RECHECK", "actual": None, "delta": None,
                        "missing": None, "extra": None, "reasons": ["target_limit"]}
            trace = {"kind": "target_limit", "simulated": True, "frame": frame_meta,
                     "target_count": len(boxes), "policy_max": self.policy}
            self.last_trace = trace
            self._write_trace(round_dir, trace)
            return {"status": "RECHECK",
                    "targets": [{"target_id": i, "bbox": list(box), "class": None,
                                 "score": 0.0} for i, box in enumerate(boxes)],
                    "decision": decision, "width": width, "height": height}
        if not boxes:
            # C03 §8 wants CHECK_FAIL with zero actuals for a valid empty scene.
            # v0 hardware cannot express empty (OPEN-11), so this is a PS-side gate.
            trace = {"kind": "empty_scene_ps_gate", "simulated": True, "frame": frame_meta,
                     "open": "OPEN-11", "target_count": 0}
            self.last_trace = trace
            self._write_trace(round_dir, trace)
            return {"status": empty["verdict"], "targets": [], "decision": empty,
                    "width": width, "height": height}

        crops = [preprocess(frame, box)[0] for box in boxes]
        targets, descriptors, ps_targets = [], [], []
        for index, (box, crop) in enumerate(zip(boxes, crops)):
            x0, y0, x1, y1 = box
            border = x0 == 0 or y0 == 0 or x1 == width or y1 == height
            targets.append({"target_id": index, "roi": quantize_roi(crop),
                            "flags": R.FLAG_TOUCH_BORDER if border else 0})
            descriptors.append({"target_id": index, "bbox": list(box),
                                "touches_border": border})
            ps_targets.append({"target_id": index, "bbox": list(box),
                               "touches_border": border})
        self.job_id = (self.job_id + 1) & 0xFFFFFFFF
        capture_id = self._capture_id(request_id)
        job = {"targets": targets, "job_id": self.job_id,
               "work_order_rev": self.job_id, "capture_id": capture_id,
               "source_config_id": self.source_config_id,
               "timeout_cycles": R.COP_HZ}  # 1 s; sim jobs are milliseconds
        try:
            result = self.driver.run(job)
        except CopError as error:
            try:
                snapshot = self.driver.terminal_snapshot("engine_failure")
            except CopError:
                snapshot = None
            trace = {"kind": "cop_failure", "simulated": True,
                     "compute_backend": self.compute_label,
                     "protocol_check": request_id, "error": str(error),
                     "error_type": type(error).__name__,
                     "error_code": getattr(error, "error_code", None),
                     "sim_error": getattr(self.driver.transport, "error_name", None),
                     "frame": frame_meta,
                     "job_id": self.job_id, "capture_id": capture_id,
                     "rois": self._write_rois(round_dir, targets),
                     "descriptors": descriptors,
                     "terminal": snapshot, "last_terminal": self.driver.last_terminal}
            self.last_trace = trace
            self._write_trace(round_dir, trace)  # persist evidence before CONSUME
            if snapshot and snapshot["status"] & R.STATUS_UNCONSUMED:
                try:
                    self.driver.consume_current("engine_failure")
                except CopError:
                    pass  # next round sees the stale terminal and recovers it
            raise

        packet_targets = []
        judge_targets = []
        for descriptor, item in zip(descriptors, result["targets"]):
            packet_targets.append({"target_id": item["target_id"],
                                   "bbox": descriptor["bbox"],
                                   "class": item["class"], "score": item["score"]})
            judge_targets.append({"class": item["class"], "score": item["score"],
                                  "touches_border": descriptor["touches_border"]})
        decision = judge(judge_targets, self.order, self.min_score,
                         self.max_targets, self.policy)
        if decision != result["decision"]:
            raise CopProtocolError("engine decision differs from driver's checked decision")
        trace = {"kind": "cop_job", "simulated": True,
                 "compute_backend": self.compute_label,
                 "preprocess": PREPROCESS_VERSION,
                 "roi_quantization": f"SIM_ONLY S_input={SIM_S_INPUT:.10f}",
                 "protocol_check": request_id,
                 "frame": frame_meta,
                 "work_order": dict(self.order), "policy_max": self.policy,
                 "min_score": self.min_score,
                 "rois": self._write_rois(round_dir, targets),
                 "descriptors": descriptors, "driver": result["trace"],
                 "decision": decision}
        self.last_trace = trace
        self._write_trace(round_dir, trace)
        self._last_round_dir = round_dir
        self._pending_consume = result  # service calls consume() after packet persist
        return {"status": decision["verdict"], "targets": packet_targets,
                "decision": decision, "width": width, "height": height}

    def _capture_id(self, request_id):
        if request_id:
            digits = re.search(r"(\d+)$", request_id)
            if digits:
                return int(digits.group(1)) & 0xFFFFFFFF
        return self.job_id

    def _write_rois(self, round_dir, targets):
        if round_dir is None:
            return []
        roi_dir = round_dir / "cop"
        roi_dir.mkdir(parents=True, exist_ok=True)
        metadata = []
        for index, target in enumerate(targets):
            name = f"roi_{index:03d}.bin"
            (roi_dir / name).write_bytes(target["roi"])
            metadata.append({"index": index, "path": f"cop/{name}",
                             "bytes_sha256": hashlib.sha256(target["roi"]).hexdigest()})
        return metadata

    def _write_trace(self, round_dir, trace):
        if round_dir is None:
            return
        round_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(round_dir / "cop_trace.json", trace)


def cop_engine(order, min_score, max_targets=16, policy_max=None, **kwargs):
    """Factory matching vision_live_service's engine contract."""
    return CopEngine(order, min_score, max_targets, policy_max, **kwargs)
