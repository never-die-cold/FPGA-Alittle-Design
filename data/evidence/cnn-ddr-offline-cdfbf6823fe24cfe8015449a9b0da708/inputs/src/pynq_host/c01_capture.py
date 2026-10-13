"""C01 S2MM single-frame owner. PG020 frame-count auto-stop, park slot 0.

Only an independent, cache-invalidated complete copy can leave this owner.
Caller must hold exclusive hardware ownership and keep identity stable.
An unconfirmed stop quarantines native buffers; caller MUST stay alive.
"""
import time
import numpy as np

CR, SR, PARK = 0x30, 0x34, 0x28
VSIZE, HSIZE, STRIDE, ADDRESS = 0xA0, 0xA4, 0xA8, 0xAC
ERRORS, IRQ, RUN = 0xC9F0, 0x1000, 0x11011
SHAPE = (720, 1280, 3)
FRAME_BYTES = 2764800
QUARANTINE = []  # Strong references prevent finalizers freeing DMA-owned memory.


class CaptureError(RuntimeError):
    pass


class SingleFrameCapture:
    def __init__(self, dma, status, allocate, identity, timeout=3.0,
                 clock=time.monotonic, sleep=time.sleep):
        self.dma, self.status, self.allocate = dma, status, allocate
        self.identity, self.timeout, self.clock, self.sleep = identity, timeout, clock, sleep
        self.buffers = []
        self.may_write = False
        self.closed = False
        self.started = False
        self.token = None
        self.cap_before = None
        self.evidence = {}

    def _wait(self, predicate, reason):
        end = self.clock() + self.timeout
        while True:
            if predicate():
                return
            if self.clock() >= end:
                raise CaptureError(reason)
            self.sleep(0.001)

    def _cap(self):
        return {hex(o): int(self.status.read(o)) for o in range(0, 0x24, 4)}

    def _check_source(self):
        cap = self._cap()
        if self.identity() != self.token:
            raise CaptureError("overlay/boot generation changed")
        if (cap['0x0'], cap['0x14'], cap['0x18']) != (0x43415031, 1280, 720):
            raise CaptureError("CAP1 identity/geometry changed")
        if not cap['0x4'] & 1 or cap['0x4'] & 0xC:
            raise CaptureError("capture lock/fault invalid")
        if self.cap_before is not None:
            for o in ('0x10', '0x1c', '0x20'):
                if cap[o] != self.cap_before[o]:
                    raise CaptureError("capture source error event: " + o)
        return cap

    def _check_descriptors(self):
        expected = {HSIZE: 3840, STRIDE: 3840, VSIZE: 720}
        expected.update({ADDRESS + i*4: int(b.physical_address) for i, b in enumerate(self.buffers)})
        if any(self.dma.read(o) != value for o, value in expected.items()):
            raise CaptureError("DMA descriptor changed")
        if self.dma.read(PARK) & 0x1F00:
            raise CaptureError("DMA park reference changed")

    def _protected(self):
        self._check_source()
        cr, sr, park = self.dma.read(CR), self.dma.read(SR), self.dma.read(PARK)
        if sr & ERRORS:
            raise CaptureError("DMA error: 0x%08x" % sr)
        if cr & (0xFF0000 | 0x101F) != RUN & (0xFF0000 | 0x101F) & ~1:
            raise CaptureError("single-frame control changed or still running")
        if not (sr & 1 and sr & IRQ) or (park >> 24) & 0x1F:
            raise CaptureError("complete halted park slot not confirmed")
        self._check_descriptors()
        return {"cr": cr, "sr": sr, "park": park, "cap": self._cap()}

    def capture(self):
        if self.started or self.closed:
            raise CaptureError("owner is single-use")
        self.started = True
        self.token = self.identity()
        self.cap_before = self._check_source()
        self.evidence['before'] = {"cap": self.cap_before, "cr": self.dma.read(CR), "sr": self.dma.read(SR)}
        # Refuse an external active owner before allocating or mutating anything.
        if self.dma.read(CR) & 1 or not self.dma.read(SR) & 1:
            raise CaptureError("DMA already active; exclusive ownership refused")
        t0 = self.clock()
        primary = None
        try:
            for _ in range(4):
                b = self.allocate(shape=SHAPE, dtype=np.uint8)
                self.buffers.append(b)
                address = int(b.physical_address)
                if b.shape != SHAPE or b.dtype != np.uint8 or b.strides != (3840, 3, 1) or b.nbytes != FRAME_BYTES:
                    raise CaptureError("DMA allocation geometry invalid")
                if address % 64 or address < 0 or address + FRAME_BYTES > 2**32:
                    raise CaptureError("DMA allocation address invalid")
                for other in self.buffers[:-1]:
                    a = int(other.physical_address)
                    if address < a + FRAME_BYTES and a < address + FRAME_BYTES:
                        raise CaptureError("DMA allocations overlap")
            self.dma.write(CR, 4)
            self._wait(lambda: not self.dma.read(CR) & 4 and self.dma.read(SR) & 1, "DMA reset timeout")
            self.dma.write(PARK, self.dma.read(PARK) & ~0x1F00)
            for i, b in enumerate(self.buffers):
                self.dma.write(ADDRESS+i*4, int(b.physical_address))
            self.dma.write(STRIDE, 3840)
            self.dma.write(HSIZE, 3840)
            # Stream can be accepted/discarded while halted. Configure nonzero
            # geometry before checking/clearing idle-time sticky frame errors.
            self.dma.write(VSIZE, 720)
            self.evidence['configured_idle'] = {"cr": self.dma.read(CR), "sr": self.dma.read(SR)}
            self.dma.write(SR, ERRORS | IRQ | 0x2000)
            self.evidence['cleared_idle'] = {"cr": self.dma.read(CR), "sr": self.dma.read(SR)}
            if self.dma.read(SR) & (ERRORS | IRQ) or self.dma.read(CR) & 1:
                raise CaptureError("DMA configured idle reset/clear not clean")
            self._check_source()
            self.may_write = True  # Set BEFORE run write: failed MMIO can still have taken effect.
            self.dma.write(CR, RUN)
            if self.dma.read(CR) & (0xFF0000 | 0x101F) != RUN:
                raise CaptureError("single-frame start control readback mismatch")
            self.dma.write(VSIZE, 720)  # Last register starts the configured transfer.
            self.evidence['addresses'] = [int(b.physical_address) for b in self.buffers]
            def completed():
                self._check_source()
                sr, cr = self.dma.read(SR), self.dma.read(CR)
                if sr & ERRORS:
                    raise CaptureError("DMA error while waiting: 0x%08x" % sr)
                return bool(sr & IRQ and sr & 1 and not cr & 1)
            self._wait(completed, "single-frame completion timeout")
            self.evidence['protected_before'] = self._protected()
            t1 = self.clock()
            self.buffers[0].invalidate()
            t2 = self.clock()
            frame = np.array(self.buffers[0], dtype=np.uint8, copy=True, order='C')
            t3 = self.clock()
            self.evidence['protected_after'] = self._protected()
            self.may_write = False
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

    def close(self):
        if self.closed:
            return
        if self.may_write:
            try:
                if self.identity() != self.token:
                    raise CaptureError("generation changed; cannot stop unknown DMA owner")
                self.dma.write(CR, self.dma.read(CR) & ~1)
                try:
                    self._wait(lambda: self.dma.read(SR) & 1 and not self.dma.read(CR) & 1, "DMA stop timeout")
                except CaptureError:
                    self.dma.write(CR, 4)
                    self._wait(lambda: not self.dma.read(CR) & 5 and self.dma.read(SR) & 1, "DMA recovery reset timeout")
                self.may_write = False
            except BaseException as exc:
                self.evidence['cleanup_error'] = repr(exc)
                if self not in QUARANTINE:
                    QUARANTINE.append(self)
                # Preserve the primary failure; never free or reload the overlay here.
                raise CaptureError("DMA stop unconfirmed; buffers quarantined") from exc
        failures = []
        for b in self.buffers:
            try:
                b.freebuffer()
            except BaseException as exc:
                failures.append(repr(exc))
        # Do not retry native frees that may have taken effect before raising.
        self.closed = True
        if failures:
            self.evidence['cleanup_error'] = failures
            raise CaptureError("native buffer release failed: " + repr(failures))
        self.evidence['cleanup'] = "halt confirmed; %d owned buffers freed once" % len(self.buffers)
