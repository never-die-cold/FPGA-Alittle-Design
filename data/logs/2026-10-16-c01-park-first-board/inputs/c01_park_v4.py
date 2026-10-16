"""Park walk v4: repeat-W1C warmup under the latched-bit reality, timed grants.

Run 3 missed its clears because SR carries IRQ (bit12, outside the ERRORS
mask) from the first frame, so `errors == HALT_STICKY` never matched while
errors was 0x810 (bits 4/11). Run 2 showed a mid-run W1C clears 4/11 for good
and the park current-slot grant followed. v4 therefore: W1C-sweeps once at
start (clears bit14), repeatedly W1C-clears while `errors & HALT_STICKY`
during warmup, waits up to 8 s for grant, records every grant latency and
every W1C, then walks 0->1 and makes two protected copies of slot 0 with
epoch-delta/lock/pending health; stops, records the post-stop ~180-interval
transient, restores the original vision. Publish-free diagnostic.
"""
import fcntl
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

SITE = '/home/xilinx/vision_m2'
TRIAL = Path(SITE) / 'c01-ff610bdae8ef46ce9304e531ebaf9627'
CR, SR, PARK = 0x30, 0x34, 0x28
VSIZE, HSIZE, STRIDE, ADDRESS = 0xA0, 0xA4, 0xA8, 0xAC
ERRORS, IRQ, RUN = 0xC9F0, 0x1000, 0x11011
PARK_RUN = RUN & ~0x10
HALT_STICKY = 0x4810
W1C_PARK = HALT_STICKY | IRQ | 0x2000
W1C_SWEEP = ERRORS | IRQ | 0x2000
SHAPE = (720, 1280, 3)


class StopRequired(RuntimeError):
    pass


