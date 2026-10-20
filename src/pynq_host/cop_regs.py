"""C03 coprocessor register contract constants shared by the PS driver and the sim.

Values frozen by docs/contracts/coprocessor-integration-v0.md §4.  Sim-only
identifiers (descriptor flag bits, error names) are marked as such: C03 does not
freeze their encoding, so the real driver must not depend on them.
"""
import zlib

CLASSES = ("bolt", "nut", "washer")
COP_BASE = 0x8001_0000
IP_ID = 0x434F5030  # ASCII "COP0"
MAX_TARGETS = 16
POLICY_MAX = 10
ROI_BYTES = 4096
RESULT_BYTES = 16
DESCRIPTOR_BYTES = 16
COP_HZ = 100_000_000  # J04 OOC timing target; used only to convert TIMEOUT_CYCLES

OFFSETS = {
    "IP_ID": 0x000, "VERSION": 0x004, "CAPABILITY": 0x008, "CTRL": 0x00C,
    "STATUS": 0x010, "ERROR_CODE": 0x014, "IRQ_ENABLE": 0x018, "CFG_SEQ": 0x01C,
    "CFG_APPLIED": 0x020, "MODEL_ID": 0x024, "WEIGHT_CRC32": 0x028,
    "ROI_COUNT": 0x02C, "TIMEOUT_CYCLES": 0x030, "WORK_ORDER": 0x034,
    "WORK_ORDER_REV": 0x038, "JOB_ID": 0x03C, "CAPTURE_ID": 0x040,
    "SOURCE_CONFIG_ID": 0x044, "WEIGHT_ADDR": 0x048, "WEIGHT_BYTES": 0x04C,
    "TARGET_DESC_ADDR": 0x050, "ROI_ADDR": 0x054, "ROI_STRIDE": 0x058,
    "RESULT_ADDR": 0x05C, "RESULT_STRIDE": 0x060, "MIN_MARGIN_Q": 0x064,
    "CFG_COMMIT": 0x068, "RESULT_INDEX": 0x06C, "RESULT_META": 0x070,
    "RESULT_LOGITS": 0x074, "RESULT_SCORE": 0x078, "RESULT_SEQ": 0x07C,
    "PERF_CYCLES": 0x080, "DMA_BYTES": 0x084, "FW_ACTUAL_COUNTS": 0x088,
    "FW_DECISION": 0x08C,
}
BY_NAME = OFFSETS
BY_OFFSET = {offset: name for name, offset in OFFSETS.items()}
PS_WRITABLE = frozenset((
    "CTRL", "IRQ_ENABLE", "CFG_SEQ", "MODEL_ID", "WEIGHT_CRC32", "ROI_COUNT",
    "TIMEOUT_CYCLES", "WORK_ORDER", "WORK_ORDER_REV", "JOB_ID", "CAPTURE_ID",
    "SOURCE_CONFIG_ID", "WEIGHT_ADDR", "WEIGHT_BYTES", "TARGET_DESC_ADDR",
    "ROI_ADDR", "ROI_STRIDE", "RESULT_ADDR", "RESULT_STRIDE", "MIN_MARGIN_Q",
    "CFG_COMMIT", "RESULT_INDEX",
))
PS_READABLE = frozenset((
    "IP_ID", "VERSION", "CAPABILITY", "STATUS", "ERROR_CODE", "CFG_SEQ",
    "CFG_APPLIED", "MODEL_ID", "WEIGHT_CRC32", "ROI_COUNT", "TIMEOUT_CYCLES",
    "WORK_ORDER", "WORK_ORDER_REV", "JOB_ID", "CAPTURE_ID", "SOURCE_CONFIG_ID",
    "WEIGHT_ADDR", "WEIGHT_BYTES", "TARGET_DESC_ADDR", "ROI_ADDR", "ROI_STRIDE",
    "RESULT_ADDR", "RESULT_STRIDE", "MIN_MARGIN_Q", "RESULT_META", "RESULT_LOGITS",
    "RESULT_SCORE", "RESULT_SEQ", "PERF_CYCLES", "DMA_BYTES", "FW_ACTUAL_COUNTS",
    "FW_DECISION",
))

STATUS_READY = 1 << 0
STATUS_BUSY = 1 << 1
STATUS_DONE = 1 << 2
STATUS_ERROR = 1 << 3
STATUS_TIMEOUT = 1 << 4
STATUS_CFG_VALID = 1 << 5
STATUS_MODEL_VALID = 1 << 6
STATUS_RESULT_VALID = 1 << 7
STATUS_DMA_BUSY = 1 << 8
STATUS_IRQ_PENDING = 1 << 9
STATUS_MBOX_PENDING = 1 << 10

CTRL_START = 1 << 0
CTRL_ABORT = 1 << 1
CTRL_SOFT_RESET = 1 << 2
CTRL_CLEAR_DONE = 1 << 3
CTRL_CLEAR_ERROR = 1 << 4
CTRL_IRQ_ACK = 1 << 5
CTRL_PS_MASK = CTRL_ABORT | CTRL_SOFT_RESET | CTRL_CLEAR_DONE | CTRL_CLEAR_ERROR | CTRL_IRQ_ACK

