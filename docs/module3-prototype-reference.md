# 模块三：交付原型的 FP32 逐层软件参考

2026-10-10，`dev/exe @ aa23206` 上的未提交工作区实现。
目的：为 CNN 实现提供可复算的结构、参数和逐层数值，解决只看最终分类无法定位错误的问题。
这份参考不是正式 INT8 模型、RTL 接口契约或 M2 硬件验收证据。

## 实现与验证状态

- 已实现并验证：实际网络审计、推理 BN 折叠、NumPy 独立算子、逐层对拍、位模式导出和隔离复算。
- 已实现但未验证：PYNQ NumPy 环境兼容性与板端运行时间；现有权重在真实工位的分类效果。
- 未实现/未接入：可信 PTQ/QAT、正式缩放/零点/舍入/饱和参数、INT8 权重排布、
  CNN RTL、与核握手、真实取图和 LIVE 服务。

## 实际网络与预算

来源为 `models/cnn-border-fill-best.pt`，SHA256
`70fe3dc35bb592481f43e2086efe46b4ca5d2788d53a2b318d23a7169f7ecec6`。
类别顺序 bolt/nut/washer，输入 64×64 灰度，输入浮点值为像素/255。
结构复用交付 `FastenerCNN`，以下数字由仓库 `test_model_audit.py` 逐项断言。

| 层 | 算子 / stride / padding | 输出 CHW 或 C | 权重元素 | 折叠偏置 | MAC |
|---|---|---|---:|---:|---:|
| conv1 | 3×3, 1→16 / 2 / 1 + ReLU | 16×32×32 | 144 | 16 | 147,456 |
| conv2 | 3×3, 16→32 / 1 / 1 + ReLU | 32×32×32 | 4,608 | 32 | 4,718,592 |
| conv3 | 3×3, 32→32 / 2 / 1 + ReLU | 32×16×16 | 9,216 | 32 | 2,359,296 |
| conv4 | 3×3, 32→64 / 1 / 1 + ReLU | 64×16×16 | 18,432 | 64 | 4,718,592 |
| gap | 每通道 16×16 平均 | 64 | 0 | 0 | 0 |
| logits | Linear 64→3，无 softmax | 3 | 192 | 3 | 192 |
| 总计 | | | **32,592** | **147** | **11,944,128** |

MAC 指乘加对数，不包含偏置、ReLU、GAP、读写与调度；GAP 另有 16,320 次加法和 64 次除法。
原模型训练参数 32,883；折叠后权重+偏置 32,739 个 FP32，共 130,956 字节。
旧文档约 0.33 MB 估算已修正。若未来采用 INT8 权重+INT32 偏置，单是这两部分为
33,180 字节；此值不含量化 scale、地址对齐、tile/padding、DMA 和缓存，也不是当前 INT8 交付物。

最大单个输出为 32,768 元素；完整相邻两层激活最多 49,152 元素，FP32 为 196,608 字节。
这是保存完整张量的数量口径，不是 NumPy 实际内存峰值或硬件 BRAM 用量；
滑动窗口/框架工作区、流式调度、双缓冲与权重存放需另算。
128 个 MAC、100 MHz 若每拍全利用，纯 MAC 理想耗时约 0.933 ms/ROI；
不包含其他算子和数据搬运，不承诺这个频率、利用率或实机延迟。

## BN 折叠和独立计算

推理时 BN 使用固定 running_mean/var。令 a=gamma/sqrt(var+epsilon)，
折叠得到 W'=W×a、b'=(b−mean)×a+beta，原无偏置卷积的 b 按 0 处理。
因此即使原 Conv 的 bias=False，折叠后仍需要每通道偏置。
只允许 eval 模式，训练模式和非有限参数拒绝。

独立 NumPy 实现按输入滑窗与 OIHW 权重作互相关，不翻转卷积核；
CHW 输入在空间两侧补实数零，按原 stride 取窗，再加偏置/ReLU；
GAP 按空间平均，Linear 输出原始 logits。未来 INT8 实数零的编码须按 zero_point 处理。
参考层保存原始 PyTorch 模型的结果，BN 仍在原计算图中，
不把 NumPy 输出当作自己的期望值。包中的 NumPy 检查器不导入 PyTorch。

## 浮点判据与失败留痕

六个输入（全零、中灰、全白、固定随机、角点脉冲、交替条纹）×六个网络阶段对拍。
初始 atol=2e-5 在条纹的 conv4 上 FAIL，完整日志和双精度诊断已保留。
诊断使用相同折叠 FP32 参数、双精度累加，排除滑窗坐标/卷积核方向错误的可能；
误差规模支持累加顺序、BN 折叠与浮点舍入的解释，不作为整数等价证明。

最终逐元素判据为 `abs(actual−expected) <= 1e-4 + 2e-5*abs(expected)`。
六组对拍最大绝对差 0.000183105469，三组归档包最大绝对差 0.00016784668；
六个输入最终类别一致。这是容差内接近，非 FP32 逐位相同、非模型精度验收。
另有手算滑窗索引测试；整数黄金参考须在量化/累加/舍入/饱和规则确定后另建。

## 参考包格式

归档入口：[fp32-reference-v1](../data/evidence/2026-10-10-model-reference/README.md)。
包保存折叠权重/偏置、三个诊断输入及每阶段完整期望张量，清单标明来源、
代码哈希、运行版本、层形状、排布、容差和数值误差；这些输入无真实类别标签。

- 像素：uint8，HW，每行两个十六进制字符。
- 权重：FP32，OIHW；Linear 为 OI；偏置为 O。
- 激活：FP32，CHW；GAP/logits 为 C。input 是归一化后的 1×64×64。
- FP32 hex：每行八个十六进制字符，表示 IEEE754 32 位模式；例如 1.0 为 3f800000。
- NPY 与 hex 都按 C 顺序逐元素排列，NPY FP32 为小端；hex 行序不是逐字节倒序。
- 清单和每个 NPY/hex/工具文件都有 SHA256；同时检查 NPY/hex 位模式一致。

FP32 hex 不能直接送入 INT8 MAC；包中未提供 INT8 scale/zero-point。
哈希用于修改检测，不提供来源签名。生产正式参考时还须归档数据划分与标注。
导出目录已存在时拒绝覆盖；清单最后写出，中断的无清单目录不是完整参考包。

## 仓库与独立复现

```bash
bash sim/scripts/run_inspection_python.sh
```

当前入口共十一组：原有六组应用测试 + 五组逐层参考/审计/文件/包测试。
本轮不改既有八组视觉或 EXE 实现，不重复以相同条件跑硬件无关的旧入口。

```powershell
python sim/vision/export_model_reference.py sim/build/my-fp32-reference
python -I sim/vision/check_model_reference.py sim/build/my-fp32-reference
python -I sim/build/my-fp32-reference/tools/check_model_reference.py sim/build/my-fp32-reference
```

导出需要 NumPy/PyTorch，校验只需 NumPy。将整个包复制到别处后，执行包内检查器即可。
测试已在仓库内临时目录以 Python -I、无原模型/源模块依赖的方式隔离复算，
并覆盖覆盖目录拒绝、工具篡改、审计不一致和修改数值黄金后的拒绝。
所有验证输出留在仓库内，原始日志见[本轮验证](../data/logs/2026-10-10-model-reference/README.md)。
