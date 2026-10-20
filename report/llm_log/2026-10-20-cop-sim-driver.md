# 2026-10-20 COP_SIM PS 驱动、服务接入与异常矩阵

## 任务

用户本轮分工：WC 负责把计算能力接到服务和 EXE；先与 JL 对齐“怎么提交、怎么知道完成、
怎么拿结果、出错怎么恢复”；硬件未就绪时用模拟硬件跑通软件流程；确保超时、重复请求、
旧结果、运行失败不会在 UI 上显示成 CHECK_PASS；完成一轮服务+EXE 的展示/保存/追溯。

## 主要决策

1. **不另造协议**：PS 使用档只冻结 C03 §4/§5 的用法，寄存器语义、权限和固件判定
   仍以 C03 与 `cop_work_order.h` 为准；模拟硬件按 J04 读 0 的 VERSION/CAPABILITY/
   ERROR_CODE 建模（OPEN-9），不臆造错误码。
2. **模拟硬件的 seam**：驱动只依赖 `read32/write32` + DMA 面；`CopSim`/`SimDmaPlane`
   只用于离板。真实 `PynqDmaPlane` 故意 `NotImplementedError`，避免把占位实现说成已接入。
3. **安全闸**：结果必须通过 `RESULT_SEQ` 递增、索引窗双读、`FW_DECISION` 复算；
   PS verdict 严格度必须 ≥ 固件，计数必须相等。旧的 sticky 结果、不递增的 seq、
   更宽松的 PS 判定都直接 503，不生成报文。
4. **touch_border 是 PS 侧更严格 gate**：J04 固件 `cop_judge` 不读描述符；PS 仍提交
   border 目标，但在最终判定加 `touches_border`，并把它作为“允许 PS 更严格”的唯一理由。
5. **预启动门本地短路**：`ROI_COUNT=0`（OPEN-11）与 >10 不提交，避免固件只写
   `FW_DECISION` 而不置 DONE 导致的等待歧义；同时把“固件缺完成通知”登记为 JL 阻断项。
6. **重试语义**：服务按 C04 §2.4 草案保留 16 条 `trigger_ref→packet`；EXE 手动失败后
   复用同一 ref，失败期间 `manual_failed` 立即撤旧 PASS，不等 max_age。
7. **追溯链**：`cop_trace.json` 写帧像素哈希 + ROI 字节哈希 + cfg/result seq + FW/PS 判定；
   `round_artifacts` 能验证 capture→trace→ROI 的哈希链，ROI 篡改被拒。

## 证据

- `sim/scripts/run_inspection_python.sh`：19 组，exit 0；
- `sim/scripts/run_cop_sim_round.sh`：一轮 `CHECK_PASS`（1/1/1，3 target，cfg/result seq=1），
  截图、records、packet、trace、ROI 哈希链齐全；
- `data/logs/2026-10-20-cop-sim-round/README.md` 汇总命令、结果、异常矩阵与边界；
- 异常：stale 轮 503 且无 packet；同 ref 重试新 check 但只记一条；重复 ref 同 check；
  超时/CRC/ABORT/软复位/重复 JOB_ID 均 PASS。

## K1/K2 拉取与对齐（同日）

- 拉取 JL `5d2f867`（K1 `docs/coprocessor-wc-interface.md`、K2 `docs/coprocessor-storage-plan.md`），
  合并为 `f540a38`；K1 是 C03 摘录，K2 是 PLAN/UNVERIFIED，不改 WC 数据面接口。
- 按 K1/C03 §3.2 修正：正常轮 PS **不写 `CTRL`**，成功 DONE/RESULT_VALID 留给固件下一轮
  START 前清；PS 只在 ERROR/TIMEOUT/ABORT/进程重启遗留终态时写 `CTRL=0x18`。
- `PynqMmio` 移除 `0x8001_0000` 默认值，强制 Address Editor 的 PS AXI base（K1 mock 约束）。
- 补“旧 DONE 还在”的竞态：终态轮询只接受 `RESULT_SEQ` 已变化的 DONE；旧 DONE 持续
  超过宽限即报错，不把上一轮结果贴到新 bbox。
- 新增测试：正常第二笔任务无 `CTRL` 写；PynqMmio 缺 base 拒绝。两套 gate 仍为 exit 0。
- 两项待 JL 确认：K1 的 `CFG_APPLIED && READY` 窗口（PS 以 `CFG_APPLIED` 为硬回执）；
  “消费后 RISC-V 清 DONE”缺少 PS→FW 消费回执（当前固件在下一轮 START 前清）。

## 明确未做

- 未上板；未验证真实 MMIO/AXI/DataMover/CDC；未实现 `PynqDmaPlane`；
- 未使用正式 INT8 模型；`S_input=1/127` 是 sim-only，分类器为脚本/图像派生；
- 固件重复作业与预启动完成通知仍缺（JL 阻断项）；
- 真实 UVC/HDMI、整机时序/bitstream、PYNQ 服务部署仍由 NC/JL 接手。
