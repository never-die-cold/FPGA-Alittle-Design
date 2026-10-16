"""Park candidate first board run: warmup clear + slot-0 protected copy.

NOT formal N03. Mirrors the frozen entry's safety semantics (flock, hash
checks, video-tick precheck instead of the smoke settle race, UNSAFE-STOP
keep-alive, bounded busy-aware restore) but drives the reviewed park driver
bytes directly on the already-trialled overlay path. Publishes nothing beyond
the local PNG artifact class the frozen entry itself uses.
"""
import fcntl
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

SITE = '/home/xilinx/vision_m2'
TRIAL = Path(SITE) / 'c01-8b702ebb0b284fa3a408491e13e644e3'
DRIVER_SHA = '1f11aefdc11805387b0c345583828fd733e5e38b0b0e043b0510808f648e8430'
PARK_SHA = '953dec241be0f4c76d254cdca6efc4da2f334b978338eded49c694dd2f1001b5'
BIT_SHA = '86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f'
HWH_SHA = 'eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c'


def restore_bounded(print_fn):
    outcome = {'restore_error': None}
    try:
        __import__('m2_onboard').cmd_load()
        deadline = time.monotonic() + 40.0
        last = None
        while time.monotonic() < deadline:
            try:
                print_fn('RESTORE-SMOKE: trying')
                __import__('m2_onboard').cmd_smoke()
                outcome['smoke'] = 'PASS'
                break
            except SystemExit:
                last = 'SystemExit'
            except RuntimeError as exc:
                last = repr(exc)
                if 'busy' not in last:
                    raise
                print_fn('RESTORE-RETRY: commit busy; frame-gated pending')
            time.sleep(1.0)
        else:
            outcome['smoke'] = 'TIMEOUT last=' + str(last)
    except BaseException as exc:
        outcome['restore_error'] = repr(exc)
    print_fn('RESTORE: ' + json.dumps(outcome))
    return outcome


def main():
    from pynq import MMIO, PL, allocate, Overlay
    import cv2
    sys.path.insert(0, SITE)
    import m2_onboard
    sys.path.insert(0, str(TRIAL))
    from c01_capture import QUARANTINE
    from c01_park_capture import ParkFrameCapture
    from c01_status_onboard import verify, load_candidate
    for name, sha in (('c01_capture.py', DRIVER_SHA), ('c01_park_capture.py', PARK_SHA)):
        if hashlib.sha256((TRIAL / name).read_bytes()).hexdigest() != sha:
            raise RuntimeError('trial module is not the reviewed bytes: ' + name)
    bit = TRIAL / 'capture.bit'
    if not PL.bitfile_name or 'capture' not in str(PL.bitfile_name):
        verify(bit, BIT_SHA)
        verify(bit.with_suffix('.hwh'), HWH_SHA)
        load_candidate(bit, Overlay)
    if 'capture' not in str(PL.bitfile_name):
        raise RuntimeError('candidate overlay is not loaded: %r' % PL.bitfile_name)
    lock = (Path(SITE) / 'c01-capture.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status, dma = MMIO(0x42000000, 65536), MMIO(0x43000000, 65536)
    # Fresh downloads need >15 s before the capture block sees frames (2026-10-15/16
    # board records): poll lock + one real tick inside a bounded settle window.
    tick_a, tick_b, settled = 0, 0, False
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        tick_a = status.read(8)
        time.sleep(1.0)
        tick_b = status.read(8)
        if tick_b > tick_a and status.read(4) & 1:
            settled = True
            print('PRECHECK: video locked, +%d frames; settle %.1f s' % (tick_b - tick_a, 30.0 - (deadline - time.monotonic())), flush=True)
            break
        print('SETTLE: tick %d->%d csr=0x%x' % (tick_a, tick_b, status.read(4)), flush=True)
    if not settled:
        raise RuntimeError('frame counter did not tick within 30 s settle; video absent')
    def identity():
        return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                PL.bitfile_name, str(PL.timestamp))
    boot = identity()[0]
    result = {'boot_before': boot, 'driver_sha256': DRIVER_SHA, 'park_sha256': PARK_SHA,
              'bit_sha256': BIT_SHA, 'video_framerate_delta': tick_b - tick_a,
              'kind': 'C01_PARK_CANDIDATE_FIRST_BOARD_RUN_NOT_FORMAL_N03'}
    owner, primary = None, None
    try:
        owner = ParkFrameCapture(dma, status, allocate, identity)
        frame = owner.capture()
        result['capture'] = owner.evidence
        result['shape'], result['strides'] = list(frame.shape), list(frame.strides)
        result['pixel_sha256'] = hashlib.sha256(frame.tobytes()).hexdigest()
        result['channel_mean_bgr'] = frame.mean(axis=(0, 1)).tolist()
        result['pixel_min'], result['pixel_max'] = int(frame.min()), int(frame.max())
        png = TRIAL / 'park-frame.png'
        if not cv2.imwrite(str(png), frame):
            raise RuntimeError('PNG write failed')
        decoded = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if decoded is None or not np.array_equal(decoded, frame):
            raise RuntimeError('PNG round-trip mismatch')
        result['png_sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
        result['ok'] = True
        print('PASS: park warmup clear held; slot-0 protected copy complete', flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
        if owner is not None:
            result['capture'] = owner.evidence
        print('MAIN-FAIL:', repr(exc), flush=True)
    finally:
        if QUARANTINE or (owner is not None and owner.may_write):
            result['unsafe_stop'] = True
            print('UNSAFE-STOP: buffers held; process stays alive; physical board reset required', flush=True)
            while True:
                time.sleep(1)
        result['restore'] = restore_bounded(lambda msg: print(msg, flush=True))
        result['boot_after'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        print('RESULT:', json.dumps(result), flush=True)
    if primary is not None:
        raise primary
    if result['boot_after'] != boot:
        raise RuntimeError('board rebooted during capture')
    print('PASS: original vision restored; park candidate board run complete', flush=True)


if __name__ == '__main__':
    main()
