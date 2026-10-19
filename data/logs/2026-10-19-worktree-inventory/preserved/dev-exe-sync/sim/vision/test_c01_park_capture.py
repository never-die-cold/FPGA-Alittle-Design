"""Continuous-park ownership model; repository-only, never imports PYNQ."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/pynq_host'))
from c01_capture import CR, SR, PARK, VSIZE, ADDRESS, SHAPE, CaptureError, QUARANTINE
from c01_park_capture import ParkFrameCapture, PARK_RUN, HALT_STICKY


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
        self.cap.update({0: 0x43415031, 4: 1, 0x14: 1280, 0x18: 720})
        class Status:
            def read(_, o): return self.cap[o]
        self.status = Status()
    def read(self, o):
        if o == SR and self.reg[CR] & 1 and self.reg.get(VSIZE):
            self.polls += 1
            if self.mode == 'warm_sticky' and self.polls == 1: self.reg[SR] |= HALT_STICKY
            if self.mode == 'dma_error': self.reg[SR] |= 0x10
            if self.mode == 'lock': self.cap[4] = 0
            if self.mode == 'descriptor': self.reg[ADDRESS] += 64
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
        else: self.reg[o] = value
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
            r.buffers[0][:] = 0
            self.assertTrue(np.all(frame == 37))
            c.close(); self.assertEqual([b.frees for b in r.buffers], [1]*4)
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
    print('PASS: park candidate halted sticky errors, slow copy, active faults, ownership and cleanup')
