# 2026-10-26 项目最终状态与已知限制

> 记录时间：2026-10-26 22:40。本文只记录事实，不是完赛声明，也不替代 M2/M3/M4 验收。

## 1. 结论

- 模块一（自研 RISC-V 核＋最小 SoC）已收口，证据见 [模块一收口报告](module1-closure.md)。
- 板级硬件 CNN 的旧 IMEM 修复 bit（59c2c918...）上，诊断网 zero/pattern 各 3 轮、6/6 matches_expected=true；这是目前唯一板上硬件 CNN 结果。
- 含 DMA start 边沿修复的 edge-fix bit（9341F7FA...）整机门禁 PASS，诊断/训练包已构建并通过包内 SHA 复核；但该 bit 与 trained 都尚未上板。
- 板卡当前出现 SD/mmc I/O 错误与冷启动 No Devices Found，需断电/重插 SD/重刷后再继续。
- 全链相机→板→PS→EXE、正式 INT8 模型/精度、M2/M3/M4 均未完成；不能声明最终成品完成。

## 2. 已验证

| 项 | 证据 |
|---|---|
| 模块一核与最小 SoC 收口 | [module1-closure.md](module1-closure.md) |
| 视觉 RTL／真实链路历史证据 | [2026-10-03-vision-onboard](../data/logs/2026-10-03-vision-onboard/README.md)、[2026-10-07-pi-pynq](../data/logs/2026-10-07-pi-pynq/README.md) |
| CNN 算子/整网离板黄金 | [2026-10-13-cnn-arithmetic](../data/logs/2026-10-13-cnn-arithmetic/README.md) |
| 板上诊断网 zero/pattern 6/6 | [2026-10-26-board](../data/logs/2026-10-26-board/README.md)、[zero-fast.json](../data/logs/2026-10-26-board/zero-fast.json)、[pattern-fast.json](../data/logs/2026-10-26-board/pattern-fast.json) |
| 训练权重离板 9/9 + RTL roi_001 | [2026-10-26-trained-payload](../data/logs/2026-10-26-trained-payload/README.md) |
| edge-fix 整机门禁 + 包 SHA 12/12 | [2026-10-26-build](../data/logs/2026-10-26-build/README.md) |
| A5 loader/driver 软件测试 | [2026-10-26-build](../data/logs/2026-10-26-build/README.md) |

## 3. 关键产物

- edge-fix bit（含 dma_start_ps_q 上升沿检测）：
  - bit 9341F7FA008C4A853767B2850701758E0534C923AED955B4B3B3F7E750BC4160
  - hwh DB5B53B9D1B85E8F28DD83880C0015E3D55AE492BE114809C853955891432506
  - xsa E4FE5D35973699F62EE483188E7DFE4264D04E271602910728B29130D7A4AB77
  - WNS +3.062 ns、DSP 136、BRAM36 69、DRC 0、IMEM_FIRST_WORD=00008117
- 包：build/board-package-edge-fix（pattern, zero）、build/board-package-edge-fix-trained（roi_001, frame）
- 旧板上诊断 bit 59c2c918...：zero/pattern 6/6；仅作历史/回退证据。

## 4. 未验证 / 未实现

- edge-fix bit 的板上 zero/pattern/trained 未实测；BOARD 仍 UNVERIFIED。
- 训练权重未上板；只有离板 9/9 与 RTL roi_001 证据。
- 固件仍是单作业，每个 case 需重新 Overlay；连续作业未实现。
- 真实相机 HDMI -> 板卡视频 -> PS 定位 -> CNN -> 核判定 -> EXE 全链未完成。
- 正式数据集/INT8 模型/真实精度/混淆矩阵未完成（J05/J06）。
- M2/M3/M4 验收、演示视频、目标电脑发布包未完成。

## 5. 板卡当前阻塞

- [b4-fclk-set-40.txt](../data/logs/2026-10-26-board/b4-fclk-set-40.txt)：冷板无 PL 时 cop_fclk.py 报 No Devices Found。
- [serial-state-1.txt](../data/logs/2026-10-26-board/serial-state-1.txt) 与 [serial-netfix-1.txt](../data/logs/2026-10-26-board/serial-netfix-1.txt)：mmc0 Timeout、SDHCI ADMA Err、I/O error mmcblk0p2，串口命令多次超时。
- 处理：断电、重插 SD 或换备份卡/重刷；恢复后按冷启动顺序烧 edge bit -> loader clock -> zero/pattern -> trained。见 [B-QUICKSTART](../data/logs/2026-10-26-build/B-QUICKSTART.md)。

## 6. 复现入口

- 核：bash sim/scripts/run_iverilog.sh all；见 [模块一复现](../docs/runbooks/module1-reproduction.md)。
- 协处理器离板：bash sim/scripts/run_coprocessor_iverilog.sh all。
- edge bit：build/build_pynq_cop_gate.tcl；包：sim/scripts/build_board_package.py。
- 上板：tools/cop_payload_loader.py、sim/scripts/cop_fclk.py、sim/scripts/cop_board_fast_run.py。

## 7. 下一步

1. 恢复板卡（SD/电源），按 cold-boot 顺序烧 edge-fix bit。
2. 跑 loader clock -> zero/pattern -> roi_001/frame，归档 JSON/串口/哈希。
3. 连续作业需固件 loop 或新 bitstream；不能用 fast-run 冒充连续能力。
4. 真实相机/EXE 全链、正式模型与 M2/M3/M4 按主计划继续。
