"""W05 live service on the real park chain: ParkCaptures backend + NumPy engine.

Backend: every round acquires the board capture lock, ensures the candidate
overlay (skips download when already loaded), settles on a real frame tick,
runs one protected slot-0 copy through the reviewed ParkFrameCapture bytes,
writes capture.png into the round dir, and restores the original vision with
the bounded busy-aware smoke loop so the user's display recovers between
rounds. prototype stays True until formal N03 acceptance (honest C04 §3.2).
Engine: golden locate (default parameters) -> crop_resize 64x64 -> folded
FP32 NumPy CNN (no torch on the board) -> inspection_rules-shaped judge with
the caller's order/min_score. HTTP surface is the unmodified
vision_live_service.make_server (same /v1 endpoints as EXE expects).
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

SITE = '/home/xilinx/vision_m2'
TRIAL = Path(SITE) / 'c01-8b702ebb0b284fa3a408491e13e644e3'
sys.path.insert(0, SITE)
DRIVER_SHA = '1f11aefdc11805387b0c345583828fd733e5e38b0b0e043b0510808f648e8430'
PARK_SHA = '953dec241be0f4c76d254cdca6efc4da2f334b978338eded49c694dd2f1001b5'
BIT_SHA = '86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f'
HWH_SHA = 'eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c'
CLASSES = ('bolt', 'nut', 'washer')


def _restore_original():
    import m2_onboard
    m2_onboard.cmd_load()
    deadline = time.monotonic() + 40.0
    last = None
    while time.monotonic() < deadline:
        try:
            m2_onboard.cmd_smoke()
            return
        except SystemExit:
            last = 'SystemExit'
        except RuntimeError as exc:
            last = repr(exc)
            if 'busy' not in last:
                raise
        time.sleep(1.0)
    raise RuntimeError('restore smoke timeout: ' + str(last))


class ParkCaptures:
    backend = 'PARK'
    prototype = True

    def __init__(self):
        import fcntl
        self.fcntl = fcntl
        self.seq = 0
        self.lock_path = Path(SITE) / 'c01-capture.lock'
        sys.path.insert(0, str(TRIAL))
        from c01_capture import QUARANTINE  # noqa: F401  import parity with diag entries
        self._capture_cls = None

    def _chain(self, round_dir):
        import cv2
        from pynq import MMIO, PL, Overlay, allocate
        from c01_status_onboard import verify, load_candidate
        from c01_park_capture import ParkFrameCapture
        bit = TRIAL / 'capture.bit'
        if not PL.bitfile_name or 'capture' not in str(PL.bitfile_name):
            verify(bit, BIT_SHA)
            verify(bit.with_suffix('.hwh'), HWH_SHA)
            load_candidate(bit, Overlay)
        if 'capture' not in str(PL.bitfile_name):
            raise RuntimeError('candidate overlay is not loaded')
        status, dma = MMIO(0x42000000, 65536), MMIO(0x43000000, 65536)
        deadline = time.monotonic() + 30.0
        while True:
            tick_a = status.read(8)
            time.sleep(1.0)
            if status.read(8) > tick_a and status.read(4) & 1:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('video settle timeout on candidate')
        def identity():
            return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                    PL.bitfile_name, str(PL.timestamp))
        owner = ParkFrameCapture(dma, status, allocate, identity)
        try:
            frame = owner.capture()
        finally:
            if owner.may_write or owner in getattr(ParkFrameCapture, 'QUARANTINE', ()):
                raise RuntimeError('unsafe stop: buffers held; physical reset required')
        png = round_dir / 'capture.png'
        if not cv2.imwrite(str(png), frame):
            raise RuntimeError('capture.png write failed')
        return png

    def capture(self, round_dir):
        import asyncio
        import threading
        import pynq  # noqa: F401  pynq internals need an event loop inside request threads.
        asyncio.set_event_loop(asyncio.new_event_loop())
        from pynq import allocate, PL
        lock = self.lock_path.open('a')
        self.fcntl.flock(lock, self.fcntl.LOCK_EX | self.fcntl.LOCK_NB)
        try:
            png = self._chain(round_dir)
        finally:
            self.fcntl.flock(lock, self.fcntl.LOCK_UN)
            lock.close()
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        _restore_original()
        return png


def numpy_engine(package_path, order, min_score):
    sys.path.insert(0, str(TRIAL))
    from reference import locate, crop_resize
    package = np.load(package_path)
    layers = [{'kind': 'conv_relu',
               'weight': package[f'conv{n}_weight'], 'bias': package[f'conv{n}_bias'],
               'stride': [int(v) for v in package[f'conv{n}_stride']],
               'padding': [int(v) for v in package[f'conv{n}_padding']]} for n in range(1, 5)]
    layers.append({'kind': 'global_average'})
    layers.append({'kind': 'linear', 'weight': package['logits_weight'],
                   'bias': package['logits_bias']})

    def run(capture_path, round_dir, request_id):
        import cv2
        from pynq import MMIO
        print('ENGINE: start ' + request_id, flush=True)
        frame = cv2.imread(str(capture_path), cv2.IMREAD_COLOR)
        if frame is None or frame.shape != (720, 1280, 3):
            raise RuntimeError('capture.png unreadable or wrong geometry')
        config_id = int(MMIO(0x40000000, 128).read(48))
        print('ENGINE: capture read, config_id=%d' % config_id, flush=True)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        print('ENGINE: gray done, locating (pure-python BFS, ~12 s)', flush=True)
        located = locate(gray.tolist(), int(time.time()) & 0xFFFF, config_id)
        print('ENGINE: located %d targets' % len(located['targets']), flush=True)
        targets = []
        for target in located['targets']:
            crop = np.asarray(crop_resize(gray.tolist(), target['bbox'], 64, 64), dtype=np.uint8)
            value = crop.astype(np.float32)[None] / np.float32(255)
            for layer in layers:
                if layer['kind'] == 'conv_relu':
                    padded = np.pad(value, ((0, 0), (layer['padding'][0],) * 2, (layer['padding'][1],) * 2))
                    windows = np.lib.stride_tricks.sliding_window_view(
                        padded, (layer['weight'].shape[2], layer['weight'].shape[3]), axis=(1, 2))
                    windows = windows[:, ::layer['stride'][0], ::layer['stride'][1]]
                    value = np.maximum(np.einsum('cyxij,ocij->oyx', windows,
                                                 layer['weight'], optimize=True)
                                       + layer['bias'][:, None, None], 0)
                elif layer['kind'] == 'global_average':
                    pooled = value.mean(axis=(1, 2))
                else:
                    logits = layer['weight'] @ pooled + layer['bias']
            scores = np.exp(logits - float(logits.max()))
            scores = scores / scores.sum()
            targets.append({'target_id': target['target_id'], 'bbox': target['bbox'],
                            'class': CLASSES[int(scores.argmax())], 'score': float(scores.max()),
                            'touches_border': target['touches_border']})
        print('ENGINE: classified %d targets' % len(targets), flush=True)
        actual = dict.fromkeys(CLASSES, 0)
        reasons = set()
        if len(targets) > 16:
            reasons.add('target_limit')  # C04 §2.2: list first 16, counts recomputed downstream.
            targets = targets[:16]
        for target in targets:
            if target['score'] < min_score:
                reasons.add('low_score')
            if target['touches_border']:
                reasons.add('touches_border')
            actual[target['class']] += 1
        if 'target_limit' in reasons:
            actual = None  # complete_decision recomputes from the listed targets only.
        delta = {name: (actual[name] - order[name] if actual is not None else None)
                 for name in CLASSES}
        if actual is None:
            missing = extra = None
        else:
            missing = {k: max(-v, 0) for k, v in delta.items()}
            extra = {k: max(v, 0) for k, v in delta.items()}
        decision = {'verdict': 'RECHECK' if reasons else
                    ('CHECK_FAIL' if any(delta.values()) else 'CHECK_PASS'),
                    'expected': dict(order), 'actual': actual, 'delta': delta,
                    'missing': missing, 'extra': extra, 'reasons': sorted(reasons)}
        packet_targets = [{'target_id': t['target_id'], 'bbox': t['bbox'],
                           'class': t['class'], 'score': t['score']} for t in targets]
        return {'status': decision['verdict'], 'targets': packet_targets, 'decision': decision,
                'width': located['width'], 'height': located['height']}
    return run


def main():
    import faulthandler
    import m2_onboard  # noqa: F401  verifies the original-vision dir is importable
    faulthandler.dump_traceback_later(150, repeat=True)  # periodic thread stacks to the log.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--root', required=True)
    parser.add_argument('--order', type=int, nargs=3, required=True, metavar=('BOLT', 'NUT', 'WASHER'))
    parser.add_argument('--min-score', type=float, required=True)
    args = parser.parse_args()
    order = dict(zip(CLASSES, args.order))
    sys.path.insert(0, str(TRIAL))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from vision_live_service import make_server
    captures = ParkCaptures()
    engine = numpy_engine(TRIAL / 'cnn_board_package.npz', order, args.min_score)
    print('LIVE SERVICE (backend=%s, prototype=%s): http://%s:%d/v1/status' % (
        captures.backend, captures.prototype, args.host, args.port), flush=True)
    make_server(host=args.host, port=args.port, root=args.root,
                captures=captures, engine=engine, order=order).serve_forever()


if __name__ == '__main__':
    main()
