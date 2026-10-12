"""Recompute BN statistics with train crops, select on val, check FP32 BN folding."""
import argparse
import copy
import json
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from train_fastener_classifier import FastenerCNN
from train_scene_classifier import SceneCrops


def score(model, loader):
    model.eval()
    correct = 0
    with torch.no_grad():
        for images, labels in loader:
            correct += (model(images).argmax(1) == labels).sum().item()
    return correct/len(loader.dataset)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(4)
    state = torch.load(args.weights, map_location='cpu', weights_only=False)
    model = FastenerCNN()
    model.load_state_dict(state['state_dict'])
    mode = state.get('preprocess_mode', 'opposite')
    size = state.get('input_size', 64)
    val = DataLoader(SceneCrops(args.dataset, 'val', input_size=size, mode=mode), 64)
    train = DataLoader(SceneCrops(args.dataset, 'train', input_size=size, mode=mode), 50)
    baseline = score(model, val)
    original = copy.deepcopy(model.state_dict())
    model.train()
    for module in model.modules():
        if isinstance(module, torch.nn.BatchNorm2d):
            module.reset_running_stats()
            module.momentum = None
    with torch.no_grad():
        for images, _ in train:
            model(images)
    calibrated = score(model, val)
    if calibrated <= baseline:
        model.load_state_dict(original)
    args.output.mkdir(parents=True, exist_ok=True)
    state.update(state_dict=model.state_dict(), architecture='fastener-4conv-bn-v1',
                 bn_recalibrated=calibrated > baseline)
    torch.save(state, args.output / 'best.pt')
    folded = copy.deepcopy(model).eval()
    for index in [0, 3, 6, 9]:
        folded.features[index] = torch.nn.utils.fuse_conv_bn_eval(
            folded.features[index], folded.features[index+1])
        folded.features[index+1] = torch.nn.Identity()
    max_error, disagreements = 0., 0
    with torch.no_grad():
        for images, _ in val:
            a, b = model(images), folded(images)
            max_error = max(max_error, (a-b).abs().max().item())
            disagreements += (a.argmax(1) != b.argmax(1)).sum().item()
    torch.save({'architecture': 'fastener-4conv-folded-fp32-v1',
                'state_dict': folded.state_dict(), 'classes': state['classes'], 'input_size': size,
                'preprocess_mode': mode},
               args.output / 'folded-fp32.pt')
    report = {'weights': str(args.weights), 'dataset': str(args.dataset),
              'baseline_val_accuracy': baseline, 'recalibrated_val_accuracy': calibrated,
              'selected_recalibrated': calibrated > baseline, 'fold_max_logit_error': max_error,
              'fold_argmax_disagreements': disagreements, 'val_objects': len(val.dataset),
              'int8_verified': False, 'board_verified': False}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
