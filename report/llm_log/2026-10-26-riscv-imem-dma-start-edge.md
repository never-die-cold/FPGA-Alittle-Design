# [2026-10-26] 协作记录：IMEM 初值未生效与 PS DMA start 重复触发

> 标签：#riscv #coprocessor #IMEM #DMA #板级
> 平台：Codex + JL/NC（Windows Vivado 2026.1 / PYNQ-Z2）｜ 模型：GPT-5
> 相关 commit：`75fb2eb` `3404c33`；补丁 `report/llm_log/2026-10-26-imem-edge-fix.patch`

## 1. 任务与初始提示词

上板后 loader 出现 `NO_ACK`/DMA 卡住。要求定位：CPU 是否真的执行了 `cop_job`；IMEM 初值是否
进入 bitstream；`dma_start_ps_i` 高电平是否在 ACK 后重复触发；给出可交给构建机的补丁和板端
复验命令。不得用 fast-run 的短脉冲 workaround 冒充 RTL 修复。

## 2. 模型第一版方案

1. `create_pynq_cop_bd.tcl` 把 `CONFIG.IMEM_INIT_FILE/DMEM_INIT_FILE` 设为
   `file normalize` 后的 `cop_job.hex` 绝对路径，并检查文件存在。
2. `build_pynq_cop_gate.tcl` 综合后扫描 runme.log，若 `$readmemh` 出现
   unable/cannot/not found/failed 则 FAIL，禁止再产出 NOP 固件位流。
3. `run_pynq_cop_gate.ps1` 显式使用 `python.exe` 并传 `PYTHON`。
4. `pynq_cop_top.v` 给 `dma_start_ps_i` 加 PS 域上升沿检测，一次高电平只发一次请求。

## 3. 失败现象

1. 旧 10/25 bit 的 CPU 未执行固件：loader zero → `NO_ACK`，`STATUS=0x61`、
   `CFG_APPLIED==CFG_SEQ`、`DMA_BYTES=4096`、`FW_DECISION=0`。
2. IMEM 修复 bit（`59c2c918…`）CPU 已执行（`FW_DECISION=0x1003`），但第一笔 DMA 卡住：
   `STATUS=0x121`（DMA_BUSY=1、MODEL_VALID=0），`DMA_BYTES=0x200/0x000`，
   `DMASR=0`、`DMACR=0x10003`。原因是 `dma_start_ps_i` 高电平在 ACK 返回后二次触发，
   第二次 start 清掉了 adapter 的 `loading_o`；不是 AXI DMA Reset 位问题。
3. 尝试用 SLCR `FPGA_RST_CTRL` 复位 cop 域导致 AXI 挂死、SSH/COM12 失联，必须断电重启；
   该复位不能作为 workaround。
4. 板端 FCLK1 原为 142.857 MHz，先设 40 MHz 再重载 PL 后 20/20 首读才为 1。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 旧 bit `NO_ACK`、FW_DECISION=0 | CPU 没执行固件 | IMEM/DMEM 初值改绝对路径 + 存在性检查 | `$readmem ... read successfully` |
| 2 | 新 bit CPU 执行但 DMA 卡 | start 电平重复触发 | `dma_start_ps_i` 上升沿检测 | TB 断言“高电平只发一次” |
| 3 | 综合可能再产 NOP 固件 | 日志未设门禁 | runme.log `$readmemh` 失败即 FAIL | 门禁可失败可见 |
| 4 | SLCR 复位挂死 | 不是合法 workaround | 记录“禁止重复 SLCR 复位” | 断电重启恢复 |
| 5 | fast-run 短脉冲可跑通 | 只是板端临时绕过 | 明确不替代 RTL edge fix | 连续作业仍待验证 |

## 5. 最终结论

- 新 bit `566B512A…379032` 构建/门禁 PASS（WNS +2.771、DSP 136、BRAM36 69、DRC 0、
  `IMEM_FIRST_WORD=0x00008117`、`READMEM_WARNINGS=0`）。
- 旧 IMEM 修复 bit 上 fast-run：zero/pattern 各 3 轮，6/6 `matches_expected=true`；
  zero `2/2/258`（logits 2,-3,4）、pattern `0/0/0`（logits 1,-3,1），`result_seq=1`。
- 连续作业（不重载 Overlay）、长时间/温度稳定性、正式模型、真实相机、HDMI/EXE 全链仍未验收；
  BOARD 保持 UNVERIFIED。

## 6. 经验沉淀

- 触发条件：位流里 CPU 不执行，或 DMA start 是“电平”而握手是“脉冲”。
- 排查步骤：先看 IMEM_FIRST_WORD/`$readmem` 日志确认固件真的进 BRAM；再查 start 是否
  在 ACK 后重复触发；不要用 SLCR 复位做调试捷径。
- 适用范围：所有 BRAM 预载固件与 level→pulse 的 PS/PL 握手。
#skill候选
