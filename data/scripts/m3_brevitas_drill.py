#!/usr/bin/env python3
"""模块三训练侧 Brevitas QAT 演练（docs/module3-model-training.md §2 推荐路线验证，2026-10-03）

目的：证明正式量化路线"Brevitas QAT 训练 → INT8 导出 → 纯整数累加复现"可行，暴露接口问题。
与 2026-09-30 m3_train_drill.py 同网络（conv3x3 1→4→4 + fc，输入 8x8）、同两类合成数据，结果可对照。
在手工 PTQ 演练之上的增量：①训练即量化（QAT，激活 scale 参与训练）；
②复现语义升级为整数累加（int8×int8→int32→rescale→requant），即协处理器 MAC 阵列语义，
导出的 weights_hex + scales 可脱离 brevitas 独立复现 argmax——这是给 cop_top 黄金参考的口径。

接口教训（回填 module3-model-training.md §5 对齐点）：
  brevitas 0.13 无 layer.quant_input_scale 属性，激活 scale 用 QuantIdentity 显式量化点持有
  （IntQuantTensor.scale），不碰框架内部 API；层名显式命名（吸取 9/30 演练教训①）。

用法：python data/scripts/m3_brevitas_drill.py [输出目录]
前置：pip install brevitas（torch 复用既有 CPU 版）
"""
import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from brevitas.nn import QuantConv2d, QuantIdentity, QuantLinear
from brevitas.quant import Int8ActPerTensorFloat, Int8WeightPerTensorFloat

torch.manual_seed(20261003)
WQ = dict(weight_quant=Int8WeightPerTensorFloat, bias=False)  # 对称 per-tensor [-127,127]


class Net(nn.Module):
    """显式量化点链：qin0→conv1→relu→qin1→conv2→relu→qin2→fc，每个 IntQuantTensor 的 scale 手里都有。"""

    def __init__(self):
        super().__init__()
        self.qin0 = QuantIdentity(Int8ActPerTensorFloat, return_quant_tensor=True)
        self.conv1 = QuantConv2d(1, 4, 3, padding=1, **WQ)
        self.qin1 = QuantIdentity(Int8ActPerTensorFloat, return_quant_tensor=True)
        self.conv2 = QuantConv2d(4, 4, 3, padding=1, **WQ)
        self.qin2 = QuantIdentity(Int8ActPerTensorFloat, return_quant_tensor=True)
        self.fc = QuantLinear(4 * 8 * 8, 10, **WQ)

    def forward(self, x):
        x = F.relu(self.conv1(self.qin0(x)))
        x = F.relu(self.conv2(self.qin1(x)))
        return self.fc(self.qin2(x.flatten(1)))


def make_data(n, cls):
    """同 9/30 演练：左上角亮块 vs 右下角亮块 + 噪声。"""
    x = torch.rand(n, 1, 8, 8) * 0.25
    if cls == 1:
        x[:, :, :3, :3] += 0.75
    else:
        x[:, :, 5:, 5:] += 0.75
    return x, torch.full((n,), cls)


def quantize_int8(v, scale):
    return torch.round(v / scale).clamp(-127, 127)


def int_sim(scales, x):
    """纯整数累加复现：q_in int8 × w int8 → int32 累加（float 容器存整数值）→ dequant→relu→requant。"""
    (s0, s1, s2), (w1, w2, wf) = scales
    with torch.no_grad():
        q = quantize_int8(x, s0)
        acc = F.conv2d(q.float(), w1[0].float(), padding=1) * s0 * w1[1]
        q = quantize_int8(F.relu(acc), s1)
        acc = F.conv2d(q.float(), w2[0].float(), padding=1) * s1 * w2[1]
        q = quantize_int8(F.relu(acc), s2)
        return F.linear(q.float().flatten(1), wf[0].float()) * s2 * wf[1]


def export(scales, q1, q2, outdir):
    (s0, s1, s2), layers = scales
    n = 0
    with open(os.path.join(outdir, "weights_hex"), "w") as f:
        for name, wv in zip(("conv1", "conv2", "fc"), layers):
            for v in wv[0].flatten():
                f.write(f"{v.item() & 0xFF:02x}\n")
                n += 1
    with open(os.path.join(outdir, "scales.txt"), "w") as f:
        for name, wv in zip(("conv1", "conv2", "fc"), layers):
            f.write(f"{name} w_scale={wv[1]:.6e}\n")
        for name, s in zip(("in[conv1]", "in[conv2]", "in[fc]"), (s0, s1, s2)):
            f.write(f"act_scale {name}={s:.6e}\n")
    with open(os.path.join(outdir, "act_golden.txt"), "w") as f:
        f.write(f"in[conv1] first16: {', '.join(f'{v:.5f}' for v in q1.value.flatten()[:16].tolist())}\n")
        f.write(f"in[fc] first16: {', '.join(f'{v:.5f}' for v in q2.value.flatten()[:16].tolist())}\n")
    return n


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "data/logs/2026-10-03-m3-brevitas-drill"
    os.makedirs(outdir, exist_ok=True)

    model = Net()
    xs = torch.cat([make_data(16, 0)[0], make_data(16, 1)[0]])
    ys = torch.cat([make_data(16, 0)[1], make_data(16, 1)[1]])
    opt = torch.optim.SGD(model.parameters(), lr=0.05)
    loss_fn = nn.CrossEntropyLoss()
    loss = None
    for _ in range(60):
        opt.zero_grad()
        loss = loss_fn(model(xs), ys)
        loss.backward()
        opt.step()

    # 分步前向（与 Net.forward 逐算子一致），顺路持有各量化点的 IntQuantTensor
    with torch.no_grad():
        q0 = model.qin0(xs)
        q1 = model.qin1(F.relu(model.conv1(q0)))
        q2 = model.qin2(F.relu(model.conv2(q1)).flatten(1))
        out = model.fc(q2)
        assert torch.allclose(out, model(xs), atol=1e-6), "分步前向与 Net.forward 不一致"
    acc = (out.argmax(1) == ys).float().mean().item()

    scales = ((float(q0.scale), float(q1.scale), float(q2.scale)),
              tuple((m.quant_weight().int().to(torch.int8), float(m.quant_weight().scale))
                    for m in (model.conv1, model.conv2, model.fc)))
    out_sim = int_sim(scales, xs)
    agree = (out.argmax(1) == out_sim.argmax(1)).float().mean().item()
    max_diff = (out - out_sim).abs().max().item()

    n = export(scales, q1, q2, outdir)
    print(f"qat loss={loss.item():.4f} acc={acc:.2f}")
    print(f"int-sim argmax_agree={agree:.2f} max_out_diff={max_diff:.4f}")
    print(f"export: {n} weights -> weights_hex + scales.txt + act_golden.txt @ {outdir}")
    assert acc == 1.0, "QAT 训练未收敛，演练无效"
    assert agree == 1.0, "整数累加复现与 brevitas 前向不一致，导出口径需回炉"
    print("PASS: brevitas QAT -> int8 export -> integer-accum replay complete (argmax 100% agree)")


if __name__ == "__main__":
    main()
