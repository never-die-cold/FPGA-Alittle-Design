"""C03/J04 register-level fake coprocessor for PS-side driver and service tests.

This is NOT hardware. It mirrors docs/contracts/coprocessor-integration-v0.md §4:
PS-only shadow writes, CFG_COMMIT atomic apply, J04 firmware's START/result window
flow, sticky DONE/ERROR/TIMEOUT with W1C, ABORT/SOFT_RESET, and a watchdog.

It intentionally keeps VERSION/CAPABILITY/ERROR_CODE at 0 like J04 (OPEN-9).
Sim-only identifiers (descriptor flag bits, error names) live in cop_regs.py and
must not be used as a frozen hardware contract.
"""
import threading
import time
from collections import deque

import cop_regs as R


class CopBusError(R.CopBusError):
    """Kept as a sim module alias for tests; the shared class lives in cop_regs."""


class SimFaults:
    """Fault injection knobs; every one is sim-only."""

    def __init__(self, timeout=False, crc_mismatch=False, short_payload=False,
                 stale_result=False, target_error=None, low_conf=None, delay_s=0.0):
        self.timeout = timeout
        self.crc_mismatch = crc_mismatch
        self.short_payload = short_payload
        self.stale_result = stale_result
        self.target_error = target_error
        self.low_conf = low_conf
        self.delay_s = delay_s


def scripted_compute(classes):
    """Deterministic classifier: target i gets classes[i % len(classes)]."""
    if not classes or any(name not in R.CLASSES for name in classes):
        raise ValueError("scripted classes must be bolt/nut/washer")
    def compute(target_id, roi):
        class_id = R.CLASSES.index(classes[target_id % len(classes)])
        logits = [-127, -127, -127]
        logits[class_id] = 127
        margin = 254
        return {"class_id": class_id, "logits": logits, "margin_q": margin,
                "score_q15": 32767}
    return compute


