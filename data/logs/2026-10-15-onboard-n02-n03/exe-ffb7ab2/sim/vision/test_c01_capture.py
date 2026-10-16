"""Fault injection for real single-frame driver; no hardware imports."""
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/pynq_host'))
from c01_capture import (SingleFrameCapture, CaptureError, QUARANTINE, CR, SR, PARK,
                         VSIZE, ADDRESS, RUN, SHAPE)


class Buffer(np.ndarray):
    def __new__(cls, address, events):
        obj = np.zeros(SHAPE, np.uint8).view(cls)
        obj.physical_address, obj.events, obj.frees = address, events, 0
        return obj
    def invalidate(self):
        self.events.append('invalidate')
        if hasattr(self, 'on_invalidate'): self.on_invalidate()
        self[:] = 37  # Simulates stale CPU cache until invalidate.
    def freebuffer(self):
        self.frees += 1
        self.events.append('free')
        if getattr(self, 'fail_free', False): raise RuntimeError('injected native free failure')


class Rig:
    def __init__(self, mode='ok'):
        self.mode, self.t, self.generation = mode, 0., 'A'
        self.events, self.buffers = [], []
        self.reg = {CR: 0, SR: 1 | 0x1000 | 0x40, PARK: 0}
        self.cap = {o: 0 for o in range(0, 0x24, 4)}
        self.cap.update({0: 0x43415031, 4: 1, 0x14: 1280, 0x18: 720})
        self.started, self.polls = False, 0
        class Status:
            def read(_, o):
                return self.cap[o]
        self.status = Status()
    def read(self, o):
        if o == SR and self.started and self.reg[CR] & 1:
            self.polls += 1
            if self.mode == 'dma_error': self.reg[SR] |= 0x20
            if self.mode == 'lock': self.cap[4] = 0
            if self.mode == 'generation': self.generation = 'B'
            if self.mode == 'descriptor': self.reg[ADDRESS] += 64
            if self.mode not in ('timeout', 'unsafe', 'dma_error', 'lock', 'generation'):
                self.reg[SR] |= 0x1000  # IRQ first, not yet halted.
                if self.polls >= 4:
                    self.reg[CR] &= ~1
                    self.reg[SR] |= 1
                    if self.mode == 'no_irq': self.reg[SR] &= ~0x1000
                    if self.mode == 'wrong_slot': self.reg[PARK] |= 1 << 24
        return self.reg.get(o, 0)
    def write(self, o, value):
        self.events.append(('write', o, value))
        if o == SR:
            self.reg[o] &= ~value
        elif o == CR and value == 4:
            if self.started and self.mode == 'unsafe': return
            self.reg[CR], self.reg[SR] = 0, 1
        elif o == CR and self.started and self.mode == 'unsafe':
            return
        else:
            self.reg[o] = value
            if o == VSIZE and self.reg[CR] & 1:
                self.started = True
                self.reg[SR] = 0
            if o == CR and not value & 1:
                self.reg[SR] |= 1
    def allocate(self, shape, dtype):
        if self.mode == 'alloc_failure' and len(self.buffers) == 2:
            raise MemoryError('injected')
        b = Buffer(0x10000000 + len(self.buffers)*0x300000, self.events)
        if self.mode == 'overlap': b.physical_address = 0x10000000
        if self.mode == 'unaligned': b.physical_address += 1
        self.buffers.append(b)
        return b
    def sleep(self, seconds): self.t += seconds
    def owner(self):
        return SingleFrameCapture(self, self.status, self.allocate,
                                  lambda: self.generation, .02, lambda: self.t, self.sleep)


class Tests(unittest.TestCase):
    def test_complete_copy_and_release(self):
        r = Rig(); c = r.owner(); frame = c.capture()
        self.assertEqual(frame.shape, SHAPE)
        self.assertTrue(np.all(frame == 37)); self.assertGreaterEqual(r.polls, 4)
        r.buffers[0][:] = 99
        self.assertTrue(np.all(frame == 37))
        self.assertLess(r.events.index('invalidate'), r.events.index('free'))
        c.close(); self.assertEqual([b.frees for b in r.buffers], [1]*4)
        self.assertEqual(c.evidence['protected_after']['sr'] & 0x1001, 0x1001)
        self.assertEqual(c.evidence['identity'], 'A')
        self.assertEqual(len(c.evidence['buffers']), 4)
        self.assertEqual(c.evidence['buffers'][0]['bytes'], 2764800)
        self.assertIsNone(c.evidence['buffers'][0]['coherent'])
    def test_failures_never_copy(self):
        for mode in ('timeout', 'no_irq', 'dma_error', 'lock', 'descriptor',
                     'wrong_slot', 'overlap', 'unaligned', 'alloc_failure'):
            with self.subTest(mode=mode):
                r = Rig(mode); c = r.owner()
                with self.assertRaises((CaptureError, MemoryError)): c.capture()
                self.assertNotIn('invalidate', r.events)
                self.assertTrue(all(b.frees == 1 for b in r.buffers))
    def test_refuse_external_owner(self):
        r = Rig(); r.reg[CR] = RUN; r.reg[SR] = 0
        with self.assertRaises(CaptureError): r.owner().capture()
        self.assertEqual(r.events, []); self.assertEqual(r.buffers, [])
    def test_configured_idle_precedes_clean_and_run(self):
        r = Rig(); c = r.owner(); c.capture()
        writes = [event for event in r.events if isinstance(event, tuple)]
        reset = writes.index(('write', CR, 4))
        geometry = writes.index(('write', VSIZE, 720))
        clear = next(i for i,e in enumerate(writes) if e[1] == SR)
        run = writes.index(('write', CR, RUN))
        self.assertLess(reset, geometry); self.assertLess(geometry, clear); self.assertLess(clear, run)
    def test_source_changes_during_copy_not_published(self):
        for kind in ('epoch', 'invalidate_failure'):
            r = Rig(); original = r.allocate
            def allocation(**kw):
                b = original(**kw)
                if len(r.buffers) == 1:
                    def changed():
                        if kind == 'epoch': r.cap[0x10] += 1
                        else: raise RuntimeError('invalidate failed')
                    b.on_invalidate = changed
                return b
            r.allocate = allocation; c = r.owner()
            with self.assertRaises((CaptureError, RuntimeError)): c.capture()
            self.assertTrue(c.closed); self.assertFalse(c.may_write)
            self.assertEqual([b.frees for b in r.buffers], [1]*4)
    def test_release_failure_attempts_remaining_buffers_once(self):
        r = Rig(); original = r.allocate
        def allocation(**kw):
            b = original(**kw)
            b.fail_free = len(r.buffers) == 1
            return b
        r.allocate = allocation; c = r.owner()
        with self.assertRaises(CaptureError): c.capture()
        c.close()
        self.assertEqual([b.frees for b in r.buffers], [1]*4)
        self.assertIn('cleanup_error', c.evidence)
    def test_unsafe_stop_keeps_buffers(self):
        for mode in ('unsafe', 'generation'):
            r = Rig(mode); c = r.owner()
            with self.assertRaises(CaptureError): c.capture()
            self.assertIn(c, QUARANTINE)
            self.assertTrue(c.may_write); self.assertFalse(c.closed)
            self.assertEqual([b.frees for b in r.buffers], [0]*4)
            self.assertIn('cleanup_error', c.evidence)
            self.assertIn('main_error', c.evidence)
            # Test rig is now independently confirmed reset; release only in the fake.
            c.token = r.generation; r.mode = 'ok'; c.close(); QUARANTINE.remove(c)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): sys.exit(1)
    print('PASS: C01 single-frame ownership, cache, faults and quarantine')
