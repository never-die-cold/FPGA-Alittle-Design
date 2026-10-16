"""C01 capture-stage direct diagnostic on the already-loaded candidate overlay.

NOT formal N03: starts from the late-smoke state (candidate loaded, video at
60 fps, pipe config applied, DMA halted with idle sticky SR=0x14811) instead of
re-downloading, and skips the entry smoke stage. It runs ONLY the frozen
SingleFrameCapture bytes -- source check, soft reset, geometry-then-sticky-clear
(the ordering fix never board-tested), RUN with frame-count auto-stop, joint
confirm, invalidate, independent copy, PNG round-trip -- then restores the
original vision overlay. An unconfirmed stop quarantines buffers and keeps the
process alive exactly like the frozen entry.
"""
import fcntl
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

TRIAL = Path('/home/xilinx/vision_m2/c01-ff610bdae8ef46ce9304e531ebaf9627')
SITE = '/home/xilinx/vision_m2'
DRIVER_SHA = '1f11aefdc11805387b0c345583828fd733e5e38b0b0e043b0510808f648e8430'
BIT_SHA = '86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f'


def main():
    from pynq import MMIO, PL, allocate
    import cv2
    sys.path.insert(0, SITE)
    import m2_onboard
    sys.path.insert(0, str(TRIAL))
    from c01_capture import SingleFrameCapture, QUARANTINE
    from c01_status_onboard import restore_original
    if hashlib.sha256((TRIAL / 'c01_capture.py').read_bytes()).hexdigest() != DRIVER_SHA:
        raise RuntimeError('trial driver is not the frozen N03 bytes')
    if not PL.bitfile_name or 'capture' not in PL.bitfile_name:
        raise RuntimeError('candidate overlay is not loaded: %r' % PL.bitfile_name)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    def identity():
        return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                PL.bitfile_name, str(PL.timestamp))
    status, dma = MMIO(0x42000000, 65536), MMIO(0x43000000, 65536)
    def snapshot():
        return {'cap': {hex(o): int(status.read(o)) for o in range(0, 0x24, 4)},
                'cr': int(dma.read(0x30)), 'sr': int(dma.read(0x34))}
    tick_a = status.read(8)
    time.sleep(1.0)
    tick_b = status.read(8)
    if tick_b <= tick_a:
        raise RuntimeError('frame counter not ticking; video absent: %d->%d' % (tick_a, tick_b))
    print('PRECHECK: video flowing, +%d frames/1.0 s; state=%s' % (tick_b - tick_a, json.dumps(snapshot())), flush=True)
    result = {'boot_before': boot, 'driver_sha256': DRIVER_SHA, 'bit_sha256': BIT_SHA,
              'kind': 'C01_CAPTURE_STAGE_DIRECT_DIAGNOSTIC_NOT_FORMAL_N03',
              'video_framerate_delta': tick_b - tick_a, 'state_before': snapshot()}
    owner, primary, attempted = None, None, False
    try:
        attempted = True
        owner = SingleFrameCapture(dma, status, allocate, identity)
        frame = owner.capture()
        result['capture'] = owner.evidence
        result['shape'], result['strides'] = list(frame.shape), list(frame.strides)
        result['pixel_sha256'] = hashlib.sha256(frame.tobytes()).hexdigest()
        result['channel_mean_bgr'] = frame.mean(axis=(0, 1)).tolist()
        result['pixel_min'], result['pixel_max'] = int(frame.min()), int(frame.max())
        png = TRIAL / 'stage-direct.png'
        if not cv2.imwrite(str(png), frame):
            raise RuntimeError('PNG write failed')
        decoded = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if decoded is None or not np.array_equal(decoded, frame):
            raise RuntimeError('PNG round-trip mismatch')
        result['png_sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
        result['state_after'] = snapshot()
        result['ok'] = True
        print('PASS: capture stage complete; independent frame verified', flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
        if owner is not None:
            result['capture'] = owner.evidence
        result['state_after'] = snapshot()
        print('MAIN-FAIL:', repr(exc), flush=True)
    finally:
        if QUARANTINE or (owner is not None and owner.may_write):
            result['unsafe_stop'] = True
            print('UNSAFE-STOP: buffers held; process stays alive; physical board reset required', flush=True)
            # Never exit and run native-buffer finalizers while DMA stop is unknown.
            while True:
                time.sleep(1)
        if attempted:
            try:
                restore_original(m2_onboard.cmd_load, m2_onboard.cmd_smoke)
                result['restored'] = True
            except BaseException as exc:
                result['restore_error'] = repr(exc)
                if primary is None:
                    primary = exc
        result['boot_after'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        print('RESULT:', json.dumps(result), flush=True)
    if primary is not None:
        raise primary
    if result['boot_after'] != boot:
        raise RuntimeError('board rebooted during diagnostic')
    print('PASS: original vision restored; diagnostic complete', flush=True)


if __name__ == '__main__':
    main()
