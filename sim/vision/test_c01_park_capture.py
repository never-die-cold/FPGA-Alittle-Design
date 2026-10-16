"""Continuous-park ownership model; repository-only, never imports PYNQ.

The rig encodes the 2026-10-16 board records (data/logs/2026-10-16-c01-park-first-board/):
arming the S2MM overflows the capture bridge for one interval that clears
itself (cap bit2 read-visible at most once), cap bit3 "had error" latches for
the overlay instance, epoch/ovf gain exactly +1 from that transient, halt
time 0x4810 re-asserts until W1C, and a real second fault after the warmup
baseline is refused rather than masked.
"""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/pynq_host'))
from c01_capture import CR, SR, PARK, VSIZE, ADDRESS, SHAPE, CaptureError, QUARANTINE
from c01_park_capture import ParkFrameCapture, PARK_RUN, HALT_STICKY, W1C_PARK


class Buffer(np.ndarray):
    def __new__(cls, address, rig):
        obj = np.zeros(SHAPE, np.uint8).view(cls)
        obj.physical_address, obj.rig, obj.frees = address, rig, 0
        return obj
    def invalidate(self):
        self.rig.events.append('invalidate')
        for _ in range(30):
            self.rig.read(SR)  # Deliberately slower than many frame periods.
        if self.rig.mode == 'copy_error': self.rig.reg[SR] |= 0x20
        if self.rig.mode == 'copy_sticky': self.rig.reg[SR] |= HALT_STICKY
        if self.rig.mode == 'copy_generation': self.rig.generation = 'B'
    def freebuffer(self):
        self.frees += 1
        self.rig.events.append('free')


class Rig:
    def __init__(self, mode='ok'):
        self.mode, self.t, self.polls, self.generation = mode, 0., 0, 'A'
        self.reg, self.buffers, self.events = {CR: 0, SR: 1, PARK: 0}, [], []
        self.cap = {o: 0 for o in range(0, 0x24, 4)}
        self.cap.update({0: 0x43415031, 4: 3, 0x14: 1280, 0x18: 720})  # lock+tracking, fault-free.
        self.street = 0  # extra epoch/ovf bump after the warm-up re-baseline (double_transient).
        self.armed, self.post_arm_reads = False, 0
        class Status:
            def read(_, o):
                if not self.armed: return self.cap[o]
                if o == 4:
                    self.post_arm_reads += 1
                    value = self.cap[4]
                    if value & 1: value |= 8  # bit3 "had error" latches once events happened (board record).
                    if self.post_arm_reads == 1 or self.mode == 'copy_pending':
                        value |= 4  # arm-transient pending, read-visible at most once.
                    return value
                if o in (0x10, 0x1c): return self.cap[o] + (1 if self.post_arm_reads else 0) + self.street
                return self.cap[o]
        self.status = Status()
    def read(self, o):
        if o == SR and self.reg[CR] & 1 and self.reg.get(VSIZE):
            self.polls += 1
            if self.mode == 'warm_sticky' and self.polls in (1, 2): self.reg[SR] |= HALT_STICKY
            if self.mode == 'double_transient' and self.polls >= 6: self.street = 1
            if self.mode == 'dma_error' and self.polls >= 6: self.reg[SR] |= 0x10
            if self.mode == 'dma_error' and self.polls < 6: pass  # warm-up clears it, then it returns.
            if self.mode == 'lock' and self.polls >= 6: self.cap[4] = 0
            if self.mode == 'descriptor' and self.polls >= 6: self.reg[ADDRESS] += 64
            if self.mode == 'pending' and self.polls >= 6: self.cap[0x1c] += 1
            if self.mode not in ('timeout', 'unsafe'):
                if self.mode != 'no_irq': self.reg[SR] |= 0x1000  # May precede slot change.
                if self.polls % 3 == 0:
                    current = (self.reg[PARK] >> 24) & 0x1F
                    self.buffers[current][:] = 37 if current == 0 else 99
                    target = (self.reg[PARK] >> 8) & 0x1F
                    if self.mode == 'wrong_slot': target = 2
                    self.reg[PARK] = (self.reg[PARK] & ~(0x1F << 24)) | (target << 24)
        value = self.reg.get(o, 0)
        return value | HALT_STICKY if o == SR and not self.reg[CR] & 1 else value
    def write(self, o, value):
        self.events.append((o, value))
        if o == SR: self.reg[SR] &= ~value
        elif o == PARK: self.reg[PARK] = (self.reg[PARK] & ~0x1F00) | (value & 0x1F00)
        elif o == CR and self.mode == 'unsafe' and self.reg.get(VSIZE): return
        elif o == CR and value == 4: self.reg.update({CR: 0, SR: 1, VSIZE: 0})
        elif o == CR:
            self.reg[CR] = value
            self.reg[SR] = 0 if value & 1 else 1
        else:
            self.reg[o] = value
            if o == VSIZE and self.reg[CR] & 1: self.armed = True
    def allocate(self, shape, dtype):
        b = Buffer(0x10000000+len(self.buffers)*0x300000, self)
        self.buffers.append(b)
        return b
    def sleep(self, seconds): self.t += seconds
    def owner(self):
        return ParkFrameCapture(self, self.status, self.allocate, lambda: self.generation,
                                .02, lambda: self.t, self.sleep)


