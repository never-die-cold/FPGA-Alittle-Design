"""PS-side driver for the C03 A1/A2 MMIO coprocessor.

Transport-agnostic: the driver only needs ``read32/write32`` and a DMA plane.
``SimDmaPlane`` + ``CopSim`` exercise the whole flow off-board; ``PynqMmio`` is
the intended one-line swap for real hardware, but no board path is claimed here.

A1/A2 invariants (C03 §14, K1):
- READY is advisory (!BUSY); config receipt is CFG_APPLIED only.
- ACCEPTED is the sticky START receipt; PS has NO_ACK and HW_TIMEOUT software
  watchdogs independent of READY and of the hardware timeout.
- Terminals are mutually exclusive; only one PS CONSUME clears
  DONE/ERROR/TIMEOUT/RESULT_VALID/ACCEPTED/ERROR_CODE.  RESULT_SEQ persists.
- A valid result is read and validated, then persisted by the caller, then
  consumed.  The driver never consumes a DONE result by itself.
- RESULT_SEQ must advance and stay unchanged across the indexed result reads.
- FW_DECISION must describe the same RESULT_SEQ and match the firmware rules.
- The PS decision may be stricter than the firmware's, never more permissive
  (touch-border is a PS-side gate until JL adds it to cop_judge).
"""
import hashlib
import math
import time

import cop_regs as R
from inspection_rules import effective_policy, judge

MODEL_ID_DEFAULT = 0x434F5044  # "COPD"; sim placeholder, not a formal manifest ID
DEFAULT_ADDRESSES = {"weight": 0x0100_0000, "descriptor": 0x0110_0000,
                     "roi": 0x0120_0000, "result": 0x0130_0000}
VERDICT_RANK = {"CHECK_PASS": 0, "CHECK_FAIL": 1, "RECHECK": 2}


class CopError(RuntimeError):
    """Base class for driver-visible failures (service maps them to 503)."""


class CopConfigError(CopError):
    pass


class CopJobError(CopError):
    def __init__(self, message, status=None, error_name=None, result_seq=None,
                 error_code=None):
        self.status = status
        self.error_name = error_name
        self.result_seq = result_seq
        self.error_code = error_code
        detail = message
        if status is not None:
            detail += f" (status=0x{status:08x}"
            detail += f", error_code={error_code}" if error_code is not None else ""
            detail += f", sim_error={error_name}" if error_name else ""
            detail += ")"
        super().__init__(detail)


class CopTimeoutError(CopJobError):
    pass


class CopNoAck(CopJobError):
    """ACCEPTED never arrived before the PS software watchdog expired."""


class CopHardwareTimeout(CopJobError):
    """ACCEPTED arrived but no terminal arrived before the PS software watchdog."""


class CopStaleResult(CopError):
    """UNCONSUMED terminal from a previous round; consume/persist it first."""

    def __init__(self, message, status=None, result_seq=None, error_code=None):
        self.status = status
        self.result_seq = result_seq
        self.error_code = error_code
        super().__init__(message)


class CopProtocolError(CopError):
    """Hardware/result/decision did not satisfy the contract; never mask as PASS."""


class SimDmaPlane:
    def __init__(self, sim):
        self.sim = sim

    def load_model(self, addr, payload):
        return self.sim.load_weights(addr, payload)

    def load_rois(self, addr, rois, stride):
        return self.sim.load_rois(addr, rois, stride)

    def load_descriptors(self, addr, descriptors):
        return self.sim.load_descriptors(addr, descriptors)


class PynqMmio:
    """Adapter for pynq.lib.MemoryMappedIO-like objects; not exercised here.

    The PS AXI base is assigned by Vivado Address Editor; it is NOT the
    core-side local window ``0x8001_0000``.  Requiring it explicitly prevents
    a sim/mock address from silently becoming the board address.
    """

    def __init__(self, mmio, base):
        if type(base) is not int or base < 0:
            raise ValueError("PS AXI base address is required (Address Editor)")
        self.mmio = mmio
        self.base = base

    def read32(self, offset):
        return int(self.mmio.read(self.base + offset))

    def write32(self, offset, value):
        self.mmio.write(self.base + offset, int(value))


