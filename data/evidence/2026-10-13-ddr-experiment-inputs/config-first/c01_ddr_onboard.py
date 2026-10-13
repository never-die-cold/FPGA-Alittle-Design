"""Bounded custom C01 single-frame experiment; preserve original vision."""
import fcntl
import hashlib
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
from c01_capture import SingleFrameCapture, QUARANTINE
from c01_status_onboard import verify, load_candidate, restore_original

BIT_SHA = '86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f'
HWH_SHA = 'eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c'


def main():
    from pynq import MMIO, Overlay, allocate, PL
    import cv2
    sys.path.insert(0, '/home/xilinx/vision_m2')
    import m2_onboard
    root = Path(__file__).resolve().parent
    bit = Path(os.environ['C01_BIT'])
    output = root / 'ddr-result.json'
    if output.exists(): raise RuntimeError('new evidence directory required')
    lock = (Path('/home/xilinx/vision_m2') / 'c01-capture.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    original = Path('/home/xilinx/vision_m2/vision.bit')
    verify(original, '4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5')
    verify(original.with_suffix('.hwh'), 'c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5')
    verify(bit, BIT_SHA); verify(bit.with_suffix('.hwh'), HWH_SHA)
    # Do not unload an unknown active owner.
    if Path(PL.bitfile_name).resolve() != original.resolve():
        raise RuntimeError('active overlay is not the expected idle original vision')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    def identity():
        return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(), PL.bitfile_name, str(PL.timestamp))
    result = {'boot_before': boot, 'bit_sha256': BIT_SHA, 'hwh_sha256': HWH_SHA,
              'driver_sha256': hashlib.sha256((root / 'c01_capture.py').read_bytes()).hexdigest(),
              'kind': 'CUSTOM_DDR_SINGLE_FRAME_EXPERIMENT_NOT_FORMAL_N03'}
    owner = None
    attempted = False
    primary = None
    try:
        attempted = True
        overlay = load_candidate(bit, Overlay)
        dma, status = MMIO(0x43000000, 65536), MMIO(0x42000000, 65536)
        if dma.read(0x30) & 1 or not dma.read(0x34) & 1:
            attempted = False
            raise RuntimeError('candidate DMA unexpectedly active; do not restore over owner')
        for _ in range(100):
            if status.read(4) & 1: break
            time.sleep(.05)
        else: raise RuntimeError('video lock did not settle')
        time.sleep(2)
        m2_onboard.cmd_smoke()
        owner = SingleFrameCapture(dma, status, allocate, identity)
        print('STAGE: custom single-frame DMA begins', flush=True)
        frame = owner.capture()
        result['capture'] = owner.evidence
        result['shape'], result['strides'] = list(frame.shape), list(frame.strides)
        result['pixel_sha256'] = hashlib.sha256(frame.tobytes()).hexdigest()
        result['channel_mean_bgr'] = frame.mean(axis=(0, 1)).tolist()
        result['pixel_min'], result['pixel_max'] = int(frame.min()), int(frame.max())
        png = root / 'custom-ddr.png'
        if not cv2.imwrite(str(png), frame): raise RuntimeError('PNG write failed')
        decoded = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if decoded is None or not np.array_equal(decoded, frame): raise RuntimeError('PNG round-trip mismatch')
        result['png_sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
        result['png_path'] = str(png)
        result['ok'] = True
        print('PASS: custom DDR complete independent frame', json.dumps(result), flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
        if owner is not None: result['capture'] = owner.evidence
        print('MAIN-FAIL:', repr(exc), flush=True)
    finally:
        if QUARANTINE or (owner is not None and owner.may_write):
            result['unsafe_stop'] = True
            output.write_text(json.dumps(result, indent=2))
            print('UNSAFE-STOP: buffers held; process stays alive; physical board reset required', flush=True)
            # Never exit and run native-buffer finalizers while DMA stop is unknown.
            while True: time.sleep(1)
        if attempted:
            try:
                restore_original(m2_onboard.cmd_load, m2_onboard.cmd_smoke)
                result['restored'] = True
            except BaseException as exc:
                result['restore_error'] = repr(exc)
                if primary is None: primary = exc
        result['boot_after'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        output.write_text(json.dumps(result, indent=2))
        print('RESULT:', json.dumps(result), flush=True)
    if primary is not None: raise primary
    if result['boot_after'] != boot: raise RuntimeError('board rebooted during capture')
    print('PASS: custom DDR cleanup and original vision restoration', flush=True)


if __name__ == '__main__': main()