class Tests(unittest.TestCase):
    def test_persistent_halt_errors_and_slow_copy(self):
        for mode in ('ok', 'warm_sticky'):
            r = Rig(mode); c = r.owner(); frame = c.capture()
            self.assertTrue(np.all(frame == 37))
            self.assertTrue(c.evidence['protected_after']['cr'] & 1)
            self.assertFalse(c.evidence['protected_after']['sr'] & 1)
            self.assertEqual([b.frees for b in r.buffers], [1]*4)
            self.assertLess(r.events.index('invalidate'), r.events.index((CR, PARK_RUN & ~1)))
            if mode == 'warm_sticky':
                clears = [e for e in r.events if e == (SR, W1C_PARK)]
                self.assertEqual(len(clears), 2, r.events)  # latched sticky needed two W1Cs.
            r.buffers[0][:] = 0
            self.assertTrue(np.all(frame == 37))
            c.close(); self.assertEqual([b.frees for b in r.buffers], [1]*4)
    def test_start_transient_absorbed_once_at_grant(self):
        r = Rig(); c = r.owner(); frame = c.capture()
        self.assertTrue(np.all(frame == 37))
        grant = c.evidence['warmup_1']
        self.assertEqual(grant['cap']['0x10'], 1)   # the arm transient became the new baseline.
        self.assertEqual(r.post_arm_reads > 1, True)
        self.assertFalse(c.evidence['protected_after']['cap']['0x4'] & 4)
    def test_second_event_and_pending_refuse_copy(self):
        for mode in ('double_transient', 'copy_pending'):
            with self.subTest(mode=mode):
                r = Rig(mode); c = r.owner()
                with self.assertRaises(CaptureError): c.capture()
                self.assertNotIn('invalidate', r.events)
                self.assertEqual([b.frees for b in r.buffers], [1]*4)
    def test_active_errors_never_masked(self):
        for mode in ('timeout', 'no_irq', 'dma_error', 'lock', 'descriptor', 'wrong_slot', 'copy_error', 'copy_sticky'):
            with self.subTest(mode=mode):
                r = Rig(mode); c = r.owner()
                with self.assertRaises(CaptureError): c.capture()
                self.assertEqual([b.frees for b in r.buffers], [1]*4)
                if not mode.startswith('copy_'): self.assertNotIn('invalidate', r.events)
    def test_unknown_owner_quarantines(self):
        for mode in ('unsafe', 'copy_generation'):
            r = Rig(mode); c = r.owner()
            with self.assertRaises(CaptureError): c.capture()
            self.assertIn(c, QUARANTINE)
            self.assertEqual([b.frees for b in r.buffers], [0]*4)
            r.mode='ok'; c.token=r.generation; c.close(); QUARANTINE.remove(c)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): sys.exit(1)
    print('PASS: park candidate captures arm-transient absorption, latched epoch health,'
          ' repeat W1C warmup, active faults and ownership')