def main():
    from pynq import MMIO, PL, allocate, Overlay
    import cv2
    sys.path.insert(0, SITE)
    import m2_onboard
    sys.path.insert(0, str(TRIAL))
    from c01_status_onboard import verify, load_candidate
    bit = TRIAL / 'capture.bit'
    if not PL.bitfile_name or 'capture' not in str(PL.bitfile_name):
        verify(bit, '86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f')
        verify(bit.with_suffix('.hwh'), 'eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c')
        load_candidate(bit, Overlay)
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
    result = {'kind': 'C01_PARK_WALK_V4_NOT_FORMAL_N03',
              'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    buffers, primary, started = [], None, False
    state = {}

    def health(tag, ref):
        return {'tag': tag, 'lock': bool(status.read(4) & 1),
                'pending': bool(status.read(4) & 0x4),
                'epoch_delta': status.read(0x10) - ref['epoch'], 'rej_delta': status.read(0xc) - ref['rej'],
                'seq': status.read(8), 'seq_delta': status.read(8) - ref['seq'],
                'loss': status.read(0x20), 'sr': hex(dma.read(SR)), 'park': hex(dma.read(PARK))}

    def walk(slot, timeout=8.0, warmup=False):
        if slot is not None:
            dma.write(PARK, (dma.read(PARK) & ~0x1F00) | (slot << 8))
        begin, record = time.monotonic(), {'slot': slot, 'warmup': warmup, 'clears': []}
        while True:
            cap4 = status.read(4)
            if not cap4 & 1:
                record['result'] = 'lock_lost'
                result.setdefault('walks', []).append(record)
                raise StopRequired('video lock lost during park walk')
            sr, park = dma.read(SR), dma.read(PARK)
            errors = sr & ERRORS
            if warmup and errors & HALT_STICKY:
                dma.write(SR, W1C_PARK)
                record['clears'].append({'t': round(time.monotonic() - begin, 3), 'errors': hex(errors)})
            current = (park >> 24) & 0x1F
            if time.monotonic() - begin > timeout:
                record.update(result='timeout', sr=hex(sr), park=hex(park),
                              mmio_seconds=time.monotonic() - begin)
                result.setdefault('walks', []).append(record)
                raise StopRequired('park walk to slot %r timed out after %.1f s' % (slot, timeout))
            if current == (slot if slot is not None else current) and sr & IRQ \
                    and not errors and not cap4 & 0x4:
                record.update(result='ok', seconds=time.monotonic() - begin,
                              sr=hex(sr), park=hex(park), cap4=cap4)
                result.setdefault('walks', []).append(record)
                return record
            time.sleep(0.05)

    try:
        for _ in range(4):
            b = allocate(shape=SHAPE, dtype=np.uint8)
            if int(b.physical_address) % 64:
                raise StopRequired('allocation alignment invalid')
            buffers.append(b)
        result['buffers'] = [int(b.physical_address) for b in buffers]
        state.update(epoch=status.read(0x10), seq=status.read(8), rej=status.read(0xc))
        dma.write(PARK, (dma.read(PARK) & ~0x1F00) | (1 << 8))
        for i, b in enumerate(buffers):
            dma.write(ADDRESS + i * 4, int(b.physical_address))
        dma.write(STRIDE, 3840)
        dma.write(HSIZE, 3840)
        dma.write(CR, PARK_RUN)
        started = True
        dma.write(VSIZE, 720)
        dma.write(SR, W1C_SWEEP)
        walk(None, warmup=True)     # warmup against the just-armed request (slot 1)
        walk(0)                     # visit slot 0
        walk(1)                     # park back on slot 1: slot 0 is protected
        result['protected_before'] = health('protected_before', state)
        t1 = time.monotonic()
        buffers[0].invalidate()
        first = np.array(buffers[0], dtype=np.uint8, copy=True, order='C')
        second = np.array(buffers[0], dtype=np.uint8, copy=True, order='C')
        result['copy_seconds'] = time.monotonic() - t1
        result['protected_after'] = health('protected_after', state)
        result['first_pixel_sha256'] = hashlib.sha256(first.tobytes()).hexdigest()
        result['second_pixel_sha256'] = hashlib.sha256(second.tobytes()).hexdigest()
        result['copies_identical'] = bool(np.array_equal(first, second))
        result['channel_mean_bgr'] = first.mean(axis=(0, 1)).tolist()
        png = TRIAL / 'park-v4-frame.png'
        if not cv2.imwrite(str(png), first):
            raise StopRequired('PNG write failed')
        decoded = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if decoded is None or not np.array_equal(decoded, first):
            raise StopRequired('PNG round-trip mismatch')
        result['png_sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
        result['ok'] = True
        print('COPY-SUMMARY: mean=%s identical=%s' % (result['channel_mean_bgr'],
                                                      result['copies_identical']), flush=True)
        print('PASS: protected slot-0 copy from a running channel', flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
        result['failed'] = health('failed', state)
        print('MAIN-FAIL:', repr(exc), flush=True)
    finally:
        stopped = False
        if started:
            try:
                dma.write(CR, dma.read(CR) & ~1)
                end = time.monotonic() + 3.0
                while time.monotonic() < end and not (dma.read(SR) & 1 and not dma.read(CR) & 1):
                    time.sleep(0.002)
                if not (dma.read(SR) & 1 and not dma.read(CR) & 1):
                    dma.write(CR, 4)
                    end = time.monotonic() + 3.0
                    while time.monotonic() < end and not (not dma.read(CR) & 5 and dma.read(SR) & 1):
                        time.sleep(0.002)
                    stopped = bool(dma.read(SR) & 1 and not dma.read(CR) & 1)
                else:
                    stopped = True
                result['stopped'] = stopped
                time.sleep(3.0)
                result['post_stop_3s'] = {'cap4': status.read(4), 'seq': status.read(8),
                                          'rej_delta': status.read(0xc) - state['rej'],
                                          'epoch_delta': status.read(0x10) - state['epoch']}
                print('POST-STOP-3S: ' + json.dumps(result['post_stop_3s']), flush=True)
            except BaseException as exc:
                result['stop_error'] = repr(exc)
        for b in buffers:
            try:
                b.freebuffer()
            except BaseException as exc:
                result.setdefault('free_errors', []).append(repr(exc))
        if not stopped:
            result['unsafe_stop'] = True
            print('UNSAFE-STOP: buffers held; process stays alive; physical board reset required', flush=True)
            while True:
                time.sleep(1)
        outcome = {'restore_error': None}
        try:
            m2_onboard.cmd_load()
            deadline = time.monotonic() + 40.0
            last = None
            while time.monotonic() < deadline:
                try:
                    m2_onboard.cmd_smoke()
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
                outcome['smoke'] = 'TIMEOUT ' + str(last)
        except BaseException as exc:
            outcome['restore_error'] = repr(exc)
        result['restore'] = outcome
        print('RESULT:', json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
