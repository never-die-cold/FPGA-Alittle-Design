"""Real chain run: camera frame -> locate -> 64x64 crops -> NumPy CNN -> judge.

NOT formal N03 and an honest LIVE prototype: uses the same reviewed park
driver path, the golden localizer (default parameters), the golden
crop_resize (16.16 lerp identical to the scaler), the folded FP32 weights in
cnn_board_package.npz (checkpoint sha256 pinned to the PC export), and rules
target class/score/border so the decision block follows the v1.2 fields.
Class/score/decision need no torch on the board. A demo work order
(2/2/2, min_score 0.8) is applied and recorded as such; the real order is a
later M3 freeze. Restores the original vision when done, UNSAFE-STOP 语义同入口.
"""
import fcntl
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

SITE = '/home/xilinx/vision_m2'
TRIAL = Path(SITE) / 'c01-8b702ebb0b284fa3a408491e13e644e3'
DRIVER_SHA = '1f11aefdc11805387b0c345583828fd733e5e38b0b0e043b0510808f648e8430'
PARK_SHA = '953dec241be0f4c76d254cdca6efc4da2f334b978338eded49c694dd2f1001b5'
BIT_SHA = '86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f'
HWH_SHA = 'eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c'
CLASSES = ('bolt', 'nut', 'washer')
DEMO_ORDER = {'bolt': 2, 'nut': 2, 'washer': 2}
MIN_SCORE = 0.8


def conv2d_ref(image, weight, bias, stride, padding):
    padded = np.pad(image, ((0, 0), (padding[0], padding[0]), (padding[1], padding[1])))
    windows = np.lib.stride_tricks.sliding_window_view(padded, (weight.shape[2], weight.shape[3]), axis=(1, 2))
    windows = windows[:, ::stride[0], ::stride[1]]
    return np.einsum("cyxij,ocij->oyx", windows, weight, optimize=True) + bias[:, None, None]


def classify(crop, layers):
    value = crop.astype(np.float32)[None] / np.float32(255)
    for layer in layers:
        if layer['kind'] == 'conv_relu':
            value = np.maximum(conv2d_ref(value, layer['weight'], layer['bias'],
                                          layer['stride'], layer['padding']), 0)
        elif layer['kind'] == 'global_average':
            pooled = value.mean(axis=(1, 2))
        elif layer['kind'] == 'linear':
            logits = layer['weight'] @ pooled + layer['bias']
        else:
            raise ValueError('unsupported layer kind')
    scores = np.exp(logits - float(logits.max()))
    scores = scores / scores.sum()
    return CLASSES[int(scores.argmax())], float(scores.max()), [float(s) for s in scores]


def judge_packet(targets):
    actual = dict.fromkeys(CLASSES, 0)
    reasons = set()
    for target in targets:
        label = target.get('class')
        if label in CLASSES:
            actual[label] += 1
        else:
            reasons.add('unknown_class')
        if target['score'] < MIN_SCORE:
            reasons.add('low_score')
        if target['touches_border']:
            reasons.add('touches_border')
    delta = {label: actual[label] - DEMO_ORDER[label] for label in CLASSES}
    verdict = 'RECHECK' if reasons else ('CHECK_FAIL' if any(delta.values()) else 'CHECK_PASS')
    return {'verdict': verdict, 'expected': dict(DEMO_ORDER), 'actual': actual, 'delta': delta,
            'missing': {k: max(-v, 0) for k, v in delta.items()},
            'extra': {k: max(v, 0) for k, v in delta.items()}, 'reasons': sorted(reasons)}


def restore_bounded():
    outcome = {'restore_error': None}
    try:
        __import__('m2_onboard').cmd_load()
        deadline = time.monotonic() + 40.0
        last = None
        while time.monotonic() < deadline:
            try:
                __import__('m2_onboard').cmd_smoke()
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
            outcome['smoke'] = 'TIMEOUT last=' + str(last)
    except BaseException as exc:
        outcome['restore_error'] = repr(exc)
    print('RESTORE: ' + json.dumps(outcome), flush=True)
    return outcome


