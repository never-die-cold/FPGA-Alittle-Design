# C01 capture 阶段直接诊断与停机 SR 位语义实测定性（2026-10-15 深夜）

接续 `../2026-10-15-onboard-n02-n03/` 的 N03 排查。基线 `dev/model@491d628` + 各会话未提交改动。
本目录**不改任何受版本控制文件**：两个实验脚本只落在 `inputs/`（本地）并上传到既有板端试验目录
`/home/xilinx/vision_m2/c01-ff610bdae8ef46ce9304e531ebaf9627/`（沿用 10-15 已核对哈希的三件套所在目录）。
受控改动为零；`git diff --check` 退出 0（`git-diff-check.txt`）。

## 起点（为何不重跑完整入口）

昨晚 `2026-10-15-onboard-n02-n03` 晚段（`c01-late-smoke.txt`）已证明：候选位流上视频在位
（帧计数 4038→83985）、帧首 smoke PASS（配置号 1 配置应用成功）。完整冻结入口
（`c01_ddr_onboard.py@e822a708`）要求起始就是原 vision 且 ~11 s settle 立即重试 smoke，
而实测候选位流上取消频锁定 + JVC 重建需 >15 s——重跑完整入口大概率在 smoke 竞态上再次失败，
拿不到新信息。故将实验拆为两层：

## 实验一：冻结驱动的 capture 阶段直接执行（跳过 smoke 竞态）

`inputs/c01_stage_direct.py`（SHA `ea9b7d5a…`，107 行；上传校验 `upload-c01_stage_direct.py.txt`）：

- 板端核验三件套之一 `c01_capture.py` 为 N03 冻结字节（`1f11aefd…`）、候选位流在板、
  视频计数器在走（60 fps精确），才知道是合法停机起点。
- R11→轮询视频锁定→ live 在位确认 → 新建 `SingleFrameCapture`（冻结驱动全类）→ `capture()`，
  含四缓冲分配、复位、几何配置、清停期粘滞错误、RUN/帧计数自动停机、联合确认、invalidate、
  独立副本与 PNG round-trip；QUARANTINE/UNSAFE-STOP 保活语义与冻结入口一致。
- 失败路径末尾照常恢复原 vision（restore_original）。

**结果（`c01-stage-direct-run.txt`）**：

1. PRECHECK：视频 +60 帧/s、CAP1 身份/几何/故障全零、DMA 停机态 CR=0x10002 SR=0x14811。
2. 四缓冲分配通过（物理地址 64B 对齐、互不重叠），soft reset 成功，描述符写入有效，
   `VSIZE=720` 写入生效。
3. `configured_idle` SR 仍为 0x14811 → 写 W1C 0xF9F0 → `cleared_idle` SR=0x10811 →
   驱动判据"读回必须干净"不满足 → **冻结驱动拒绝 RUN**（设计内安全拒启，非脚本错误）。
4. 采集 STATUS 侧全程零错误事件（0xc/0x10/0x1c/0x20 全 0）、帧计数全程 60fps 在走——
   问题**不在视频桥/CAP 层**，只在 VDMA S2MM 停机期自身状态。
5. 恢复原 vision：`restore_error=RuntimeError('configuration commit is busy')`（首次 smoke 在
   锁定未完成时提交 R11→视频重新锁定后提交自动应用，随后我方早烟 PASS）。

## 实验二：停机 SR 错误位 W1C/电平语义定性（不发 RUN）

`inputs/c01_sr_persistence.py`（SHA `b5c54e62…`；上传校验 `upload-c01_sr_persistence.py.txt`）。
原 vision → 下载候选 → 全程停机（CR RS=0 恒定）+ 60fps 流持续走流的前提下：

**原始结果（`c01-sr-persistence-run.txt`，板载 SERIES 主时间轴）**：

| t | SR |
|---|---|
| 0.0 | 0x10001 |
| 1.5 | 0x14811 |
| 3.0 → 12.0 | 0x14811 不再变化 |

- 下载后 SR 从"干净的 0x10001"（仅 Halted）开始 → 1.5 s 内 bit4+bit11+bit14 **自发置位**，
  不是"接续早前残留"；一旦出现就永远保持。
- 两次 W1C 0xF9F0 + 写后立即读回 + 1s + 4s 读回：**三次读回全部仍是 0x14811**。
  bit4/11/14 对 W1C 写入完全不响应——按 PG020 定义它们要么是 RO 电平位，要么由每位时钟
  重新注入，**不是"可清一次的粘滞位"**。
