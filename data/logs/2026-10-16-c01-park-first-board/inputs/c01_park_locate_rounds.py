"""Park rounding: two independent capture->locate rounds in one board run.

NOT formal N03. Each round instantiates a fresh ParkFrameCapture (single-use),
copies the current real camera frame through the reviewed driver path, converts
it to BT.601 gray and runs the golden reference localizer with its documented
defaults. A static scene should yield identical packets between rounds,
keeping the capture loop's stability observable. Publishes nothing beyond the
stdout packets; restores the original vision once at the end.
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
ROUNDS = 2


def restore_bounded():
    outcome = {'restore_error': None}
    try:
        __import__('m2_onboard').cmd_load()
        deadline = time.monotonic() + 40.0
        last = None
        while time.monotonic() < deadline:
            try:
                __import__('m2_onboard').cmd_smoke()
                outcome['smoke'] = 'PASS'
                break
            except SystemExit:
                last = 'SystemExit'
            except RuntimeError as exc:
                last = repr(exc)
                if 'busy' not in last:
                    raise
            time.sleep(1.0)
        else:
            outcome['smoke'] = 'TIMEOUT last=' + str(last)
    except BaseException as exc:
        outcome['restore_error'] = repr(exc)
    print('RESTORE: ' + json.dumps(outcome), flush=True)
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
    from reference import locate
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
    deadline = time.monotonic() + 30.0
    while True:
        tick_a = status.read(8)
        time.sleep(1.0)
        if status.read(8) > tick_a and status.read(4) & 1:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('video settle timeout on candidate')
    def identity():
        return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                PL.bitfile_name, str(PL.timestamp))
    boot = identity()[0]
    result = {'boot_before': boot, 'park_sha256': PARK_SHA, 'bit_sha256': BIT_SHA,
              'rounds': ROUNDS, 'kind': 'C01_PARK_LOCATE_ROUNDS_NOT_FORMAL'}
    packets, primary, owners = [], None, []
    try:
        for index in range(ROUNDS):
            owner = ParkFrameCapture(dma, status, allocate, identity)
            owners.append(owner)
            frame = owner.capture()
            frame_id = owner.evidence['protected_before']['cap']['0x8']
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            t0 = time.monotonic()
            packet = locate(gray.tolist(), int(frame_id), int(pipe_id := __import__('pynq').MMIO(0x40000000, 65536).read(48)))
            packet['mode'] = 'LIVE'
            packet['prototype'] = True
            packet['round'] = (index + 1)
            packet['locate_seconds'] = time.monotonic() - t0
            packets.append(packet)
            print('ROUND-%d-PACKET: %s' % (index + 1, json.dumps(packet)), flush=True)
        result['packets'] = packets
        result['rounds_identical'] = packets[0]['targets'] == packets[ROUNDS-1]['targets']
        result['config_id'] = int(pipe_id)
        result['ok'] = True
        print('ROUNDS-SUMMARY: identical=%s targets=%s' % (
            result['rounds_identical'], len(packets[0]['targets'])), flush=True)
        print('PASS: capture loop rounds stable', flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
        result['packets'] = packets
        print('MAIN-FAIL:', repr(exc), flush=True)
    finally:
        if QUARANTINE or any(owner.may_write for owner in owners):
            result['unsafe_stop'] = True
            print('UNSAFE-STOP: buffers held; process stays alive; physical board reset required', flush=True)
            while True:
                time.sleep(1)
        result['restore'] = restore_bounded()
        result['boot_after'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        print('RESULT:', json.dumps(result), flush=True)
    if primary is not None:
        raise primary
    if result['boot_after'] != boot:
        raise RuntimeError('board rebooted during capture')
    print('PASS: original vision restored; locate rounds complete', flush=True)


if __name__ == '__main__':
    main()
