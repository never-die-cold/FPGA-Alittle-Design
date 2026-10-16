"""FP32 software reference preparation; no quantization or RTL contract."""
import numpy as np
import torch
from torch import nn


def folded_layers(model):
    """Fold evaluation BN into each convolution; export OIHW weights and O bias."""
    if model.training:
        raise ValueError("BN folding requires evaluation mode")
    layers = []
    for number, index in enumerate((0, 3, 6, 9), 1):
        conv, bn, relu = model.features[index:index + 3]
        if (not isinstance(conv, nn.Conv2d) or not isinstance(bn, nn.BatchNorm2d)
                or not isinstance(relu, nn.ReLU) or bn.training or not bn.track_running_stats
                or conv.groups != 1 or conv.dilation != (1, 1)):
            raise ValueError("unsupported convolution/BN structure")
        with torch.no_grad():
            factor = bn.weight / torch.sqrt(bn.running_var + bn.eps)
            bias = torch.zeros_like(bn.running_mean) if conv.bias is None else conv.bias
            weight = conv.weight * factor[:, None, None, None]
            bias = (bias - bn.running_mean) * factor + bn.bias
        tensors = [value.detach().cpu().numpy().astype(np.float32, copy=True) for value in (weight, bias)]
        if any(not np.isfinite(value).all() for value in tensors):
            raise ValueError("nonfinite folded parameters")
        layers.append({"name": f"conv{number}", "kind": "conv_relu", "weight": tensors[0],
                       "bias": tensors[1], "stride": list(conv.stride), "padding": list(conv.padding)})
    pool, flatten, head = model.features[12:15]
    if (not isinstance(pool, nn.AdaptiveAvgPool2d) or pool.output_size != 1
            or not isinstance(flatten, nn.Flatten) or not isinstance(head, nn.Linear)):
        raise ValueError("unsupported classifier head")
    layers.append({"name": "gap", "kind": "global_average"})
    layers.append({"name": "logits", "kind": "linear",
                   "weight": head.weight.detach().cpu().numpy().astype(np.float32, copy=True),
                   "bias": head.bias.detach().cpu().numpy().astype(np.float32, copy=True)})
    if any(not np.isfinite(layer[key]).all() for layer in layers for key in ("weight", "bias") if key in layer):
        raise ValueError("nonfinite head parameters")
    return layers


def original_trace(model, crops):
    """Record the unfused PyTorch model's stages as the package's independent oracle."""
    if model.training:
        raise ValueError("reference oracle requires evaluation mode")
    names = {2: "conv1", 5: "conv2", 8: "conv3", 11: "conv4", 13: "gap", 14: "logits"}
    value = torch.from_numpy(np.stack(crops).astype(np.float32)[:, None] / 255)
    trace = {"input": value.numpy().copy()}
    with torch.inference_mode():
        for index, module in enumerate(model.features):
            value = module(value)
            if index in names:
                trace[names[index]] = value.numpy().copy()
    return trace