- ErrIRQ（bit16）即使在这些错误持续时也**不置位**（0x14811 低 16 位，无 0x10000），
  与过去"ErrIRQ 属停止期 IP 自身行为"的旧记录表述不同：ErrIRQ 不是该错误持续存在的
  可依赖信号。
- 尾部：SR 恒 0x14811，CR 保持停机；恢复默认 vision smoke 一次 PASS（配置号 1）。

## 结论（给 WC/JL 兼容评审的硬事实）

1. **单帧驱动的"停机期清干净再 RUN"门在视频在场时物理上不可满足。** bit4/11/14 在停机
   +TUSER fsync 流持续灌入的条件下是可复现、可预期的电平状态（保留成因最强嫌疑：
   `C_USE_S2MM_FSYNC=2` 下 halted 仍 dummy-tready，`vh_rfs.vhd 71761/71911/71925`，
   见 baseline 记录；流持续送帧 → 伪错误持续重现）。
2. 10-12/10-13 的 `CaptureError('DMA reset/clear not clean')`（前次=顺序旧，指望 W1C 清成功）
   与本轮 `CaptureError('DMA configured idle reset/clear not clean')`（顺序修复后清账成功但
   电平立即回来）是**同一根因的两种落地方式**；顺序修复把失败点后移一步，但没改变
   停机期可清性。修复方向必须让清除发生在 RS=1 且通道在暖机接收的窗口（正是并行会话
   `c01_park_capture.py` 已选择的路线）；按 `c01-ddr-frame-ownership-v0.md` §6“只有暖机阶段
   在 RS=1 且未 Halted 时允许清理精确的历史 0x4810”的现有措辞，**无法覆盖 bit4/11/14
   电平持续重现的形态**，建议升级为“暖机期 0xF9F0 允许重复 W1C”，capture/copy 阶段
   一律拒绝，与 park 驱动语义一致。
3. 视频桥/CAP 层与 DDR 帧槽链路全部干净：本实验未产生任何 CAP 故障位。
   N03 卡点的根因最终收敛到 **VDMA S2MM 停机期错误位的 W1C/电平性质**，不是视频、
   不是缓冲分配、不是上传/哈希链路。
4. 桩模型复核（10-16 重读源码后修正）：并行会话的 `sim/vision/test_c01_capture.py` 并非只有
   "可清一次"模型——`idle_sticky_until_geometry`（几何后可清一次）与 `idle_sticky_persistent`
   （每次读取都重新置位、驱动必须拒启）两个模式都已存在，
   `test_persistent_idle_faults_refuse_run_before_start` 断言的正是实机行为。因此离线套件
   并无"放行实机必败路径"的缺口；实机复测一直没跑到 DMA 阶段的原因是入口 smoke 竞态，
   不是测试缺牙。剩余不符只是注释级：`until_geometry` 模式上方注释"they re-assert until
   nonzero geometry is configured"与实测（置位持续于几何配置之后）不一致，标注待改。

## 恢复与现场状态

- 原位流 vision.bit（SHA `4f0c491a…`）两次在板并 smoke PASS（配置号 1/2 已各留日志）；
  UVC 24 帧真实场景 unle `uvc-final-original/raw.png`（SHA `1dd653d0…`）。
- boot_id 全程 `c291b2c8-…` 未变（结果日志首尾一致）。
- 板端 CAP 计数器、pipe 寄存器基线存档（`restore-state-probe.txt`）。

## 边界（未做）

- 未改 RTL/驱动源、未动 N03 冻结三件套；未在停机期把错误位清零后启动。
- park 模式整帧标识/慢复制/IRQ 槽绑定实机验证仍属 NC 下一轮；
  本轮"电平型停机期错误位"事实与 park 驱动的暖机期清除语义相容（RS=1 时电平消失），
  但仍需 WC/JL 首先评审该绑定并升级契约措辞后执行。
- `c01_sr_persistence.py` 内 SWEEP1/2 有两个脚本级瑕疵（`bits()` 装饰性变量无用化、
  `dict(... Protocol ... if False else ...)` 的残留表达式）已在本 README 微记，
  板端执行的已是上传版本。GEN 结果壳不被改变。

复现入口：上传 `inputs/` 两个脚本到试验目录后按
`c01_stage_direct.py` / `c01_sr_persistence.py` 顺序执行。
