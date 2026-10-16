# 2026-10-15 深夜 C01 capture 阶段直接诊断 + 停机 SR 位电平定性（N03 根因收敛）

> 后续会话（ZCode）。接 `2026-10-15-onboard-n02-n03` 的 N03 排查；无 RTL/驱动/入口改动，
> 两个实验脚本归档于 `data/logs/2026-10-15-c01-direct-capture-stage/inputs/` 并上传既有
> 板端试验目录 `c01-ff610bdae8ef46ce9304e531ebaf9627` 上执行。未 commit。

## 背景

- 10-12 板端首战：`DMA reset/clear not clean`（旧顺序，停机粘滞 0x4810 清不净）。
- 随后驱动改为"先配几何再清停机粘滞"（`c01_capture.py` 118-125），离线桩按"可清一次的
  粘滞位"模拟——但该修复从未上板复测。
- 10-15 完整入口两次在 smoke 阶段 NOVIDEO 停止（候选位流上视频锁定 >15 s，
  入口 settle 预算 ~11 s），失败点从未到达 DMA 阶段。
- 本会话晚段已证明候选上 smoke 可 PASS（配置号 1）。
- 本轮起点：候选在板、60 fps 在流、DMA 停机 SR=0x14811。

## 实验一：跳过 smoke 竞态、直接跑冻结驱动的 capture()

预检（视频 +60 帧/s、CAP1 身份/几何/故障全零、停机）通过后执行冻结
`SingleFrameCapture.capture()`：四缓冲分配、复位、几何、清粘滞、RUN 前判据全程走到——

- 几何配置后 `configured_idle` 仍 0x14811；写 W1C 0xF9F0 后 `cleared_idle`=0x10811
  （bit12/14 确实被清一次）→ 但 bit4+bit11 重新置位 → 驱动按判据**拒绝 RUN**（设计内安全拒启）。
- 采集 STATUS 全程零错误事件、帧计数 60 fps——问题不在视频桥，在 VDMA S2MM 停机期自身。

## 实验二：停机 SR 语义定性（全程不发 RUN）

候选重载后 SR 时间轴：t=0 时 0x10001（干净）→ 1.5 s 内自发升到 0x14811 → 12 s 恒定。
两次 W1C 0xF9F0 + 写后立即读回：**三次读回全部仍 0x14811**。

**结论：bit4/11/14 在停机+TUSER fsync 流持续灌入下是电平型状态（ continu 重注入），
不是"可清一次的粘滞位"。** 视频在场时，"停机期清干净再 RUN"的驱动门物理上不可满足；
这正是 10-12 失败与 10-15 拒启的统一根因。ErrIRQ（bit16）在错误持续时也不置位。

## 由此确定的方向

1. 清除必须发生在 RS=1（暖机接收）窗口——与并行会话已产出的
   `c01_park_capture.py` 路线一致；契约 `c01-ddr-frame-ownership-v0.md` §6 的"暖机期清
   精确 0x4810"措辞需升级为"暖机期允许重复 W1C 0xF9F0"。
2. 桩模型复核（10-16 修正）：套件已含 `idle_sticky_persistent` 模式并断言拒启，
   离线回归并未放行实机必败的驱动；实机两次实验没跑到 DMA 的真实原因是入口 smoke
   竞态。`until_geometry` 模式的注释与实测不符属注释级修正，语义无需改桩。
3. 冻结 N03 三件套未动；返板包选入口须区分 `e822a708`（冻结）与 `54dd5d64`（并行漂移）。

## 现场

恢复原 vision smoke PASS（配置号 1/2 各一次），UVC 24 帧真实场景确认。
boot_id 全程未变。COM12 已释放。证据：`data/logs/2026-10-15-c01-direct-capture-stage/`。

## 待办

- 改桩（离线）：`test_c01_capture.py` IDLE_FAULTS 持续置位语义 + 版本复审。
- WC/JL 评审 park 驱动 IRQ/槽绑定 + 契约措辞升级 → NC 执行 park 驱动 N03 实测。
- `c01_sr_persistence.py` 有两处脚本级瑕疵（`bits()` 未使用、残留 `if False else` 表达式），
  已在 README 注明；后续版本清理后重新上传前须重跑 `-CheckOnly`。
