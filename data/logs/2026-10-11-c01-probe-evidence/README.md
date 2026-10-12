# C01 stream_seq 疑点实测闭环（2026-10-11 23:00–23:11）

基线 dev/model@c292038（未提交工作区）。本轮目标：按 `docs/project-handoff-2026-10-11.md` §7.2/§7.3，
用起止 VDMA CR/SR 实值 + stream_seq 增量判定"停止期间 stream_seq 增长"是否为异常，不改 RTL、不重载旧候选。

## 1. 离板改动（均在未提交工作区；改前版本已归档）

| 文件 | 改前 SHA256 | 改后 SHA256 |
| --- | --- | --- |
| `sim/scripts/c01_status_onboard.py` | `07e471ca…5898a56d94` | `0f0905b28d1f009e9979c35359b2642dc6abe902fd9f2010503672f95ecc2fb9` |
| `sim/vision/test_c01_status_onboard.py` | `96f2d212…f936d7094c764f11b9`（见归档目录内文件） | `f0f8222bc38ca38dc8bacce759b99536f5f10d2b60ad00945ae8704fcbf49b50` |

改前版本逐字节存于 `settled-script-archive/`。改动内容：

1. 窗口起止均打印 `VDMA-START/END: CR=… SR=…` 实值（原脚本只判位不打印，窗口结束不读）。
2. `SEQ-START`/`SEQ-END(delta)` 记录窗口前后 stream_seq；删除与 IP 实际行为相悖的"停止时 stream_seq=0"断言，
   替代判据：**窗口结束时通道仍 halted（CR.RS=0、SR.Halted=1）+ 锁定保持 + 捕获故障位/error_epoch 全零**。
3. 主检查异常与 finally 恢复异常分离：`MAIN-FAIL:` / `RECOVERY-FAIL:` 分别打点；
   主失败不再被恢复阶段的 SystemExit3 顶掉（`MAIN-FAIL-WAS:` 保留原异常）。
4. `faulthandler.dump_traceback_later(15, repeat=True)` 改为单次 60 秒兜底并在正常完成时 cancel，
   正常 20 秒睡眠不再打印 Timeout 栈。
5. 恢复路径改为 `restore_original()` 有界重试：每次 settle 5 秒后 smoke，NOVIDEO（SystemExit 3）最多重试一次，
   其他退出码立即上抛；不盲目反复 reprogram。

## 2. VDMA 停止期 TREADY 行为查证（源码证据）

IP 与板上完全同源：`axi_vdma` v6.3，本地 `D:/Vivado_downloads/2026.1/Vivado/data/ip/xilinx/axi_vdma_v6_3/hdl/axi_vdma_v6_3_vh_rfs.vhd`；
实际产物 HWH（`sim/build/c01-hdmi-1791713720540454/`）参数 `C_USE_S2MM_FSYNC=2`、`C_INCLUDE_S2MM=1`。

- 71761 行：`s_axis_s2mm_tready_signal <= (dw_conv_tready and s2mm_chnl_ready) or s2mm_dummy_tready`——dummy 项不受通道就绪约束。
- FSYNC=2 分支（71782 行）：`s2mm_dummy_tready <= d_tready_sof_late_cmb or d_tready_before_fsync_cmb`。
- 71911 行 `GEN_D_TREADY_BEFORE_FSYNC`：**`s2mm_dmasr_halted_s='1'` 时 `d_tready_before_fsync <= '1'`**；
  71925 行：halted 同时把 `d_tready_before_fsync_clr_flag1` 置 1。即 **停止状态显式产生 dummy tready**。
- 71760 行：`s_axis_s2mm_tvalid_int <= tvalid and s2mm_chnl_ready`——停机时内部数据通路看不到 valid，**无 DDR 写**。
- 71886 行：通道未就绪 + tvalid 无 SOF → `s2mm_sof_late_err` 并置 `d_tready_sof_late` 继续消费。

结论：v6.3 在 FSYNC=2 下，**S2MM halted 时 TREADY 保持高、握手照常、数据被丢弃**。AMD 论坛有同类行为报告
（"AXI VDMA fsync setting issue"，adaptivesupport.amd.com，2024-09）。因此"停止期间 stream_seq=0"旧判据无效；
stream_seq 只是监视器看到的握手几何计数，与交接文档口径一致，不是 DDR 写完成凭据。

## 3. 板卡预检（只读，无需 sudo 的部分先做）

