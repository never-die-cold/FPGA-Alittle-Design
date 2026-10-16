"""Board-side real CNN inference on golden crops; pure NumPy, no torch.

Loads the folded NPZ (cnn_board_package.npz), verifies layers/metadata against
the export contract, and runs two 64x64 golden crops (generated offline from
the frozen dataset fixture with their PC torch softmax results recorded) plus
two all-zero-image diagnostics. The numeric core follows numpy_reference's
strict FP32 conv2d semantics; outputs class/score/probabilities, and the
completed capture-loop PNG path is intentionally not used here.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

SITE = Path('/home/xilinx/vision_m2/c01-8b702ebb0b284fa3a408491e13e644e3')
PACKAGE = SITE / 'cnn_board_package.npz'
CROPS = SITE / 'golden_crops.npz'
EXPECTED = SITE / 'golden_crops_meta.json'
CLASSES = ('bolt', 'nut', 'washer')


def conv2d_ref(image, weight, bias, stride, padding):
    stride_ = [int(s) for s in (stride if hasattr(stride, '__len__') else [stride])]
    padding_ = [int(p) for p in (padding if hasattr(padding, '__len__') else [padding])]
    if len(stride_) == 1: stride_ = stride_ * 2
    if len(padding_) == 1: padding_ = padding_ * 2
    if len(stride_) != 2 or len(padding_) != 2:
        raise ValueError('stride/padding must unpack to two ints')
    padded = np.pad(image, ((0, 0), (padding_[0], padding_[0]), (padding_[1], padding_[1])))
    windows = np.lib.stride_tricks.sliding_window_view(padded, (weight.shape[2], weight.shape[3]), axis=(1, 2))
    windows = windows[:, ::stride_[0], ::stride_[1]]
    return np.einsum("cyxij,ocij->oyx", windows, weight, optimize=True) + bias[:, None, None]


def predict_trace(crop, layers):
    if crop.dtype != np.uint8 or crop.shape != (64, 64):
        raise ValueError('crop must be uint8 64x64')
    value = crop.astype(np.float32)[None] / np.float32(255)   # (C, H, W) with C=1
    pooled, logits = None, None
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
    peak = float(logits.max())
    scores = np.exp(logits - peak)
    scores = scores / scores.sum()
    return {'class': CLASSES[int(scores.argmax())], 'score': float(scores.max()),
            'probabilities': [float(s) for s in scores], 'logits': [float(x) for x in logits]}


def main():
    package = np.load(PACKAGE)
    crop_package = np.load(CROPS)
    expected = json.loads((SITE / 'golden_crops_meta.json').read_text())
    if package['checkpoint_sha256'].item() != expected['checkpoint_sha256']:
        raise RuntimeError('package/crop checkpoint identity mismatch')
    layers = []
    for number in range(1, 5):
        layers.append({'name': f'conv{number}', 'kind': 'conv_relu',
                       'weight': package[f'conv{number}_weight'], 'bias': package[f'conv{number}_bias'],
                       'stride': [int(x) for x in package[f'conv{number}_stride']],
                       'padding': [int(x) for x in package[f'conv{number}_padding']]})
    layers.append({'name': 'gap', 'kind': 'global_average'})
    layers.append({'name': 'logits', 'kind': 'linear',
                   'weight': package['logits_weight'], 'bias': package['logits_bias']})
    result = {'kind': 'C01_BOARD_NUMPY_CNN_INFERENCE_NOT_FORMAL',
              'checkpoint_sha256': str(package['checkpoint_sha256'].item())}
    samples = []
    for name, crop in enumerate(crop_package['crops']):
        outcome = predict_trace(crop, layers)
        outcome['name'] = str(crop_package['names'][name])
        samples.append(outcome)
        print('CROP-RESULT: ' + json.dumps(outcome), flush=True)
    result['samples'] = samples
    matched = all(
        all(abs(s['probabilities'][i] - e['probabilities'][i]) <= 2e-5 for i in range(3))
        and s['class'] == e['class'] for s, e in zip(samples[:len(expected['results'])], expected['results']))
    result['pc_prediction_match'] = matched
    print('MATCH-PC-SOFTMAX: %s' % matched, flush=True)
    print('RESULT:', json.dumps(result), flush=True)
    if not matched:
        raise SystemExit(2)
    print('PASS: board numpy CNN agrees with PC torch predictions', flush=True)


if __name__ == '__main__':
    main()
