"""Run-state steady observation: tolerate the one-frame start transient.

Run 1 established: starting S2MM overflows the capture bridge for exactly one
interval (rej+1/epoch+1/ovf+1) that self-recovers while lock holds; run 2 and
run 1 aborted on that transient. This observer keeps polling across it and
answers, with data: (1) does stream_seq advance (frames actually written);
(2) when does SR IRQ assert under continuous circular run; (3) how does the
park current-slot field move; (4) does a mid-run W1C hold clean; (5) does the
0x4810 halt-pattern re-accumulate after a stop. Publish-free; UNSAFE-STOP and
restoration semantics identical to the frozen entry.
"""
import fcntl
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
W1C_SWEEP = ERRORS | IRQ | 0x2000


def main():
    from pynq import MMIO, PL, allocate, Overlay
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
    print('PRECHECK: video locked and ticking', flush=True)
    result = {'kind': 'C01_RUNSTATE_STEADY_OBSERVER_NOT_FORMAL_N03',
              'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    buffers, primary, started = [], None, False
    try:
        for _ in range(4):
            buffers.append(allocate(shape=(720, 1280, 3), dtype=np.uint8))
        result['baseline'] = {'sr': hex(dma.read(SR)), 'cap4': status.read(4), 'seq': status.read(8),
                              'rej': status.read(0xc), 'epoch': status.read(0x10),
                              'ovf': status.read(0x1c), 'loss': status.read(0x20), 'park': hex(dma.read(PARK))}
        epoch0, seq0, rej0 = status.read(0x10), status.read(8), status.read(0xc)
        dma.write(PARK, (dma.read(PARK) & ~0x1F00) | (1 << 8))
        for i, b in enumerate(buffers):
            dma.write(ADDRESS + i * 4, int(b.physical_address))
        dma.write(STRIDE, 3840)
        dma.write(HSIZE, 3840)
        dma.write(CR, PARK_RUN)
        started = True
        dma.write(VSIZE, 720)
        dma.write(SR, W1C_SWEEP)
        samples, t_run = [], time.monotonic()
        outcome, stayed = 'timeout', True
        midrun_done = False
        while time.monotonic() - t_run < 6.0:
            sample = {'t': round(time.monotonic() - t_run, 2), 'sr': dma.read(SR),
                      'cap4': status.read(4), 'seq': status.read(8),
                      'rej': status.read(0xc) - rej0, 'epoch': status.read(0x10) - epoch0,
                      'ovf': status.read(0x1c), 'loss': status.read(0x20),
                      'park': dma.read(PARK), 'cr': dma.read(CR)}
            samples.append(sample)
            if not sample['cap4'] & 1:
                outcome, stayed = 'lock_lost', False
                break
            if sample['cap4'] & 0x4:
                outcome = 'overflow_pending_sustained'
                break
            if sample['loss'] != 0 or sample['epoch'] > 2:
                outcome = 'repeated_error_events'
                break
            if not midrun_done and sample['seq'] - seq0 >= 30 and sample['t'] >= 2.0:
                dma.write(SR, W1C_SWEEP)   # mid-run W1C, then watch hold/slip
                sample['midrun_w1c'] = True
                midrun_done = True
            if sample['t'] >= 5.0 and sample['seq'] > seq0:
                outcome = 'steady_5s'
                break
            time.sleep(0.1)
        result['samples'] = samples
        result['outcome'] = outcome
        print('OBSERVER-OUTCOME: ' + outcome, flush=True)
    except BaseException as exc:
        primary = exc
        result['main_error'] = repr(exc)
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
                result['post_stop_3s'] = {'sr': hex(dma.read(SR)), 'cr': hex(dma.read(CR)),
                                          'cap4': status.read(4), 'seq': status.read(8),
                                          'rej': status.read(0xc), 'epoch': status.read(0x10),
                                          'ovf': status.read(0x1c)}
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