def synthetic_compute(target_id, roi):
    """Deterministic image-derived stand-in; not a validated classifier.

    Uses the ROI bytes so different frames produce different results, and is
    labelled SIM in every packet/trace. Never present as hardware recognition.
    """
    value = R.crc32(bytes(roi) + bytes((target_id & 0xFF,)))
    logits = [(value >> (8 * i)) & 0x7F for i in range(3)]
    logits = [value - 64 for value in logits]
    order = sorted(range(3), key=lambda index: (logits[index], -index), reverse=True)
    margin = min(254, max(0, logits[order[0]] - logits[order[1]]))
    return {"class_id": order[0], "logits": logits, "margin_q": margin,
            "score_q15": (margin * 32767 + 127) // 254}


class CopSim:
    """Thread-backed register model; one job at a time, like the J04 firmware."""

    def __init__(self, compute=None, faults=None, poll_s=0.0):
        self.compute = compute or synthetic_compute
        self.faults = faults or SimFaults()
        self.poll_s = poll_s
        self._lock = threading.RLock()
        self._cv = threading.Condition(self._lock)
        self._closed = False
        self._pending = False
        self._shadow = {}
        self._memory = {}
        self._descriptors = []
        self._rois = []
        self._results = []
        self._result_index = 0
        self._result_seq = 0
        self._fw_counts = 0
        self._fw_decision = 0
        self._busy = False
        self._dma_busy = False
        self._done = False
        self._error = False
        self._timeout = False
        self._result_valid = False
        self._error_name = None
        self._cfg_seq = 0
        self._cfg_applied = 0
        self._cfg_valid = False
        self._model_ok = False
        self._loaded = None
        self._generation = 0
        self._job_started = 0.0
        self._dma_bytes = 0
        self._perf_cycles = 0
        self._ops = deque(maxlen=256)
        self._jobs = 0
        self._worker = threading.Thread(target=self._worker_loop, daemon=True,
                                        name="cop-sim-firmware")
        self._worker.start()

    # ---- register access -------------------------------------------------
    def read32(self, offset):
        with self._lock:
            name = self._name(offset)
            if name == "CTRL":
                return 0
            if name not in R.PS_READABLE:
                raise CopBusError(f"PS read of write-only {name}")
            self._ops.append(("R", name, None))
            return self._read_reg(name)

    def write32(self, offset, value):
        if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
            raise ValueError("register value must be uint32")
        with self._lock:
            name = self._name(offset)
            if name not in R.PS_WRITABLE:
                raise CopBusError(f"PS write of read-only {name}")
            self._ops.append(("W", name, value))
            if name == "CTRL":
                self._write_ctrl(value)
            elif name == "CFG_SEQ":
                if value == 0:
                    raise CopBusError("CFG_SEQ must be non-zero")
                self._cfg_seq = value
                self._cfg_valid = False  # OPEN-3 conservative default
                self._shadow[name] = value
            elif name == "CFG_COMMIT":
                if value == 1:
                    self._commit()
            elif name == "RESULT_INDEX":
                if value >= R.MAX_TARGETS:
                    raise CopBusError("RESULT_INDEX out of range")
                self._result_index = value
            else:
                self._shadow[name] = value
                if name in ("MODEL_ID", "WEIGHT_ADDR", "WEIGHT_BYTES", "WEIGHT_CRC32"):
                    self._refresh_model_valid()

    def _name(self, offset):
        if type(offset) is not int or offset & 3:
            raise CopBusError(f"unaligned offset {offset!r}")
        if offset not in R.BY_OFFSET:
            raise CopBusError(f"unmapped offset 0x{offset:03x}")
        return R.BY_OFFSET[offset]

    def _read_reg(self, name):
        if name == "IP_ID":
            return R.IP_ID
        if name in ("VERSION", "CAPABILITY", "ERROR_CODE"):
            return 0  # J04/OPEN-9: not implemented, do not infer meaning
        if name in ("CFG_SEQ",):
            return self._cfg_seq
        if name == "CFG_APPLIED":
            return self._cfg_applied
        if name == "STATUS":
            return self._status()
        if name == "RESULT_META":
            return self._result_word("meta")
        if name == "RESULT_LOGITS":
            return self._result_word("logits")
        if name == "RESULT_SCORE":
            return self._result_word("score")
        if name == "RESULT_SEQ":
            return self._result_seq
        if name == "PERF_CYCLES":
            return self._perf_cycles
        if name == "DMA_BYTES":
            return self._dma_bytes
        if name == "FW_ACTUAL_COUNTS":
            return self._fw_counts
        if name == "FW_DECISION":
            return self._fw_decision
        return self._shadow.get(name, 0)

    def _status(self):
        status = 0
        if not self._busy and self._cfg_valid and self._model_ok \
                and not self._error and not self._timeout:
            status |= R.STATUS_READY
        if self._busy:
            status |= R.STATUS_BUSY
        if self._done:
            status |= R.STATUS_DONE
        if self._error:
            status |= R.STATUS_ERROR
        if self._timeout:
            status |= R.STATUS_ERROR | R.STATUS_TIMEOUT
        if self._cfg_valid:
            status |= R.STATUS_CFG_VALID
        if self._model_ok:
            status |= R.STATUS_MODEL_VALID
        if self._result_valid:
            status |= R.STATUS_RESULT_VALID
        if self._dma_busy:
            status |= R.STATUS_DMA_BUSY
        return status

    def _write_ctrl(self, value):
        if value & R.CTRL_START:
            raise CopBusError("PS may not write START")
        if value & R.CTRL_ABORT:
            if self._busy:
                self._generation += 1
                self._busy = False
                self._done = False
                self._result_valid = False
                self._error = True
                self._error_name = "ABORTED"
            else:  # OPEN-10: J04 sets ERROR for an idle ABORT
                self._error = True
                self._error_name = "ABORTED"
        if value & R.CTRL_SOFT_RESET:
            self._generation += 1
            self._busy = False
            self._done = False
            self._timeout = False
            self._error = False
            self._error_name = None
            self._result_valid = False
            self._fw_counts = 0
            self._fw_decision = 0
            self._results = []  # keep cfg/model per C03-P10
        if value & R.CTRL_CLEAR_DONE:
            self._done = False
            self._result_valid = False
        if value & R.CTRL_CLEAR_ERROR:
            self._error = False
            self._timeout = False
            self._error_name = None
        # IRQ_ACK has no observable source in this model.

    def _commit(self):
        if self._busy:
            raise CopBusError("CFG_COMMIT while busy")  # SLVERR, not queued
        if self._bad_config():
            self._cfg_valid = False
            if not self._error:  # C03 §9: keep the first cause
                self._error = True
                self._error_name = "BAD_CONFIG"
            return
        self._cfg_applied = self._cfg_seq
        self._cfg_valid = True
        self._pending = True
        self._cv.notify_all()

    def _bad_config(self):
        shadow = self._shadow
        count = shadow.get("ROI_COUNT", 0)
        if not 1 <= count <= R.MAX_TARGETS:
            return True
        if shadow.get("TIMEOUT_CYCLES", 0) <= 0:
            return True
        if shadow.get("ROI_STRIDE", 0) != R.ROI_BYTES \
                or shadow.get("RESULT_STRIDE", 0) != R.RESULT_BYTES:
            return True
        for name in ("WEIGHT_ADDR", "TARGET_DESC_ADDR", "ROI_ADDR", "RESULT_ADDR"):
            if shadow.get(name, 0) & 63:
                return True
        if shadow.get("MIN_MARGIN_Q", 0) > 254:
            return True
        if not self._model_ok:
            return True
        return self._bad_descriptors(count)

    def _bad_descriptors(self, count):
        if len(self._descriptors) != count:
            return True
        ids, indices = set(), set()
        for item in self._descriptors:
            if not isinstance(item, dict):
                return True
            target_id, flags = item.get("target_id"), item.get("flags", 0)
            roi_index = item.get("roi_index")
            if type(target_id) is not int or not 0 <= target_id <= 0xFFFF \
                    or target_id in ids or type(flags) is not int or flags & ~3 \
                    or type(roi_index) is not int or not 0 <= roi_index < count \
                    or roi_index in indices or item.get("reserved", 0) != 0:
                return True
            ids.add(target_id)
            indices.add(roi_index)
        return False

    # ---- PS data plane (sim; real path needs DataMover/AXI DMA) ------------
    def load_weights(self, addr, payload):
        if not isinstance(payload, (bytes, bytearray)) or not payload:
            raise ValueError("weight payload must be non-empty bytes")
        if addr & 63:
            raise CopBusError("weight address must be 64-byte aligned")
        with self._lock:
            if self._busy:
                raise CopBusError("weight load while busy")
            self._dma_busy = True
            effective = bytes(payload)
            if self.faults.short_payload:
                effective = effective[:-1]  # short DMA packet
            crc = R.crc32(effective)
            if self.faults.crc_mismatch:
                crc ^= 1
            self._memory[addr] = effective
            self._loaded = {"addr": addr, "bytes": len(effective), "crc32": crc}
            self._dma_bytes = len(effective)
            self._refresh_model_valid()
            if not self._model_ok:
                self._error = True
                self._error_name = ("DMA_SHORT" if len(effective) != self._shadow.get("WEIGHT_BYTES")
                                    else "BAD_MODEL")
            self._dma_busy = False
            return {"bytes": len(effective), "crc32": crc}

    def load_rois(self, addr, rois, stride=R.ROI_BYTES):
        if stride != R.ROI_BYTES or addr & 63:
            raise CopBusError("ROI address/stride violates v0")
        with self._lock:
            if len(rois) != self._shadow.get("ROI_COUNT"):
                raise CopBusError("ROI count does not match ROI_COUNT")
            for index, roi in enumerate(rois):
                if not isinstance(roi, (bytes, bytearray)) or len(roi) != R.ROI_BYTES:
                    raise ValueError("each ROI must be 4096 bytes")
                self._memory[addr + index * stride] = bytes(roi)
            self._rois = [bytes(roi) for roi in rois]
            self._dma_bytes += len(rois) * R.ROI_BYTES
            return len(rois) * R.ROI_BYTES

    def load_descriptors(self, addr, descriptors):
        if addr & 63:
            raise CopBusError("descriptor address must be 64-byte aligned")
        with self._lock:
            self._descriptors = [dict(item) for item in descriptors]

    def _refresh_model_valid(self):
        shadow, loaded = self._shadow, self._loaded
        self._model_ok = bool(
            loaded and shadow.get("WEIGHT_ADDR") == loaded["addr"]
            and shadow.get("WEIGHT_BYTES") == loaded["bytes"]
            and shadow.get("WEIGHT_CRC32") == loaded["crc32"]
            and shadow.get("MODEL_ID", 0) != 0)

    # ---- firmware model ---------------------------------------------------
    def _worker_loop(self):
        while True:
            with self._cv:
                while not self._closed and not self._pending:
                    self._cv.wait(0.05)
                if self._closed:
                    return
                self._pending = False
            self._run_job()

    def _run_job(self):
        with self._lock:
            if self._busy:
                return
            count = self._shadow.get("ROI_COUNT", 0)
            if count == 0 or count > R.MAX_TARGETS:
                self._fw_decision = R.encode_fw_decision(0, R.REASON_CONFIG, "RECHECK")
                return
            if count > R.POLICY_MAX:
                self._fw_decision = R.encode_fw_decision(0, R.REASON_TARGET_LIMIT, "RECHECK")
                return
            if not self._cfg_valid or not self._model_ok or self._error or self._timeout:
                self._fw_decision = R.encode_fw_decision(0, R.REASON_CONFIG, "RECHECK")
                return
            order = R.unpack_work_order(self._shadow.get("WORK_ORDER", 0))
            min_margin = self._shadow.get("MIN_MARGIN_Q", 0)
            timeout_s = self._shadow.get("TIMEOUT_CYCLES", 0) / R.COP_HZ
            rois = list(self._rois)
            self._generation += 1
            generation = self._generation
            self._busy = True
            self._done = False
            self._result_valid = False
            self._timeout = False
            self._job_started = time.monotonic()
            self._jobs += 1

        started = time.monotonic()
        targets, timed_out = [], False
        for index in range(count):
            if self.faults.delay_s:
                time.sleep(self.faults.delay_s)
            with self._lock:
                if generation != self._generation:
                    return  # ABORT/SOFT_RESET consumed the job
                if self.faults.timeout or time.monotonic() - started > timeout_s:
                    timed_out = True
                    break
            outcome = self.compute(index, rois[index] if index < len(rois) else b"")
            if not isinstance(outcome, dict):
                outcome = {"class_id": 0xFF, "logits": [0, 0, 0], "margin_q": 0,
                           "score_q15": 0, "error": True}
            low_conf = outcome.get("margin_q", 0) < min_margin
            target = {"class_id": int(outcome.get("class_id", 0xFF)),
                      "logits": [int(v) for v in outcome.get("logits", [0, 0, 0])],
                      "margin_q": int(outcome.get("margin_q", 0)),
                      "score_q15": int(outcome.get("score_q15", 0)),
                      "valid": True, "low_conf": bool(low_conf),
                      "error": bool(outcome.get("error", False))}
            if self.faults.target_error == index:
                target["error"] = True
            if self.faults.low_conf == index:
                target["low_conf"] = True
            targets.append(target)

        with self._lock:
            if generation != self._generation:
                return
            self._busy = False
            if timed_out or time.monotonic() - started > timeout_s:
                self._timeout = True
                self._error = True
                self._error_name = "WATCHDOG"
                self._fw_decision = R.encode_fw_decision(0, R.REASON_INVALID, "RECHECK")
                self._perf_cycles = int((time.monotonic() - started) * R.COP_HZ)
                return
            judged = R.firmware_judge(targets, count, order)
            new_seq = self._result_seq if self.faults.stale_result else \
                (self._result_seq + 1) & 0xFFFFFFFF
            self._results = targets
            self._result_seq = new_seq
            self._fw_counts = R.pack_actual(judged["actual"])
            self._fw_decision = R.encode_fw_decision(new_seq, judged["reasons"],
                                                      judged["verdict"])
            self._perf_cycles = int((time.monotonic() - started) * R.COP_HZ)
            self._result_valid = True
            self._done = True

    # ---- test/inspection helpers -----------------------------------------
    def _result_word(self, kind):
        if not self._result_valid or self._result_index >= len(self._results):
            return 0
        target = self._results[self._result_index]
        if kind == "meta":
            return ((self._descriptor_target_id(self._result_index) & 0xFFFF)
                    | ((target["class_id"] & 0xFF) << 16)
                    | (int(target["valid"]) << 24) | (int(target["low_conf"]) << 25)
                    | (int(target["error"]) << 26))
        if kind == "logits":
            logits = [value & 0xFF for value in target["logits"]]
            return logits[0] | (logits[1] << 8) | (logits[2] << 16)
        return (target["score_q15"] & 0xFFFF) | ((target["margin_q"] & 0xFF) << 16)

    def _descriptor_target_id(self, index):
        if 0 <= index < len(self._descriptors):
            return self._descriptors[index].get("target_id", 0)
        return index

    @property
    def error_name(self):
        with self._lock:
            return self._error_name

    @property
    def status(self):
        with self._lock:
            return self._status()

    @property
    def result_seq(self):
        with self._lock:
            return self._result_seq

    @property
    def fw_decision(self):
        with self._lock:
            return self._fw_decision

    @property
    def jobs(self):
        with self._lock:
            return self._jobs

    def wait_idle(self, timeout=5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if not self._busy:
                    return True
            time.sleep(0.002)
        return False

    def trace(self):
        with self._lock:
            return {"status": self._status(), "cfg_seq": self._cfg_seq,
                    "cfg_applied": self._cfg_applied, "result_seq": self._result_seq,
                    "fw_counts": self._fw_counts, "fw_decision": self._fw_decision,
                    "error_name": self._error_name, "jobs": self._jobs,
                    "ops": list(self._ops)}

    def close(self):
        with self._cv:
            self._closed = True
            self._cv.notify_all()
        self._worker.join(timeout=1.0)
