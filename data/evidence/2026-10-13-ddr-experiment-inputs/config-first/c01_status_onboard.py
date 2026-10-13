"""C01 display/status diagnostic only; never starts capture DMA. Restore vision."""
import hashlib
import os
import signal
import sys
import time
from pathlib import Path


def verify(path, expected):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
        raise ValueError("artifact SHA256 mismatch: " + str(path))


def load_candidate(bit, overlay_type):
    print("STAGE: HWH metadata parse before programming", flush=True)
    overlay = overlay_type(str(bit), download=False, gen_cache=False)
    for base in (0x40000000, 0x42000000, 0x43000000):
        segments = [entry for entry in overlay.ip_dict.values()
                    if entry.get("phys_addr") == base and entry.get("addr_range") == 65536]
        if len(segments) != 1:
            raise RuntimeError("pre-download address mismatch: " + hex(base))
    print("STAGE: HWH layout accepted; candidate download begins", flush=True)
    overlay.download()
    print("STAGE: candidate download returned", flush=True)
    return overlay

def restore_original(load, smoke, sleep=time.sleep):
    """Bounded restoration: reload original vision, settle, smoke; one NOVIDEO retry."""
    load()
    print("STAGE: original vision loaded; bounded settle before smoke", flush=True)
    for attempt in (1, 2):
        sleep(5)
        try:
            smoke()
            return
        except SystemExit as exc:
            if exc.code != 3 or attempt == 2:
                raise
            print("RECOVERY-RETRY: restore smoke attempt %d NOVIDEO; settle 5 more seconds" % attempt, flush=True)

def probe(bit, bit_sha, hwh_sha, load, mmio, smoke, restore, pause=time.sleep):
    verify(bit, bit_sha)
    verify(Path(bit).with_suffix(".hwh"), hwh_sha)
    attempted = False
    main_error = None
    try:
        attempted = True
        print("STAGE: artifact pair verified; overlay load begins", flush=True)
        overlay = load(str(bit))
        print("STAGE: overlay load returned; address validation begins", flush=True)
        for base in (0x40000000, 0x42000000, 0x43000000):
            segments = [entry for entry in overlay.ip_dict.values()
                        if entry.get("phys_addr") == base and entry.get("addr_range") == 65536]
            if len(segments) != 1:
                raise RuntimeError("unexpected overlay address map: " + hex(base))
        status = mmio(0x42000000, 65536)
        dma = mmio(0x43000000, 65536)
        print("STAGE: VDMA halted-state MMIO reads begin", flush=True)
        cr_start, sr_start = dma.read(0x30), dma.read(0x34)
        print("VDMA-START: CR=0x%08X SR=0x%08X" % (cr_start, sr_start), flush=True)
        if cr_start & 1 or not sr_start & 1:
            # Unexpected external DMA activity must not be reprogrammed underneath it.
            attempted = False
            raise RuntimeError("DMA unexpectedly running; restoration withheld until halted")
        print("STAGE: capture identity/geometry MMIO reads begin", flush=True)
        if (status.read(0), status.read(0x14), status.read(0x18)) != (0x43415031, 1280, 720):
            raise RuntimeError("capture identity/geometry mismatch")
        for _ in range(100):
            if status.read(4) & 1:
                break
            pause(0.05)
        else:
            raise TimeoutError("video lock did not assert")
        print("STAGE: capture lock accepted; allow 5 seconds for HDMI reacquisition", flush=True)
        pause(5)
        print("STAGE: HDMI settling finished; pipe smoke begins", flush=True)
        smoke()
        print("PASS: C01 addresses, identity, geometry, idle DMA and existing vision smoke", flush=True)
        seq_start = status.read(8)
        print("SEQ-START: stream_seq=%d" % seq_start, flush=True)
        print("WINDOW: C01 HDMI direct display active for 20 seconds", flush=True)
        pause(20)
        cr_end, sr_end = dma.read(0x30), dma.read(0x34)
        print("VDMA-END: CR=0x%08X SR=0x%08X" % (cr_end, sr_end), flush=True)
        print("STATUS:", {hex(offset): status.read(offset) for offset in range(0, 0x24, 4)}, flush=True)
        seq_end = status.read(8)
        print("SEQ-END: stream_seq=%d delta=%d" % (seq_end, seq_end - seq_start), flush=True)
        if cr_end & 1 or not sr_end & 1:
            raise RuntimeError("VDMA S2MM left halted state during window: CR=0x%08X SR=0x%08X" % (cr_end, sr_end))
        flags = status.read(4)
        if not flags & 1:
            raise RuntimeError("video lock dropped during window: CSR 0x4=0x%X" % flags)
        if flags & 0xC or status.read(0x10) != 0:
            raise RuntimeError("capture fault or error event during window: CSR 0x4=0x%X error_epoch=%d"
                               % (flags, status.read(0x10)))
        print("PASS: C01 display/status diagnostic; stream_seq delta = halt-state accept-and-discard"
              " handshakes, not DDR writes", flush=True)
    except BaseException as exc:
        main_error = exc
        print("MAIN-FAIL: %r" % (exc,), flush=True)
        raise
    finally:
        if attempted:
            try:
                print("STAGE: original vision restoration begins", flush=True)
                restore()
                print("CLEANUP: original vision load and smoke completed", flush=True)
            except BaseException as recovery_error:
                print("RECOVERY-FAIL: %r" % (recovery_error,), flush=True)
                if main_error is None:
                    raise
                print("MAIN-FAIL-WAS: %r" % (main_error,), flush=True)


def main():
    print("STAGE: board diagnostic entered", flush=True)
    from pynq import MMIO, Overlay
    import faulthandler
    # Single hang breadcrumb past worst normal runtime (~57s incl. one restore retry);
    # cancelled on normal completion so routine 20s sleeps never print Timeout stacks.
    faulthandler.dump_traceback_later(60)
    sys.path.insert(0, "/home/xilinx/vision_m2")
    import m2_onboard
    old = Path("/home/xilinx/vision_m2/vision.bit")
    verify(old, "4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5")
    verify(old.with_suffix(".hwh"), "c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5")
    def restore():
        restore_original(m2_onboard.cmd_load, m2_onboard.cmd_smoke, time.sleep)
    def timeout(signum, frame):
        raise TimeoutError("C01 diagnostic timeout")
    signal.signal(signal.SIGTERM, timeout)
    probe(Path(os.environ["C01_BIT"]), os.environ["C01_BIT_SHA"], os.environ["C01_HWH_SHA"],
          lambda path: load_candidate(path, Overlay), MMIO, m2_onboard.cmd_smoke, restore)
    faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