- COM12 存在；shell 存活（`shell-alive-preflight.txt`）：boot_id `312c2889-f77a-438a-9c74-2a07e8a5b9c6` 与交接记录一致，未重启。
- `vision.bit` SHA 前缀 `4f0c491a6383d8a1` 与原位流一致。
- `sudo -n` 过期（`sudo-and-dirs-preflight.txt`）→ 用户经 `pynq_serial_auth.ps1` 弹窗重新认证，窗口退出码 0。
- 远端新建 `c01-ab75f5d26f8747418c4b6b0fd83995cd/`，从 `c01-8b4d42b3653c4c31a70626bf9a971abf/` 复制候选，
  板端重读 SHA：bit `86d2adb0…81d14f`、hwh `eaaf68c3…a04cc4a7` 与修复版候选一致（`remote-dir-prep.txt`）。
- 新脚本经 `send_pynq_file.ps1` raw UART 上传并 SHA 复读校验通过（`upload-script-console.txt`）。
  首次调用因 Git Bash MSYS 路径转换改写了 `/home/...` 参数被路径校验拒绝，`MSYS_NO_PATHCONV=1` 后成功。

## 4. 离板回归

- `python-entry-probe-evidence.txt` / `-exit.txt=0`：11 组 Python 统一入口（msys64 bash + 显式 PATH + VISION_PYTHON）。
- `git diff --check` 干净（design_v0.md 的 CRLF 提示为既有状态，与本次无关）。

## 5. 实机诊断（`board-c01-probe-coexist/`，改进版脚本 + coexist 包装器）

**整体 PASS**：BOARD_EXIT=0、UVC_EXIT=0、UVC 结束早于 CLEANUP、`HOST_EXIT_CODE=0`、CLEANUP 标记在场。

关键读数（`board.txt`）：

| 时点 | VDMA CR (0x30) | VDMA SR (0x34) | stream_seq |
| --- | --- | --- | --- |
| 窗口前 | 0x00010002 | 0x00010001 | 81 |
| 窗口后（20s） | 0x00010002（不变） | 0x00014811 | 1281 |

- CR 全程 bit0(RS)=0——通道从未启动；SR 全程 bit0(Halted)=1。
- **delta=1200 = 60fps × 20s 精确吻合**：停止状态下流以满速率被"接受-丢弃"。
- SR 结束值新增位（v6.3 位定义，10731–10756 行）：bit4 DMAIntErr、bit11 FSIZE_MORE_OR_SOF_LATE_ERR、
  bit14 ERRIRQ；bit16 为 IRQ 阈值计数字段（=1），非错误。bit11 正是 71886 行"未就绪收到无 SOF 数据"的
  dummy 消费路径所置的粘滞错误位——与源码推断完全一致，且**这些位是停止期 IP 自身行为，不是本设计的故障**。
- CAP1 状态：0x4=3（锁定+跟踪中）、rejected=0、error_epoch=0、overflow_intervals=0、lock_losses=0。
- 候选 smoke（配置号1 applied）与恢复后 smoke 均**一次通过**；上轮"恢复等待5秒后 NOVIDEO"未复现，RECOVERY-RETRY 未触发。
- UVC 24 帧 1280×720×3 uint8（MJPG 30fps 模式），png_sha256 `e69d0f53…af46d8fa`、pixels_sha256
  `df694868…40ce3418`，尾帧像素 std=91、跨度 0–255，真实场景非均匀内容。

## 6. 本轮结论与边界

1. **诊断整体通过（显示/状态口径）**：地址、恒等、几何、锁定、原 pipe smoke、共存窗口、恢复全部有实值证据；
   异常分离与有界恢复按交接建议落地。
2. `stream_seq` 增长在 RS=0/Halted=1 下是 IP 行为，**不是 DMA 运行、更不是 DDR 写完成的证据**；
   新 PASS 行已明确标注。C01 的 DDR 取帧验收仍未做、未通过。
3. 修复候选位流（bit `86d2adb0…`）第二次实机运行全程正常；仍非发布位流。

## 7. 未解释观察与下一步

- **窗口前计数偏低**：lock→settle→smoke 约 6–8 秒只累计 81 帧（≈10fps 均值），窗口内却满速 60fps。
  可能与监视器跟踪建立、输入同步启动或 dummy-tready 建立时序有关；本轮不影响判据，列为下次诊断观察点。
- **PS 驱动注意**：VDMA 停止期会置粘滞 SR 错误位（DMAIntErr/SOFLateErr/ERRIRQ）；首次启动捕获 DMA 前
  必须复位通道或写 1 清 SR，错误位不能当作"通道曾经跑过"的证据。
- 下一步沿交接 §7.6：custom DDR 帧槽所有权协议（写完成/错误、槽交接、cache invalidate、独立完整副本、幂等释放），
  再做真实 BGR 颜色/动态对拍与 N03 长测。
