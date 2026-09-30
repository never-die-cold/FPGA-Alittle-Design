#!/usr/bin/env python3
"""模块三训练侧全链演练（docs/module3-model-training.md §3 结论项，2026-09-30）

目的：证明"训练 → INT8 量化 → 权重 hex 导出"链路可行，暴露接口问题。
非正式交付物；正式网络/数据集待 10/5 拍板后重做。

链路：
  1. 极简 CNN（conv3x3(1→4) → relu → conv3x3(4→4) → relu → flatten → fc(64→10)），
     输入 8x8，两类合成可分数据（免下载数据集，网络独立）。
  2. SGD 短训练。
  3. 手工 per-tensor 对称量化：权重 INT8（scale=amax/127），激活用校准集 amax 静态量化
     ——与 INT8 MAC 阵列语义对齐，不依赖 torch.ao 的浮点格式。
  4. 精度对照：FP32 vs 模拟 INT8（去量化重算）逐样本 argmax 一致率 + 最大绝对输出差。
  5. 导出（cop_top 契约冻结前的默认排布，冻结后按契约重排）：
     weights_hex：逐层扁平 INT8（conv1, conv2, fc），每行一字节
     scales.txt ：逐层 w_scale + 各层输入 amax
     act_golden.txt：校准首图逐层输出前 16 值（FP32 参考，供协处理器逐层比对）

用法：python data/scripts/m3_train_drill.py [输出目录]
前置：pip install torch --index-url https://download.pytorch.org/whl/cpu
"""
import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(20260930)


def make_model():
    return nn.Sequential(
        nn.Conv2d(1, 4, 3, padding=1), nn.ReLU(),
        nn.Conv2d(4, 4, 3, padding=1), nn.ReLU(),
        nn.Flatten(), nn.Linear(4 * 8 * 8, 10),
    )


def make_data(n, cls):
    """两类合成可分样本：左上角亮块 vs 右下角亮块 + 噪声。"""
    x = torch.rand(n, 1, 8, 8) * 0.25
    if cls == 1:
        x[:, :, :3, :3] += 0.75
    else:
        x[:, :, 5:, 5:] += 0.75
    return x, torch.full((n,), cls)


def calibrate_activations(model, xs):
    """逐层前向，记录每个 conv/linear 层输入的 amax（激活量化 scale 来源）。"""
    acts = {}
    with torch.no_grad():
        h = xs
        for i, m in enumerate(model):
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                acts[i] = h.abs().max().item()
            h = m(h)
    return acts


def quantize_weights(model):
    """{name: (q_int8, scale)}，对称 per-tensor，q 范围 [-127,127]。"""
    out = {}
    for name, p in model.named_parameters():
        if "weight" not in name:
            continue
        amax = p.abs().max().item()
        scale = amax / 127.0 if amax > 0 else 1.0
        out[name] = (torch.round(p / scale).clamp(-127, 127).to(torch.int8), scale)
    return out


def sim_int8_infer(model, qw, acts_max, x):
    """权重 INT8 + 激活 INT8 的去量化模拟推理。"""
    def q_act(v, layer_idx):
        amax = acts_max[layer_idx]
        s = amax / 127.0 if amax > 0 else 1.0
        return (v / s).round().clamp(-127, 127) * s

    with torch.no_grad():
        h = x
        conv_names = ["0.weight", "2.weight"]   # Sequential 索引（ReLU 占位）
        conv_i = 0
        for i, m in enumerate(model):
            if isinstance(m, nn.Conv2d):
                s_w = qw[conv_names[conv_i]][1]
                w = qw[conv_names[conv_i]][0].float() * s_w
                h = F.conv2d(q_act(h, i), w, padding=m.padding)
                conv_i += 1
            elif isinstance(m, nn.Linear):
                s_w = qw["5.weight"][1]
                w = qw["5.weight"][0].float() * s_w
                h = F.linear(h, w)
            else:
                h = m(h)
    return h


def export_hex(qw, path):
    n = 0
    with open(path, "w") as f:
        for layer in sorted(qw):
            for v in qw[layer][0].flatten():
                f.write(f"{v.item() & 0xFF:02x}\n")
                n += 1
    return n


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "data/logs/2026-09-30-m3-train-drill"
    os.makedirs(outdir, exist_ok=True)

    model = make_model()
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

    out_fp = model(xs)
    acc_fp = (out_fp.argmax(1) == ys).float().mean().item()

    qw = quantize_weights(model)
    acts_max = calibrate_activations(model, xs)
    out_q = sim_int8_infer(model, qw, acts_max, xs)
    acc_q = (out_q.argmax(1) == ys).float().mean().item()
    agree = (out_fp.argmax(1) == out_q.argmax(1)).float().mean().item()
    max_diff = (out_fp - out_q).abs().max().item()

    n = export_hex(qw, os.path.join(outdir, "weights_hex"))
    with open(os.path.join(outdir, "scales.txt"), "w") as f:
        for layer in sorted(qw):
            f.write(f"{layer} w_scale={qw[layer][1]:.6e}\n")
        for i in sorted(acts_max):
            f.write(f"act_in[{i}] amax={acts_max[i]:.6e}\n")
    with torch.no_grad():
        h = xs[:1]
        with open(os.path.join(outdir, "act_golden.txt"), "w") as f:
            for i, m in enumerate(model):
                if isinstance(m, nn.Flatten):
                    h = m(h)
                    continue
                h = m(h)
                vals = ", ".join(f"{v:.5f}" for v in h.flatten()[:16].tolist())
                f.write(f"layer[{i}] {type(m).__name__} first16: {vals}\n")

    print(f"train loss={loss.item():.4f} acc_fp={acc_fp:.2f}")
    print(f"int8 acc_q={acc_q:.2f} argmax_agree={agree:.2f} max_out_diff={max_diff:.4f}")
    print(f"export: {n} weights -> weights_hex + scales.txt + act_golden.txt @ {outdir}")
    assert acc_fp == 1.0, "FP 训练未收敛，演练无效"
    assert agree == 1.0, "INT8 与 FP 预测不一致，量化策略需回炉"
    print("PASS: train->int8->hex drill complete (argmax 100% agree)")


if __name__ == "__main__":
    main()
