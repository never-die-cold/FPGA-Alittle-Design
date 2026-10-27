# 2026-10-26 训练权重导出为 INT8 payload：RTL 仿真 PASS（未上板）

> 分支：`fix/imem-init-2026-10-26`（工作区）｜对象：`models/cnn-border-fill-best.pt`
> 结论：**训练权重 → PTQ INT8 → 36,032 B payload → cnn_sequencer RTL 仿真逐元素一致**。
> 这不是板级结论；BOARD 仍 UNVERIFIED。

## 1. 目的

板上现有 payload 是 `kind=PROVISIONAL` 的 J02 诊断网络（非训练模型）。本步把仓库里的
FP32 训练权重导出成同一 manifest/同一 36,032 B 容器的 INT8 参数，让硬件 CNN 输出具有
识别语义。导出复用三条已验证路径，只替换数值：

- 权重排布 `pack_weights`（`sim/coprocessor/generate_conv_vectors.py`，O16_KH_KW_I8）；
- 整数语义 `run_network`（`src/coprocessor/int8_network_reference.py`，C02 冻结契约）；
- 容器 `generate_payload_manifest.py`（manifest v1，20 tensors，36032 B）。

## 2. 新增脚本

`sim/scripts/export_trained_payload.py`：BN 折叠 → 逐通道权重量化 + 逐张量激活 scale
（输入固定 `1/127`，契约 §3.2）→ 搜索不溢出的 INT32 bias → 每通道
`multiplier/shift`（shift=31）→ 逐层黄金 + `result.txt` → 调 manifest 打包。

判据：INT8 与 FP32 的 argmax 在标定图上一致率 ≥ 0.9，否则退出码 1、不出包。

## 3. 命令与原始输出

```powershell
python sim\scripts\export_trained_payload.py --images data\evidence\2026-10-10-offline-inspection \
  --limit 12 --output sim\build\payload-trained
```

```text
PASS: manifest_v1 PROVISIONAL payload bytes=36032 sha256=a31a26f734796aa9867507ae5fea68581b314e2c8eb3aed1aee26075cdbd8736 crc32=0x05b6f630
agreement=9/9 (1.000)
empty: int8=0 fp32=0 score=8901 margin=69 AGREE
synthetic: int8=0 fp32=0 score=3741 margin=29 AGREE
annotated: int8=0 fp32=0 score=5547 margin=43 AGREE
frame: int8=0 fp32=0 score=3741 margin=29 AGREE
roi_000: int8=0 fp32=0 score=19351 margin=150 AGREE
roi_001: int8=2 fp32=2 score=6837 margin=53 AGREE
roi_002: int8=0 fp32=0 score=20770 margin=161 AGREE
viewer-exe: int8=0 fp32=0 score=1161 margin=9 AGREE
viewer: int8=0 fp32=0 score=1161 margin=9 AGREE
PASS: trained payload sim/build/payload-trained/payload-v1 sha256=a31a26f7...
```

manifest 结构负例：

```text
PASS: manifest_v1 20 tensors preserve J02 bytes; SHA256/CRC/padding valid; offset and OOB negatives rejected
```

**RTL 仿真（训练权重进硬件路径）**：

```powershell
& 'C:\msys64\ucrt64\bin\iverilog.exe' -g2001 -Wall -s tb_cnn_sequencer \
  -P tb_cnn_sequencer.USE_BRAM=1 -P tb_cnn_sequencer.USE_PAYLOAD=1 \
  -o sim\build\payload_network.vvp sim\coprocessor\tb_cnn_sequencer.v src\coprocessor\*.v
& 'C:\msys64\ucrt64\bin\vvp.exe' sim\build\payload_network.vvp \
  +model=sim/build/payload-trained/network-vectors \
  +case=sim/build/payload-trained/network-vectors/roi_001 \
  +payload=sim/build/payload-trained/payload-v1/payload.bin +crc=05b6f630
```

```text
PASS: payload_network manifest payload -> DMA -> shadow BRAM -> atomic activate; bytes=36032 crc32=05b6f630
PASS: cnn_sequencer .../roi_001 all 9225 packed words/73795 elements match integer network;
      logits=29e2f4 class=2 margin=53 cycles=472594
```

## 4. 归档哈希

| 文件 | SHA256 |
|:---|:---|
| `payload.bin` | `a31a26f734796aa9867507ae5fea68581b314e2c8eb3aed1aee26075cdbd8736` |
| `manifest.json` | `e605f9652aa631fe6e7083e18b61779b1f16c0a471b73d7a1228cc807b256b70` |
| `network-vectors/weights.hex` | `fa8621a16a1fc730ed3601729d6d138608720448ac4ca984c8f6084e7fcb9997` |
| `network-vectors/bias.hex` | `639371cdd918ec3c922c13cdd95822aeb87f734758ef49d3bb7715a9056cb05a` |
| `network-vectors/multipliers.hex` | `39d753ec029d976b9a9b7789289b7a8529426018476c6d4f23affc0b829cf220` |
| `network-vectors/shifts.hex` | `2a21fc76bf3fdeca567f1e84e74d1a442d8443778ca4fb541ca5f346864cbfe0` |
| `network-vectors/roi_001/*` | 逐层黄金与 `result.txt` 见目录 |

## 5. 边界（不得外推）

- 标定图来自仓库内夹具（`synthetic.png`、`roi_00x.png`、`frame.png`），**不是紧固件实拍集**；
  一致率 9/9 只证明整数化没有改变 argmax，**不证明识别精度**。
- 只跑了 `roi_001` 一例进 RTL；其余八例仅 Python 参考对拍。
- `generate_payload_manifest.py` 的 `model_id` 固定 `0x4A303250`，与诊断网相同；正式区分
  需 JL 决定是否加 `--model-id`，否则 PS 侧指纹无法区分诊断/训练权重。
- `package_coprocessor_nc.sh` 与 `test_cop_payload_loader.py` 的用例名写死 `pattern/zero`，
  训练权重用的实拍 case 名要打包，需把用例列表改成读 `cases.txt`。
- 板上仍待：IMEM 修复后的新 bit、FCLK 回读、zero/pattern、再跑本 payload。

## 6. 下一步

1. **JL**：新 bit 门禁通过后，用本 payload 替换 `payload/provisional-model` 重打包
   （先决定 model_id 与用例名问题），NC 在板上跑同一 case 对拍 `logits=29e2f4`。
2. **NC**：板级顺序不变 —— 改钟 40 MHz → 重配 PL → `clock --reads 20` → zero/pattern →
   训练权重 case。
3. **WC**：`PynqDmaPlane` 打通后，PS 侧 ROI 直接喂同一格式，硬件输出接 EXE。
