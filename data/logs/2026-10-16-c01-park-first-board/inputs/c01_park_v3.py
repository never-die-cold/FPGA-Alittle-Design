"""Park walk v3: transient-tolerant warmup, timed slot walks, protected copy.

NOT formal N03. Implements the hardware-observed contract on the candidate
overlay: (a) the one-frame start-overflow transient self-recovers while a
latched кап4 bit3 stays set, so health is judged by lock/pending/epoch-delta
instead of the 0xC mask; (b) halt-time 0x4810 clears by W1C only while RS=1
and repeats are legitimate warmup actions (park driver rule); (c) the park
current-slot grant may lag the request ~2 s, so every walk waits up to 6 s
and records its own latency; (d) slot-0 is copied twice under park-1
protection, PNG round-tripped, and the run is stopped to record the post-stop
transient before restoring the original vision. Publish-free.
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
SHAPE, FRAME_BYTES = (720, 1280, 3), 2764800


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
    result = {'kind': 'C01_PARK_WALK_V3_NOT_FORMAL_N03',
              'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    buffers, primary, started = [], None, False
    state = {'epoch': None, 'seq': None}

    def health(tag, ref):
        reading = {'tag': tag, 'lock': bool(status.read(4) & 1),
                   'pending': bool(status.read(4) & 0x4),
                   'epoch_delta': status.read(0x10) - ref['epoch'],
                   'seq': status.read(8), 'seq_delta': status.read(8) - ref['seq'],
                   'rej_delta': status.read(0xc) - ref['rej'], 'loss': status.read(0x20),
                   'sr': hex(dma.read(SR)), 'park': hex(dma.read(PARK))}
        return reading

    def walk(slot, timeout=6.0, warmup=False):
        if slot is not None:
            dma.write(PARK, (dma.read(PARK) & ~0x1F00) | (slot << 8))
        begin, clears = time.monotonic(), 0
        while True:
            cap4 = status.read(4)
            if not cap4 & 1:
                raise StopRequired('video lock lost during park walk')
            if cap4 & 0x4:
                if time.monotonic() - begin > 1.0:
                    raise StopRequired('capture overflow pending held >1 s mid-walk')
            sr, park = dma.read(SR), dma.read(PARK)
            errors = sr & ERRORS
            if warmup and errors == HALT_STICKY:
                dma.write(SR, W1C_PARK)
                clears += 1
            elif errors and not errors & ~HALT_STICKY:
                pass
            running = sr & 0x10000 or not sr & 1
            if time.monotonic() - begin > timeout:
                result.setdefault('walks', []).append({'slot': slot, 'result': 'timeout',
                                                       'sr': hex(sr), 'park': hex(park), 'clears': clears})
                raise StopRequired('park walk to slot %r timed out after %.1f s' % (slot, timeout))
            current = (park >> 24) & 0x1F
            if warmup:
                if current == slot and sr & IRQ and not errors:
                    result.setdefault('walks', []).append(
                        {'slot': slot, 'result': 'ok', 'seconds': time.monotonic() - begin,
                         'clears': clears, 'sr': hex(sr), 'park': hex(park)})
                    return
            elif current == slot and sr & IRQ and not errors:
                result.setdefault('walks', []).append(
                    {'slot': slot, 'result': 'ok', 'seconds': time.monotonic() - begin,
                     'sr': hex(sr), 'park': hex(park)})
                return
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
        walk(1, warmup=True)                     # warmup: halt-fault W1C clears land here
        walk(0)                                  # visit slot 0
        walk(1)                                  # park back: slot 0 protected
        result['protected_before'] = health('protected_before', state)
        t1 = time.monotonic()
        buffers[0].invalidate()
        first = np.array(buffers[0], dtype=np.uint8, copy=True, order='C')
        second = np.array(buffers[0], dtype=np.uint8, copy=True, order='C')
        result['copy_seconds'] = time.monotonic() - t1
        result['protected_after'] = health('protected_after', state)
        result['first_pixel_sha256'] = hashlib.sha256(first.tobytes()).hexdigest()
        result['second_pixel_sha256'] = hashlib.sha256(second.tobytes()).hexdigest()
        result['channel_mean_bgr'] = first.mean(axis=(0, 1)).tolist()
        png = TRIAL / 'park-v3-frame.png'
        if not cv2.imwrite(str(png), first):
            raise StopRequired('PNG write failed')
        decoded = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if decoded is None or not np.array_equal(decoded, first):
            raise StopRequired('PNG round-trip mismatch')
        print('COPY-SUMMARY: mean=%s min=%d max=%d png=%s' % (
            result['channel_mean_bgr'], int(first.min()), int(first.max()),
            hashlib.sha256(png.read_bytes()).hexdigest()), flush=True)
        primary = None
        result['ok'] = True
        print('PASS: protected slot-0 copy from a running channel', flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
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
                                          'rej': status.read(0xc) - state['rej'],
                                          'epoch': status.read(0x10) - state['epoch']}
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