class PynqDmaPlane:
    """J08 data-plane seam.  Physical bank/DataMover wiring is OPEN-1/OPEN-2."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "DataMover/AXI DMA plane is not implemented; use SimDmaPlane until J08 "
            "provides the physical bank and result DMA (OPEN-1/OPEN-2)")

    def load_model(self, addr, payload):
        raise NotImplementedError("J08 data plane")

    def load_rois(self, addr, rois, stride):
        raise NotImplementedError("J08 data plane")

    def load_descriptors(self, addr, descriptors):
        raise NotImplementedError("J08 data plane")


class CopDriver:
    def __init__(self, transport, dma, order, min_score, max_targets=16,
                 policy_max=None, model_payload=b"COP-SIM-PLACEHOLDER-MODEL",
                 model_id=MODEL_ID_DEFAULT, addresses=None, job_timeout_s=5.0,
                 accept_timeout_s=1.0, config_timeout_s=2.0, poll_s=0.002):
        judge([], order, min_score, max_targets, policy_max)  # freeze/validate inputs
        if not isinstance(model_payload, (bytes, bytearray)) or not model_payload:
            raise ValueError("model payload must be non-empty bytes")
        if type(model_id) is not int or not 0 < model_id <= 0xFFFFFFFF:
            raise ValueError("model_id must be a non-zero uint32")
        self.transport = transport
        self.dma = dma
        self.order = dict(order)
        self.min_score = float(min_score)
        self.max_targets = max_targets
        self.policy_max = effective_policy(max_targets, policy_max)
        self.model_payload = bytes(model_payload)
        self.model_id = model_id
        self.model_crc = R.crc32(self.model_payload)
        self.addresses = dict(DEFAULT_ADDRESSES)
        if addresses:
            self.addresses.update(addresses)
        # ceil keeps the integer low-conf boundary consistent with judge(score < min_score):
        # margin >= ceil(min_score*254) => score_q15/32767 >= min_score.
        self.min_margin_q = max(0, min(254, math.ceil(self.min_score * 254)))
        self.job_timeout_s = job_timeout_s
        self.accept_timeout_s = accept_timeout_s
        self.config_timeout_s = config_timeout_s
        self.poll_s = poll_s
        self.cfg_seq = 0
        self.last_result_seq = None
        self._model_loaded = None
        self._cache = None
        self.last_terminal = None
        self.events = []

    # ---- register helpers ------------------------------------------------
    def read(self, name):
        return self.transport.read32(R.OFFSETS[name])

    def write(self, name, value):
        self.transport.write32(R.OFFSETS[name], value)

    def status(self):
        return self.read("STATUS")

    def _sim_error(self):
        return getattr(self.transport, "error_name", None)

    def _poll(self, predicate, timeout, what):
        deadline = time.monotonic() + timeout
        polls = 0
        while True:
            value = predicate()
            polls += 1
            if value:
                return value, polls
            if time.monotonic() > deadline:
                raise CopProtocolError(f"timed out waiting for {what}")
            time.sleep(self.poll_s)

    # ---- A1/A2 terminal handling -----------------------------------------
    @staticmethod
    def _terminal(status):
        return status & (R.STATUS_DONE | R.STATUS_ERROR | R.STATUS_TIMEOUT)

    def consume(self, result=None):
        """PS-only CONSUME: clear a persisted/known terminal atomically.

        Must be called only after the caller has read and persisted the result
        (or after capturing an error terminal).  RESULT_SEQ is preserved.
        """
        status = self.status()
        if not status & R.STATUS_UNCONSUMED:
            raise CopProtocolError("CONSUME without a terminal")
        if status & R.STATUS_BUSY:
            raise CopProtocolError("CONSUME while BUSY")
        seq = self.read("RESULT_SEQ")
        if result is not None and result.get("result_seq") != seq:
            raise CopProtocolError(
                f"CONSUME seq {seq} does not match result {result.get('result_seq')}")
        try:
            self.write("CTRL", R.CTRL_CONSUME)
        except R.CopBusError as error:
            raise CopProtocolError(f"CONSUME rejected: {error}") from error
        after = self.status()
        if after & (R.STATUS_UNCONSUMED | R.STATUS_ACCEPTED | R.STATUS_RESULT_VALID):
            raise CopProtocolError(f"CONSUME did not clear terminal: 0x{after:08x}")
        if self.read("ERROR_CODE") != 0:
            raise CopProtocolError("CONSUME did not clear ERROR_CODE")
        if self.read("RESULT_SEQ") != seq:
            raise CopProtocolError("CONSUME changed RESULT_SEQ")
        self.last_result_seq = seq
        self.events.append({"kind": "consume", "result_seq": seq,
                            "status_before": status, "status_after": after})
        return after

    def terminal_snapshot(self, reason="terminal"):
        status = self.status()
        return {"reason": reason, "status": status,
                "result_seq": self.read("RESULT_SEQ"),
                "error_code": self.read("ERROR_CODE"),
                "fw_decision": self.read("FW_DECISION")}

    def consume_current(self, reason="recover"):
        """Capture the current terminal metadata, then CONSUME it.

        The caller must persist the returned snapshot before treating the
        evidence as archived; this helper is for error/stale recovery, not for
        a valid DONE result (use ``consume(result)`` after persistence).
        """
        status = self.status()
        if status & R.STATUS_BUSY:
            self.write("CTRL", R.CTRL_ABORT)
            self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                       "BUSY to clear before CONSUME")
            status = self.status()
        if not status & R.STATUS_UNCONSUMED:
            return None
        snapshot = self.terminal_snapshot(reason)
        self.last_terminal = snapshot
        self.consume(None)
        return snapshot

    def recover(self):
        """Consume a leftover terminal (recovery/startup); no normal-path use."""
        return self.consume_current("recover")

    def ensure_ready(self):
        """Reach BUSY=0 && UNCONSUMED=0 before submitting a new job."""
        status = self.status()
        if status & R.STATUS_BUSY:
            self.write("CTRL", R.CTRL_ABORT)
            self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                       "BUSY to clear before submit")
            status = self.status()
        if status & R.STATUS_ACCEPTED and not self._terminal(status):
            # Abandoned ACCEPTED without a terminal: force ERROR, then consume.
            self.write("CTRL", R.CTRL_ABORT)
            self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                       "BUSY to clear after stale ACCEPTED")
            status = self.status()
            if status & R.STATUS_UNCONSUMED:
                self.consume_current("stale_accepted")
            status = self.status()
        if status & R.STATUS_UNCONSUMED:
            raise CopStaleResult(
                "UNCONSUMED terminal before submit; persist/consume it first",
                status=status, result_seq=self.read("RESULT_SEQ"),
                error_code=self.read("ERROR_CODE"))
        if status & (R.STATUS_ACCEPTED | R.STATUS_RESULT_VALID):
            raise CopProtocolError(f"pre-submit state not clean: 0x{status:08x}")
        return status

    def abort(self):
        self.write("CTRL", R.CTRL_ABORT)
        self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                   "BUSY to clear after ABORT")
        self.events.append({"kind": "abort"})

    def soft_reset(self):
        self.write("CTRL", R.CTRL_SOFT_RESET)
        self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                   "BUSY to clear after SOFT_RESET")
        self.events.append({"kind": "soft_reset"})

    # ---- submission ------------------------------------------------------
    def _validate_job(self, job):
        targets = job.get("targets")
        if not isinstance(targets, list) or not 1 <= len(targets) <= self.policy_max:
            raise CopConfigError("target count must be 1..policy_max")
        ids = set()
        for index, target in enumerate(targets):
            if not isinstance(target, dict):
                raise ValueError("target must be a dict")
            identity = target.get("target_id")
            if type(identity) is not int or not 0 <= identity <= 0xFFFF or identity in ids:
                raise ValueError("target_id must be unique uint16")
            ids.add(identity)
            roi = target.get("roi")
            if not isinstance(roi, (bytes, bytearray)) or len(roi) != R.ROI_BYTES:
                raise ValueError("each target needs a 4096-byte INT8 ROI")
            if target.get("roi_index", index) != index:
                raise ValueError("roi_index must follow descriptor order")
            flags = target.get("flags", 0)
            if type(flags) is not int or flags & ~3:
                raise ValueError("descriptor flags are sim-only bits 0..1")
        for name in ("job_id", "work_order_rev", "capture_id", "source_config_id"):
            value = job.get(name)
            if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
                raise ValueError(f"{name} must be uint32")

    def _fingerprint(self, job):
        digest = hashlib.sha256()
        for target in job["targets"]:
            digest.update(int(target["target_id"]).to_bytes(2, "little"))
            digest.update(int(target.get("flags", 0)).to_bytes(1, "little"))
            digest.update(bytes(target["roi"]))
        return digest.hexdigest()

    def _configure(self, job, count):
        addresses = self.addresses
        targets = job["targets"]
        self.write("MODEL_ID", self.model_id)
        self.write("WEIGHT_CRC32", self.model_crc)
        self.write("ROI_COUNT", count)
        self.write("TIMEOUT_CYCLES", job.get("timeout_cycles", R.COP_HZ))
        self.write("WORK_ORDER", R.pack_work_order({**self.order, "policy_max": self.policy_max}))
        self.write("WORK_ORDER_REV", job["work_order_rev"])
        self.write("JOB_ID", job["job_id"])
        self.write("CAPTURE_ID", job["capture_id"])
        self.write("SOURCE_CONFIG_ID", job["source_config_id"])
        self.write("WEIGHT_ADDR", addresses["weight"])
        self.write("WEIGHT_BYTES", len(self.model_payload))
        self.write("TARGET_DESC_ADDR", addresses["descriptor"])
        self.write("ROI_ADDR", addresses["roi"])
        self.write("ROI_STRIDE", R.ROI_BYTES)
        self.write("RESULT_ADDR", addresses["result"])
        self.write("RESULT_STRIDE", R.RESULT_BYTES)
        self.write("MIN_MARGIN_Q", self.min_margin_q)
        signature = (self.model_id, self.model_crc, addresses["weight"],
                     len(self.model_payload))
        if self._model_loaded != signature:
            info = self.dma.load_model(addresses["weight"], self.model_payload)
            self._model_loaded = signature
            self.events.append({"kind": "model_load", "crc32": self.model_crc,
                                "bytes": len(self.model_payload),
                                "sim_reported": info})
        self.dma.load_rois(addresses["roi"], [bytes(t["roi"]) for t in targets],
                           R.ROI_BYTES)
        self.dma.load_descriptors(addresses["descriptor"], [
            {"target_id": t["target_id"], "flags": t.get("flags", 0),
             "roi_index": index, "reserved": 0}
            for index, t in enumerate(targets)])
        self.cfg_seq = (self.cfg_seq + 1) & 0xFFFFFFFF
        if self.cfg_seq == 0:
            self.cfg_seq = 1
        self.write("CFG_SEQ", self.cfg_seq)
        try:
            self.write("CFG_COMMIT", 1)
        except R.CopBusError as error:
            raise CopConfigError(f"CFG_COMMIT rejected: {error}") from error

        def applied_or_failed():
            if self.read("CFG_APPLIED") == self.cfg_seq:
                return True
            return bool(self.status() & (R.STATUS_ERROR | R.STATUS_TIMEOUT))
        try:
            self._poll(applied_or_failed, self.config_timeout_s, "CFG_APPLIED")
        except CopProtocolError:
            pass
        if self.read("CFG_APPLIED") != self.cfg_seq:
            status = self.status()
            error_code = self.read("ERROR_CODE")
            error_name = self._sim_error()
            if status & R.STATUS_UNCONSUMED:
                self.consume_current("config_error")
            self._model_loaded = None
            raise CopConfigError(
                f"configuration not applied (status=0x{status:08x}, "
                f"error_code={error_code}, sim_error={error_name})")
        return self.cfg_seq

    def _ps_targets(self, hardware, descriptors):
        targets = []
        for item, descriptor in zip(hardware, descriptors):
            class_id = item["class_id"]
            class_name = R.CLASSES[class_id] if class_id <= 2 else None
            score = item["score_q15"] / 32767.0 if class_name is not None else 0.0
            if not item["valid"] or item["error"]:
                score = 0.0  # keep the class for count parity with cop_judge
            targets.append({"class": class_name, "score": score,
                            "touches_border": bool(descriptor.get("flags", 0) & R.FLAG_TOUCH_BORDER)})
        return targets

    def _check_safety(self, fw, ps, ps_targets):
        expected = dict(zip(R.CLASSES, fw["actual"]))
        if ps["actual"] != expected:
            raise CopProtocolError(f"count mismatch PS={ps['actual']} FW={expected}")
        if VERDICT_RANK[ps["verdict"]] < VERDICT_RANK[fw["verdict"]]:
            raise CopProtocolError(f"PS decision more permissive: PS={ps['verdict']} "
                                   f"FW={fw['verdict']}")
        fw_reasons = {R.FW_TO_PY_REASONS[bit] for bit in R.REASON_NAMES
                      if fw["reasons"] & bit}
        ps_reasons = set(ps["reasons"])
        extra = ps_reasons - fw_reasons - {"touches_border"}
        missing = fw_reasons - ps_reasons - {"config"}
        if extra or missing:
            raise CopProtocolError(f"reason mismatch PS={sorted(ps_reasons)} "
                                   f"FW={sorted(fw_reasons)}")
        return fw_reasons

    def _raise_terminal(self, status):
        """Read ERROR_CODE, consume the terminal, then raise the hardware error."""
        error_code = self.read("ERROR_CODE")
        error_name = self._sim_error() or R.ERROR_CODE_NAMES.get(error_code)
        snapshot = self.consume_current("terminal")
        self._model_loaded = None  # a task/model error gets a clean reload on retry
        error_type = CopTimeoutError if status & R.STATUS_TIMEOUT else CopJobError
        raise error_type("coprocessor terminal without a valid result",
                         status=status, error_name=error_name,
                         result_seq=(snapshot or {}).get("result_seq"),
                         error_code=error_code)

    def run(self, job):
        self._validate_job(job)
        count = len(job["targets"])
        key = (job["job_id"], job["work_order_rev"])
        fingerprint = self._fingerprint(job)
        if self._cache is not None and self._cache["key"] == key:
            if self._cache["fingerprint"] != fingerprint:
                raise CopProtocolError("same JOB_ID/WORK_ORDER_REV with different targets")
            return {**self._cache["result"], "duplicate": True}

        self.ensure_ready()
        cfg_seq = self._configure(job, count)
        started = time.monotonic()
        polls = 0

        # A2: independent NO_ACK watchdog for the sticky START receipt.
        deadline = started + self.accept_timeout_s
        status = self.status()
        while not status & R.STATUS_ACCEPTED:
            polls += 1
            if status & (R.STATUS_ERROR | R.STATUS_TIMEOUT):
                self._raise_terminal(status)
            if time.monotonic() > deadline:
                self.write("CTRL", R.CTRL_ABORT)
                self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                           "BUSY to clear after NO_ACK")
                status = self.status()
                snapshot = (self.consume_current("no_ack")
                            if status & R.STATUS_UNCONSUMED else None)
                raise CopNoAck("ACCEPTED not observed within PS software watchdog",
                               status=status, error_name="NO_ACK",
                               result_seq=(snapshot or {}).get("result_seq"),
                               error_code=(snapshot or {}).get("error_code"))
            time.sleep(self.poll_s)
            status = self.status()

        # A2: second independent watchdog; do not rely on hardware TIMEOUT.
        deadline = time.monotonic() + self.job_timeout_s
        while not self._terminal(status):
            polls += 1
            if time.monotonic() > deadline:
                self.write("CTRL", R.CTRL_ABORT)
                self._poll(lambda: not (self.status() & R.STATUS_BUSY), 1.0,
                           "BUSY to clear after HW_TIMEOUT")
                status = self.status()
                snapshot = (self.consume_current("hw_timeout")
                            if status & R.STATUS_UNCONSUMED else None)
                raise CopHardwareTimeout(
                    "terminal not observed within PS software watchdog",
                    status=status, error_name="HW_TIMEOUT",
                    result_seq=(snapshot or {}).get("result_seq"),
                    error_code=(snapshot or {}).get("error_code"))
            time.sleep(self.poll_s)
            status = self.status()

        if status & (R.STATUS_ERROR | R.STATUS_TIMEOUT):
            self._raise_terminal(status)
        if not status & R.STATUS_DONE:
            raise CopProtocolError(f"unexpected terminal status 0x{status:08x}")
        if not status & R.STATUS_RESULT_VALID:
            raise CopProtocolError("DONE without RESULT_VALID")
        seq_before = self.read("RESULT_SEQ")
        expected = 1 if self.last_result_seq is None else \
            ((self.last_result_seq + 1) & 0xFFFFFFFF)
        if seq_before != expected:
            raise CopProtocolError(
                f"unexpected RESULT_SEQ {seq_before}; expected {expected} "
                f"(last consumed {self.last_result_seq})")
        hardware = []
        for index, descriptor in enumerate(job["targets"]):
            self.write("RESULT_INDEX", index)
            meta = self.read("RESULT_META")
            if (meta & 0xFFFF) != descriptor["target_id"]:
                raise CopProtocolError(f"result target_id mismatch at {index}")
            hardware.append({
                "class_id": (meta >> 16) & 0xFF, "valid": (meta >> 24) & 1,
                "low_conf": (meta >> 25) & 1, "error": (meta >> 26) & 1,
                "logits": [self.read("RESULT_LOGITS") >> (8 * i) & 0xFF for i in range(3)],
                "score_q15": self.read("RESULT_SCORE") & 0xFFFF,
                "margin_q": (self.read("RESULT_SCORE") >> 16) & 0xFF})
        seq_after = self.read("RESULT_SEQ")
        status_after = self.status()
        if seq_before != seq_after or not status_after & R.STATUS_RESULT_VALID \
                or status_after & (R.STATUS_ERROR | R.STATUS_TIMEOUT | R.STATUS_BUSY):
            raise CopProtocolError("result window changed or invalidated during read")

        fw_counts = R.unpack_actual(self.read("FW_ACTUAL_COUNTS"))
        fw_decision = R.decode_fw_decision(self.read("FW_DECISION"))
        if fw_decision["result_seq"] != seq_before:
            raise CopProtocolError("FW_DECISION result_seq does not match RESULT_SEQ")
        fw_rules = R.firmware_judge(
            [{"class_id": item["class_id"], "valid": item["valid"],
              "low_conf": item["low_conf"], "error": item["error"]} for item in hardware],
            count, {**self.order, "policy_max": self.policy_max})
        if (fw_rules["verdict"] != fw_decision["verdict"]
                or fw_rules["reasons"] != fw_decision["reasons"]
                or fw_rules["actual"] != fw_counts):
            raise CopProtocolError("FW_DECISION does not match firmware rules")

        ps_targets = self._ps_targets(hardware, job["targets"])
        ps_decision = judge(ps_targets, self.order, self.min_score,
                            self.max_targets, self.policy_max)
        fw_reasons = self._check_safety({**fw_rules, "reasons": fw_decision["reasons"]},
                                        ps_decision, ps_targets)
        elapsed_ms = (time.monotonic() - started) * 1000
        trace = {
            "backend": "COP_SIM" if hasattr(self.transport, "trace") else "MMIO",
            "cfg_seq": cfg_seq, "result_seq": seq_before, "expected_seq": expected,
            "accepted": True, "unconsumed": True, "error_code": 0,
            "work_order_rev": job["work_order_rev"], "job_id": job["job_id"],
            "capture_id": job["capture_id"], "source_config_id": job["source_config_id"],
            "status": status_after, "polls": polls, "elapsed_ms": round(elapsed_ms, 3),
            "fw": {**fw_decision, "actual": fw_counts,
                   "reasons_names": sorted(fw_reasons)},
            "ps_decision": ps_decision,
            "targets": hardware,
            "perf_cycles": self.read("PERF_CYCLES"),
            "dma_bytes": self.read("DMA_BYTES"),
            "events": list(self.events),
        }
        result = {"targets": [{"target_id": descriptor["target_id"],
                               "class": ps["class"], "score": ps["score"],
                               "touches_border": ps["touches_border"],
                               "valid": item["valid"], "low_conf": item["low_conf"],
                               "error": item["error"], "logits": item["logits"],
                               "margin_q": item["margin_q"], "score_q15": item["score_q15"]}
                              for descriptor, item, ps in zip(job["targets"], hardware, ps_targets)],
                  "decision": ps_decision, "trace": trace,
                  "result_seq": seq_before, "cfg_seq": cfg_seq}
        self.events = []
        self._cache = {"key": key, "fingerprint": fingerprint, "result": result}
        return result