def main():
    from pynq import MMIO, PL, allocate, Overlay
    import cv2
    sys.path.insert(0, SITE)
    import m2_onboard
    sys.path.insert(0, str(TRIAL))
    from c01_capture import QUARANTINE
    from c01_park_capture import ParkFrameCapture
    from c01_status_onboard import verify, load_candidate
    from reference import locate, crop_resize
    for name, sha in (('c01_capture.py', DRIVER_SHA), ('c01_park_capture.py', PARK_SHA)):
        if hashlib.sha256((TRIAL / name).read_bytes()).hexdigest() != sha:
            raise RuntimeError('trial module is not the reviewed bytes: ' + name)
    bit = TRIAL / 'capture.bit'
    if not PL.bitfile_name or 'capture' not in str(PL.bitfile_name):
        verify(bit, BIT_SHA)
        verify(bit.with_suffix('.hwh'), HWH_SHA)
        load_candidate(bit, Overlay)
    if 'capture' not in str(PL.bitfile_name):
        raise RuntimeError('candidate overlay is not loaded: %r' % PL.bitfile_name)
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
    def identity():
        return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                PL.bitfile_name, str(PL.timestamp))
    boot = identity()[0]
    pipe = MMIO(0x40000000, 65536)
    config_id = int(pipe.read(48))
    package = np.load(TRIAL / 'cnn_board_package.npz')
    layers = [{'name': f'conv{n}', 'kind': 'conv_relu',
               'weight': package[f'conv{n}_weight'], 'bias': package[f'conv{n}_bias'],
               'stride': [int(v) for v in package[f'conv{n}_stride']],
               'padding': [int(v) for v in package[f'conv{n}_padding']]} for n in range(1, 5)]
    layers.append({'kind': 'global_average'})
    layers.append({'kind': 'linear', 'weight': package['logits_weight'],
                   'bias': package['logits_bias']})
    result = {'boot_before': boot, 'park_sha256': PARK_SHA, 'config_id': config_id,
              'checkpoint_sha256': str(package['checkpoint_sha256'].item()),
              'demo_order': DEMO_ORDER, 'min_score': MIN_SCORE,
              'kind': 'C01_PARK_CLASSIFY_JUDGE_LIVE_PROTOTYPE_NOT_FORMAL'}
    owner, primary = None, None
    try:
        owner = ParkFrameCapture(dma, status, allocate, identity)
        frame = owner.capture()
        result['capture'] = owner.evidence
        frame_id = int(owner.evidence['protected_before']['cap']['0x8'])
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        located = locate(gray.tolist(), frame_id, config_id)
        targets = []
        for target in located['targets']:
            crop = np.asarray(crop_resize(gray.tolist(), target['bbox'], 64, 64),
                              dtype=np.uint8)
            label, score, probabilities = classify(crop, layers)
            targets.append({**target, 'class': label, 'score': score,
                            'probabilities': probabilities})
        decision = judge_packet(targets)
        located['targets'] = [{k: t[k] for k in ('target_id', 'frame_id', 'config_id',
                                                 'bbox', 'class', 'score')} for t in targets]
        located['status'] = decision['verdict']
        located['mode'] = 'LIVE'
        located['prototype'] = True
        located['decision'] = decision
        result['packet'] = located
        result['ok'] = True
        print('LIVE-PACKET: ' + json.dumps(located), flush=True)
        print('PASS: full capture/locate/crop/classify/judge chain on real frame', flush=True)
    except BaseException as exc:
        primary = exc
        result['ok'], result['main_error'] = False, repr(exc)
        if owner is not None:
            result['capture'] = owner.evidence
        print('MAIN-FAIL:', repr(exc), flush=True)
    finally:
        if QUARANTINE or (owner is not None and owner.may_write):
            result['unsafe_stop'] = True
            print('UNSAFE-STOP: buffers held; process stays alive; physical board reset required', flush=True)
            while True:
                time.sleep(1)
        result['restore'] = restore_bounded()
        result['boot_after'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        print('RESULT:', json.dumps(result), flush=True)
    if primary is not None:
        raise primary
    if result['boot_after'] != boot:
        raise RuntimeError('board rebooted during capture')
    print('PASS: original vision restored; classify chain complete', flush=True)


if __name__ == '__main__':
    main()
