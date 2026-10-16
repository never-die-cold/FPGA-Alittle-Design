"""During-run observer for the capture STATUS block while S2MM runs.

NOT formal N03. Replicates the reviewed park sequence with full logging of
every MMIO the driver touches plus 100 ms samples of CR/SR/PARK, capture CSR
0x04/0x08/0x0c/0x10/0x1c/0x20 and pipe R11/R12, to identify which status bit
changes when the channel starts (run2 failed _check_source with no snapshot).
Warmup W1C of the recorded 0x4810 follows the park driver's exact rule while
RS=1; publish-free; stop/restore semantics identical to the frozen entry.
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
W1C_PARK = HALT_STICKY | IRQ | 0x2000


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
    pipe = MMIO(0x40000000, 65536)
    deadline = time.monotonic() + 30.0
    while True:
        tick_a = status.read(8)
        time.sleep(1.0)
        if status.read(8) > tick_a and status.read(4) & 1:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('video settle timeout on candidate')
    print('PRECHECK: video locked and ticking', flush=True)

    def snap(tag):
        reading = {'cap4': hex(status.read(4)), 'seq': status.read(8),
                   'rej': status.read(0xc), 'epoch': status.read(0x10),
                   'ovf': status.read(0x1c), 'loss': status.read(0x20),
                   'cr': hex(dma.read(CR)), 'sr': hex(dma.read(SR)),
                   'park': hex(dma.read(PARK)), 'r11': pipe.read(44), 'r12': pipe.read(48)}
        print(tag + ': ' + json.dumps(reading), flush=True)
        return reading

    result = {'kind': 'C01_WARMUP_RUNSTATE_OBSERVER_NOT_FORMAL_N03',
              'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    buffers, primary, started = [], None, False
    try:
        for _ in range(4):
            buffers.append(allocate(shape=(720, 1280, 3), dtype=np.uint8))
        snap('HALTED_BASELINE')
        dma.write(PARK, (dma.read(PARK) & ~0x1F00) | (1 << 8))
        for i, b in enumerate(buffers):
            dma.write(ADDRESS + i * 4, int(b.physical_address))
        dma.write(STRIDE, 3840)
        dma.write(HSIZE, 3840)
        dma.write(CR, PARK_RUN)
        started = True
        dma.write(VSIZE, 720)
        snap('JUST_STARTED')
        dma.write(SR, W1C_SWEEP)
        t_run, samples, clears = time.monotonic(), [], 0
        outcome = 'timeout'
        while time.monotonic() - t_run < 6.0:
            reading = {'t': round(time.monotonic() - t_run, 2), 'sr': dma.read(SR),
                       'cap4': status.read(4), 'seq': status.read(8),
                       'rej': status.read(0xc), 'epoch': status.read(0x10),
                       'ovf': status.read(0x1c), 'loss': status.read(0x20),
                       'park': dma.read(PARK), 'cr': dma.read(CR), 'r11': pipe.read(44)}
            samples.append(reading)
            current = status.read(4)
            if not current & 1 or current & 0xC:
                outcome = 'cap_lock_fault_at_%ss' % round(time.monotonic() - t_run, 2)
                break
            if reading['sr'] & ERRORS and not reading['cr'] & 1:
                outcome = 'channel_halted_with_errors_%s' % hex(reading['sr'])
                break
            if (reading['park'] >> 24) & 0x1F == 1 and reading['sr'] & IRQ and not (reading['sr'] & ERRORS):
                outcome = 'warmup_slot1_reached'
                break
            errors = reading['sr'] & ERRORS
            if errors == HALT_STICKY:
                dma.write(SR, W1C_PARK)
                clears += 1
            time.sleep(0.1)
        result['samples_head'] = samples[:40]
        result['samples_tail'] = samples[-12:]
        result['warmup_clears'] = clears
        result['outcome'] = outcome
        print('OBSERVER-OUTCOME: ' + outcome + ' clears=%d' % clears, flush=True)
        if outcome == 'warmup_slot1_reached':
            snap('WARMUP_OK')
    except BaseException as exc:
        primary = exc
        result['main_error'] = repr(exc)
        result['failed'] = snap('FAIL_STATE')
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
                snap('AFTER_STOP')
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
