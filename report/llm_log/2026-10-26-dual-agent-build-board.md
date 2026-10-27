# [2026-10-26 深夜] 双 Agent 冲刺：构建线（A）与上板线（B）阶段记录

> 分支 dev/riscv，HEAD 8884046；工作区含 A/B 并行未提交改动。
> 本记录只汇总事实，不把上板线未完成的项写成通过。

## 1. 构建线（Agent A）

- IMEM 门禁新 bit 已产出并通过整机门禁：
  - bit 566B512ABD63140FC9137E3C49C3D2A74B46520CF323139E914672AA35379032
  - hwh D069DB4FA760CCB0E49A0CCC566311829FCD9421E0CDDDBEA8C626E4EE65C6BB
  - xsa 382EF5ED1D5A0FEF27E62F7C8A65EF8C33D672C2E2E422F426C25D245483EBE6
  - WNS +2.771 ns、DSP 136、BRAM36 69、DRC 0；IMEM_FIRST_WORD=00008117、READMEM_WARNINGS=0。
- DMA start 边沿修复已落 RTL，tb_pynq_cop_top 增加“保持高电平只发一次请求”的断言，
  隔离 Icarus 实测 PASS；但本 bit 是在修改前启动的构建，**不含该修复**。
- 为下一次构建机重跑准备了补丁：data/logs/2026-10-26-build/edge-fix.patch。
- 上板包：
  - build/board-packages/diagnostic（pattern/zero）
  - build/board-packages/trained（roi_001）
  - Agent B 也用同一 bit 生成了 build/board-package-j02 与 build/board-package-trained；
    两套 bit SHA 相同，B 包多 frame 用例。
- 构建证据：data/logs/2026-10-26-build/README.md；A→B 交接：HANDOFF-A-to-B.md。

## 2. 上板线（Agent B）

- 旧 IMEM 修复 bit（59c2c918…）上 fast-run：zero/pattern 各 3 轮，6/6 matches_expected=true；
- 随后尝试 SLCR FPGA_RST_CTRL 复位 cop 域，AXI 读挂死，SSH/COM12 失联；已确认需断电重启，
  该复位不是 workaround，不能重复；
- 21:58 板卡已重新上电（串口能看到 boot 日志），B 正在恢复通道；新 bit 复跑与 trained
  roi_001 尚未完成。

## 3. 训练权重口径纠正

- loader/EXPECTED_OUTPUTS.tsv 的比较顺序是 logits = [-12,-30,41]；
  29e2f4 是原始 24-bit 字的高→低显示，不是 loader 列表顺序。
- trained 包 MODEL_ID=0x4A303251；firmware 只检查 MODEL_VALID，不比较 MODEL_ID。
- B 手册里 “41,-30,-12 / MODEL_ID=0x4A303250” 是诊断口径，trained 不能用。

## 4. 当前真实状态

- 新 bit：构建/门禁 PASS；未上板复跑。
- 训练权重：离板 9/9 argmax 一致、roi_001 RTL PASS；未上板。
- 连续作业：固件仍是单作业，每个 case 需重新 Overlay；未实现 loop/连续任务。
- 全链相机→板→EXE、正式模型精度、M2/M3/M4 验收：未完成，不能声明。
- A 线文件尚未 commit（.git/index.lock 权限拒绝），改动仍在工作区；需切完全权限或由他人提交。

## 5. 下一步

1. B 恢复 SSH/COM12 后，用 566b512a 新 bit + fast-run 复跑 zero/pattern，再跑 trained roi_001。
2. 构建机用 edge-fix.patch 重跑门禁，产出含边沿修复的 bit；再交 B 复验正常 loader 单作业。
3. 连续作业需要固件 loop 或新 bitstream，另列；不能用 fast-run 冒充连续能力。
4. 证据齐后更新 BOARD 状态；未完成项保持 UNVERIFIED。
