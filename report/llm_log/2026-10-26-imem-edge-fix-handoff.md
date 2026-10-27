# 2026-10-26 协处理器 IMEM/DMA start 修复交接

> 本机按用户要求停止 Vivado 与仿真；以下补丁和板端结论只作为队友构建/验证的输入，
> 不是最终验收。本机只保留上板操作。

## 0. 最新结果（2026-10-26）

- 已用 `sim/scripts/cop_board_fast_run.py` 在板上跑通 zero/pattern；3 轮 zero + 3 轮 pattern 全部
  `matches_expected=true`、exit 0。
- zero：class 2 / margin 2 / score 258 / logits 2,-3,4；pattern：class 0 / margin 0 / score 0 /
  logits 1,-3,1；result_seq=1（每次重新 Overlay 后）。
- 板端 workaround：预检先做、Overlay 后快速配置/DMA、C helper 产生短 start 脉冲；
  **不替代 RTL edge fix**，但可直接复验。
- 仍缺：不重载 Overlay 的连续作业、长时间/温度稳定性、正式模型、真实相机、HDMI/EXE 全链。

## 1. 已确认的板端事实

- 板卡：PYNQ-Z2，192.168.50.99，USB 串口 COM12；旧原型服务已停止（cron 仅 @reboot）。
- 当前板端包：~/cop-pkg（10/25 包，bit d14a4bd0...1e2a1a，hwh 928f0d59...49107）。
- 新 IMEM 修复包：~/cop-pkg-imem-20261026，bit 59c2c918...f6d659，hwh ec330836...a8f1e8。
- FCLK1：142.857143 -> 40.000000 MHz；先设 40 再重新加载 PL 后，20/20 次首读全 0x00000001。
- 10/25 旧 bit（CPU 未执行固件）：loader zero -> NO_ACK；STATUS=0x61、
  CFG_APPLIED==CFG_SEQ、DMA_BYTES=4096、FW_DECISION=0。
- IMEM 修复 bit（59c2...）：CPU 已执行（FW_DECISION=0x1003），但第一笔 DMA 卡住：
  STATUS=0x121（DMA_BUSY=1，MODEL_VALID=0）；DMA_BYTES=0x200 或 0x000；
  DMASR=0；DMACR=0x10003；GPIO2_DATA=0x1（start_ready=1，payload_error=0）。
  结论：dma_start_ps_i 高电平在 ack 返回后二次触发，第二次 start 清掉 adapter 的
  loading_o；不是 AXI DMA Reset 位问题（bit1 是 Keyhole）。

## 2. 本轮补丁（report/llm_log/2026-10-26-imem-edge-fix.patch）

1. build/create_pynq_cop_bd.tcl：把 pynq_cop_top 的
   CONFIG.IMEM_INIT_FILE/DMEM_INIT_FILE 设为 file normalize 后的
   src/riscv_fw/cop_job.hex 绝对路径，并检查文件存在。Vivado 综合日志已出现：
   INFO: [Synth 8-3876] $readmem data file '.../src/riscv_fw/cop_job.hex' is read successfully
2. build/build_pynq_cop_gate.tcl：综合后读 runme.log，若 $readmemh 出现
   unable/cannot/not found/failed 则 FAIL，防止再产出 NOP 固件位流。
3. build/run_pynq_cop_gate.ps1：显式用 python.exe 并传 PYTHON，解决 Windows 只有
   python、Makefile 默认 python3 的 Error 9009。
4. src/riscv/pynq_cop_top.v：给 dma_start_ps_i 加 PS 域上升沿检测，一次高电平只发一次
   请求，避免 ack 返回后重复触发；这一版尚未完成构建/板测。

## 3. 队友下一步（构建机执行）

1. 应用补丁：git apply report/llm_log/2026-10-26-imem-edge-fix.patch
2. 在构建机运行 build/run_pynq_cop_gate.ps1；必须看到
   '$readmem ... is read successfully' 和 'PYNQ COP WHOLE-SYSTEM GATE PASSED'，
   记录新 bit/hwh/xsa SHA256。
3. 把新 bit/hwh 传到板端独立包目录；先设 FCLK1=40，再加载新 bit，然后执行：
   loader clock --reads 20
   loader run --package . --case zero --measurement zero.json --timeout 10
   loader run --package . --case pattern --measurement pattern.json --timeout 10
4. 若 DMA 仍卡：读 STATUS/DMA_BYTES/DMASR/DMACR/GPIO2，不要写 PASS。
5. 若 DMA 正常但 NO_ACK：先确认固件 guard 是否在 loader preflight 期间已经过期；
   `run` 前应重新 Overlay，并在固件等待窗口内完成配置/DMA。

## 4. 边界

- 已取得板上 zero/pattern 首次诊断硬件输出，3 轮重复 PASS；但连续作业、稳定性、正式模型、
  真实相机与 EXE 全链仍未验收，BOARD 整机状态仍 UNVERIFIED_NEEDS_NC。
- 不重载 Overlay 的第二笔 `NO_ACK`，固件仍是单作业；连续作业需固件 loop/新 bitstream。
- 尝试用 SLCR `FPGA_RST_CTRL` 复位 cop 域导致板卡挂死（SSH banner reset、COM12 无输出），
  需要断电重启。**不要重复 SLCR 复位**；事故前 3 轮 PASS 证据已落盘。

## 6. 新 loader 的 reset 风险（给 A/B）

- `build/board-packages/diagnostic/payload/tools/cop_payload_loader.py` 的 `prepare_board()`
  会调用 `pulse_cop_reset()`；本板 `FPGA_RST_CTRL` 读回 `0`，按代码会写 `0x2` 再 `0x0`，
  可能把 FCLK0/AXI 一起复位。**不要直接调用新 loader 的 `prepare_board()/run_board()` 上板。**
- B 端改用 `sim/scripts/cop_board_fast_run.py`：preflight → Overlay → 配置/DMA，不调用
  `prepare_board`、不碰 SLCR；新 bit `566B512A…379032` 可在断电重启后用它验证。
- 新 bit 不含 DMA 边沿修复；fast-run 的 C 短脉冲仍需要。
- 本机剩余构建目录/日志是中止的中间产物，不能作为最终 bit。
- 采集卡：index 1 是 HDMI 采集（当前全黑），index 2 是笔记本虚拟摄像头；
  compute-only 位流不驱动 HDMI OUT，视频验收要等整机视频位流。
- 另有未跟踪文件 sim/scripts/export_trained_payload.py、
  data/logs/2026-10-26-trained-payload/ 不是本轮产生，已原样保留。