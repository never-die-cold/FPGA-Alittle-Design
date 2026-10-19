"""Opt-in C01 park-switch candidate; hardware/N03 acceptance is still pending.

Warm up in slot 1, visit slot 0, park back in slot 1, copy slot 0 while running.
Halt-time 0x4810 never authorizes a frame and is never masked in the copy window.
The caller must provide exclusive ownership, as for SingleFrameCapture.
"""
import numpy as np
from c01_capture import (SingleFrameCapture, CaptureError, CR, SR, PARK, VSIZE,
                         HSIZE, STRIDE, ADDRESS, ERRORS, IRQ, RUN, SHAPE, FRAME_BYTES)

PARK_RUN = RUN & ~0x10  # FrameCntEn=0; Circular_Park=0; threshold/IRQ remain enabled.
HALT_STICKY = 0x4810
CONTROL_MASK = 0xFF0000 | 0x101F


class ParkFrameCapture(SingleFrameCapture):
    def _park(self, slot):
        self.dma.write(SR, IRQ | 0x2000)
        self.park_reference = slot
        self.dma.write(PARK, (self.dma.read(PARK) & ~0x1F00) | (slot << 8))

    def _running(self, warmup=False):
        self._check_source()
        cr, sr, park = self.dma.read(CR), self.dma.read(SR), self.dma.read(PARK)
        if cr & CONTROL_MASK != PARK_RUN or sr & 1:
            raise CaptureError("park capture channel halted or control changed")
        errors = sr & ERRORS
        if errors:
            if warmup and errors == HALT_STICKY:
                self.dma.write(SR, HALT_STICKY | IRQ | 0x2000)
                return None
            raise CaptureError("park capture DMA error: 0x%08x" % sr)
        if (park >> 8) & 0x1F != self.park_reference or (park >> 24) & 0x1F > 1:
            raise CaptureError("park capture slot/reference changed")
        expected = {HSIZE: 3840, STRIDE: 3840, VSIZE: 720}
        expected.update({ADDRESS+i*4: int(b.physical_address) for i,b in enumerate(self.buffers)})
        if any(self.dma.read(o) != value for o,value in expected.items()):
            raise CaptureError("park capture descriptor changed")
        return {"cr": cr, "sr": sr, "park": park, "cap": self._cap()}

    def _wait_park(self, slot, warmup=False):
        def completed():
            evidence = self._running(warmup)
            if evidence is None:
                return False
            if (evidence['park'] >> 24) & 0x1F == slot and evidence['sr'] & IRQ:
                self.evidence[('warmup_' if warmup else 'park_') + str(slot)] = evidence
                return True
            return False
        self._wait(completed, "park capture frame/slot timeout")

    def _protected(self):
        evidence = self._running()
        if self.park_reference != 1 or (evidence['park'] >> 24) & 0x1F != 1:
            raise CaptureError("slot 0 is not protected by park slot 1")
        return evidence

    def capture(self):
        if self.started or self.closed:
            raise CaptureError("owner is single-use")
        self.started = True
        self.token = self.identity()
        self.evidence.update(identity=self.token, mode="PARK_CANDIDATE_NOT_BOARD_VERIFIED")
        self.cap_before = self._check_source()
        if self.dma.read(CR) & 1 or not self.dma.read(SR) & 1:
            raise CaptureError("DMA already active; exclusive ownership refused")
        primary = None
        t0 = self.clock()
        try:
            for _ in range(4):
                b = self.allocate(shape=SHAPE, dtype=np.uint8)
                self.buffers.append(b)
                address = int(b.physical_address)
                if b.shape != SHAPE or b.dtype != np.uint8 or b.strides != (3840, 3, 1) or b.nbytes != FRAME_BYTES:
                    raise CaptureError("DMA allocation geometry invalid")
                if address % 64 or address < 0 or address + FRAME_BYTES > 2**32:
                    raise CaptureError("DMA allocation address invalid")
                if any(address < int(o.physical_address)+FRAME_BYTES and int(o.physical_address) < address+FRAME_BYTES
                       for o in self.buffers[:-1]):
                    raise CaptureError("DMA allocations overlap")
            self.evidence['buffers'] = [dict(address=int(b.physical_address), shape=list(b.shape),
                dtype=str(b.dtype), strides=list(b.strides), bytes=int(b.nbytes),
                coherent=getattr(b, 'coherent', None)) for b in self.buffers]
            self.dma.write(CR, 4)
            self._wait(lambda: not self.dma.read(CR) & 4 and self.dma.read(SR) & 1, "DMA reset timeout")
            self._park(1)
            for i,b in enumerate(self.buffers):
                self.dma.write(ADDRESS+i*4, int(b.physical_address))
            self.dma.write(STRIDE, 3840)
            self.dma.write(HSIZE, 3840)
            self.may_write = True
            self.dma.write(CR, PARK_RUN)
            self.dma.write(VSIZE, 720)
            self.dma.write(SR, ERRORS | IRQ | 0x2000)
            self._wait_park(1, warmup=True)
            self._park(0)
            self._wait_park(0)
            self._park(1)
            self._wait_park(1)
            self.evidence['protected_before'] = self._protected()
            t1 = self.clock()
            self.buffers[0].invalidate()
            t2 = self.clock()
            frame = np.array(self.buffers[0], dtype=np.uint8, copy=True, order='C')
            t3 = self.clock()
            self.evidence['protected_after'] = self._protected()
            if frame.shape != SHAPE or frame.strides != (3840, 3, 1) or frame.nbytes != FRAME_BYTES:
                raise CaptureError("complete independent copy geometry invalid")
            if np.shares_memory(frame, self.buffers[0]):
                raise CaptureError("copy still aliases DMA")
            self.evidence['seconds'] = {"capture": t1-t0, "invalidate": t2-t1, "copy": t3-t2}
            return frame
        except BaseException as exc:
            primary = exc
            self.evidence['main_error'] = repr(exc)
            raise
        finally:
            try:
                self.close()
            except BaseException:
                if primary is None:
                    raise