VERDICT_IDS = {"CHECK_PASS": 1, "CHECK_FAIL": 2, "RECHECK": 3}
VERDICT_NAMES = {value: name for name, value in VERDICT_IDS.items()}
REASON_TARGET_LIMIT = 1
REASON_INVALID = 2
REASON_LOW_CONF = 4
REASON_CLASS = 8
REASON_CONFIG = 16
REASON_NAMES = {
    REASON_TARGET_LIMIT: "target_limit", REASON_INVALID: "invalid",
    REASON_LOW_CONF: "low_conf", REASON_CLASS: "unknown_class",
    REASON_CONFIG: "config",
}
# Python rule reasons that the firmware bitmask cannot distinguish; the driver
# compares verdicts exactly and this mapping only for trace/summary.
FW_TO_PY_REASONS = {
    REASON_TARGET_LIMIT: "target_limit", REASON_INVALID: "low_score",
    REASON_LOW_CONF: "low_score", REASON_CLASS: "unknown_class",
    REASON_CONFIG: "config",
}

# SIM-ONLY: C03 §6.2 requires flags for touch_border/invalid_roi but does not
# freeze their bit positions; J04 firmware does not read descriptors at all.
FLAG_TOUCH_BORDER = 1 << 0
FLAG_INVALID_ROI = 1 << 1

# SIM-ONLY: C03 §9 names error codes but does not freeze encoding (OPEN-9).
SIM_ERROR_CODES = {
    "BAD_STATE": 0xE001, "BAD_ADDR": 0xE002, "BAD_ALIGN": 0xE003,
    "BAD_LENGTH": 0xE004, "BAD_CONFIG": 0xE005, "BAD_MODEL": 0xE006,
    "DMA_READ": 0xE007, "DMA_WRITE": 0xE008, "DMA_SHORT": 0xE009,
    "RESULT_MISMATCH": 0xE00A, "ACC_OVERFLOW_GUARD": 0xE00B,
    "ABORTED": 0xE00C, "WATCHDOG": 0xE00D,
}


class CopBusError(RuntimeError):
    """AXI4-Lite SLVERR / unmapped / permission violation (non-resident)."""


def crc32(payload):
    return zlib.crc32(payload) & 0xFFFFFFFF


def verdict_name(value):
    try:
        return VERDICT_NAMES[int(value)]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"unknown verdict id {value!r}") from error


def pack_work_order(order):
    """dict bolt/nut/washer/policy_max -> 32-bit register value."""
    return (order["bolt"] | (order["nut"] << 8) | (order["washer"] << 16)
            | (order.get("policy_max", POLICY_MAX) << 24))


def unpack_work_order(value):
    return {"bolt": value & 0xFF, "nut": (value >> 8) & 0xFF,
            "washer": (value >> 16) & 0xFF, "policy_max": (value >> 24) & 0xFF}


def firmware_judge(targets, count, order):
    """Mirror src/riscv_fw/cop_work_order.h::cop_judge exactly."""
    actual = [0, 0, 0]
    reasons = 0
    total = order["bolt"] + order["nut"] + order["washer"]
    policy = order.get("policy_max", 0)
    if policy == 0 or policy > POLICY_MAX or total == 0 or total > policy:
        return {"actual": actual, "verdict": "RECHECK", "reasons": REASON_CONFIG}
    if count > POLICY_MAX:
        return {"actual": actual, "verdict": "RECHECK", "reasons": REASON_TARGET_LIMIT}
    for target in targets:
        if not target.get("valid") or target.get("error"):
            reasons |= REASON_INVALID
        if target.get("low_conf"):
            reasons |= REASON_LOW_CONF
        class_id = target.get("class_id", 0xFF)
        if class_id > 2:
            reasons |= REASON_CLASS
        else:
            actual[class_id] += 1
    verdict = ("RECHECK" if reasons else
               "CHECK_PASS" if actual == [order["bolt"], order["nut"], order["washer"]]
               else "CHECK_FAIL")
    return {"actual": actual, "verdict": verdict, "reasons": reasons}


def decode_fw_decision(value):
    """OPEN-6 layout (provisional): [31:16] result_seq, [15:8] reasons, [7:0] verdict."""
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("invalid FW_DECISION")
    return {"result_seq": value >> 16, "reasons": (value >> 8) & 0xFF,
            "verdict_id": value & 0xFF, "verdict": verdict_name(value & 0xFF)}


def encode_fw_decision(result_seq, reasons, verdict):
    return ((result_seq & 0xFFFF) << 16) | ((reasons & 0xFF) << 8) | VERDICT_IDS[verdict]


def pack_actual(actual):
    return actual[0] | (actual[1] << 8) | (actual[2] << 16)


def unpack_actual(value):
    return [value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF]
