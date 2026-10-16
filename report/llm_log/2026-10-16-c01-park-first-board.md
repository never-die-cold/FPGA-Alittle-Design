# 2026-10-16 全链首跑与 CNN 上板（owner 授权，RISC-V 环例外）

> 接 `2026-10-16-c01-park-first-board.md`（park 驱动暖机+保护复制打通）。今天下午在同一天
> 内把两环补上：CNN（板上 numpy）与判定（PS 侧 inspection_rules.judge 语义），并跑出
> 全链首跑的 v1.2 LIVE 原型包。RISC-V 环 **未接入**（C03 J02 集成位流/工业固件未实现），
> EXE 环在等 PC↔PYNQ 网线（用户重接中，Pi 只走 HDMI 不受影响）。

## 板上真 CNN（无需 torch）

- 权重包导出：`inputs/export_cnn_board_package.py` 以冻结模型
  `models/cnn-border-fill-best.pt` + `model_reference.folded_layers`（BN 折进 conv）
  导出 `cnn_board_package.npz`（140856 B，sha `1440e3fd…`；checkpoint sha `70fe3dc3…`）。
  UART 上载 PASS。
- 板端推理：`inputs/c01_board_cnn.py` 纯 NumPy（sliding_window_view+einsum，同
  `numpy_reference` 口径）。四张 golden crop（gradient/dark_disk/bright_hexagon/mid_noise）
  与 PC torch 逐元素 softmax 对拍全部差 ≤2e-5（`MATCH-PC-SOFTMAX: True`）。
- 脚本本会话迭代 6 个版本（v1/v2/v3 的 pad、v5 的加 batch 维等），全部原始错误留在
  `c01-board-cnn-v1…v6-run.txt`；最终字节 `c01_board_cnn.py@same as v6`。
- `inputs/gen_golden_crops.py` 的 golden crops 定义为四类结构输入（替换原 synthetic
  随机——判别力太弱全判 bolt），PC 或板上均使用同 NPZ。

## 全链首跑

`inputs/c01_park_classify.py`：真实相机帧→采集（park 驱动，同正式复跑）→720p gray
→ golden locate → `reference.crop_resize` 64×64 → NumPy CNN（每目标 class/score）
→ `inspection_rules` 语义 judge → v1.2 LIVE decision 包。输出诚实记录当前场景
（6 目标全是暗色长条/深色遮挡、非真实紧固件，全判 bolt、RECHECK (touches_border)）
与模型质量无关，链路本身已通；定位阈值/工单/场景构图属于 M3 工位定标后续。

证据：`data/logs/2026-10-16-c01-park-first-board/`（README 已完整追加两节；
cnn 板端对拍、全链首跑、judge 语义段）。

## 拦阻（诚实边界）

1. **RISC-V 环未接**：需要 C03 J02（MMIO/DMA/cop_top 集成+x RISC-V 工业固件）。
2. **EXE 环等网线**：PYNQ 接网线后下一轮轮询 eth0 + 拉起 LIVE 服务。
3. owner 授权代做 WC/JL 工作本会话已 2 项：`park 语义评审`（契约 §6+判据换代已落档）
   与 `CNN 原型级验收边界`（FP32 参考代替 FPGA 加速的 prototype 口径）。代价与限制
   都遵循诚实原则。

完整待办见 `autonomy-scope-and-no-automations.md` 与今日两份 llm_log。
