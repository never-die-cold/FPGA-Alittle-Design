"""Halt-period S2MM error-bit persistence diagnostic; never starts the DMA.

Loads the frozen candidate over idle original vision, then samples S2MM_VDMASR
while the channel stays halted (RS=0) and the 60 fps stream keeps flowing:
accumulation over 12 s, one bounded W1C sweep with an immediate/t-1 s/t-3 s
readback, then a second W1C to separate read-only level bits from genuinely
sticky-but-reasserting ones. Never writes RUN, allocates nothing; restores
original vision with a bounded busy-aware smoke loop recorded in this log.
"""
import json
import sys
import time
from pathlib import Path

SITE = '/home/xilinx/vision_m2'
TRIAL = Path(SITE) / 'c01-ff610bdae8ef46ce9304e531ebaf9627'
CR, SR = 0x30, 0x34
W1C_MASK = 0xF9F0  # c01_capture.py ERRORS|IRQ|0x2000: bits 4..15 + ErrIRQ(16)
NAMES = {0: 'Halted', 4: 'stickyA', 11: 'stickyB', 14: 'stickyC', 16: 'ErrIRQ'}


def bits(value):
    return [NAMES[b] for b in NAMES if value >> b & 1]


def main():
    from pynq import MMIO, Overlay, PL
    sys.path.insert(0, SITE)
    import m2_onboard
    from c01_status_onboard import load_candidate
    if not PL.bitfile_name or 'vision.bit' not in PL.bitfile_name:
        raise RuntimeError('original vision is not loaded: %r' % PL.bitfile_name)
    result = {'kind': 'C01_HALTD_SR_PERSISTENCE_DIAGNOSTIC_NO_RUN'}
    try:
        load_candidate(TRIAL / 'capture.bit', Overlay)
        dma = MMIO(0x43000000, 65536)
        if dma.read(CR) & 1 or not dma.read(SR) & 1:
            raise RuntimeError('candidate DMA not idle-halted; no mutation behind owner')
        series = []
        t0 = time.monotonic()
        while time.monotonic() - t0 < 12.0:
            series.append({'t': round(time.monotonic() - t0, 1), 'sr': dma.read(SR)})
            time.sleep(1.5)
        result['sr_series'] = series

        def sweep(tag):
            path = {}
            dma.write(SR, W1C_MASK)
            path['t0_w1c_readback'] = dma.read(SR)
            time.sleep(1.0)
            path['t1_readback'] = dma.read(SR)
            time.sleep(3.0)
            path['t4_readback'] = dma.read(SR)
            print(tag + ': ' + json.dumps(path), flush=True)
            return path
        result['sweep1'] = dict(bits(series[-1]['sr']), **{}, **{'w1c': sweep('SWEEP1')}) if False else sweep('SWEEP1')
        result['sweep2'] = sweep('SWEEP2')
        still = dma.read(SR)
        time.sleep(3.0)
        result['tail'] = {'sr': still, 'sr_after_3s': dma.read(SR),
                          'cr': dma.read(CR), 'cr_stopped': bool(dma.read(CR) & 1) is False}
        print('TAIL: ' + json.dumps(result['tail']), flush=True)
        ok = True
    except BaseException as exc:
        result['main_error'] = repr(exc)
        print('MAIN-FAIL:', repr(exc), flush=True)
        raise
    finally:
        outcome = {'restore_error': None}
        try:
            m2_onboard.cmd_load()
            outcome['loaded'] = True
            deadline = time.monotonic() + 40.0
            last = None
            while time.monotonic() < deadline:
                try:
                    m2_onboard.cmd_smoke()
                    outcome['smoke'] = 'PASS'
                    break
                except SystemExit as exc:
                    last = 'NOVIDEO(%s)' % exc.code
                except RuntimeError as exc:
                    last = repr(exc)
                    if 'busy' not in repr(exc):
                        raise
                time.sleep(1.0)
            else:
                outcome['smoke'] = 'TIMEOUT last=' + str(last)
        except BaseException as exc:
            outcome['restore_error'] = repr(exc)
            print('RECOVERY-FAIL:', repr(exc), flush=True)
        result['restore'] = outcome
        print('RESULT:', json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
