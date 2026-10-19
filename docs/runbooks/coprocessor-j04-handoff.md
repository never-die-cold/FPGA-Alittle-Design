# J04 协处理器实现交接单

> 状态：JL 侧“实现 + 可交接”收口；不等于完整验证通过或板级验收，JL 不代 WC/NC 签字。
> J04 总状态见[模块计划](../../src/coprocessor/plan.md)：J04a（JL 实现/冒烟）✅，J04b（完整验证/物理 bank/综合/板验）🟡。
> 源码锚点：PR #86 的 head（`dev/riscv`），不写死 SHA 以免自我引用失效；交接基线为 `7d6355b`
> （`411d9ee..7d6355b`，9 个提交）。内容锚点以本单 §2 的文件 SHA256 为准。
> 早期日志中的 `9fdd035` 等哈希是 rebase 前本地记录，不对应远端提交；复现以本单和 `dev/riscv` 为准。

## 1. 一键冒烟与独立入口

仓库根目录执行；脚本会按 `RISCV_CROSS`/`COPROCESSOR_PYTHON` 覆盖，并在本机自动回退：

```bash
# Windows/MSYS2（本机工具链为 riscv32-unknown-elf）
COPROCESSOR_PYTHON=python RISCV_CROSS=riscv32-unknown-elf- bash sim/scripts/run_coprocessor_iverilog.sh all

# Linux（仓库内 venv）
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh all
```

独立入口均使用同一前缀：`mmio_gate`、`ctrl_regs`、`mailbox`、`config_regs`、
`dma_loader`、`task_ctrl`、`axi_lite`、`firmware`、`cop_top`。例如：

```bash
COPROCESSOR_PYTHON=python RISCV_CROSS=riscv32-unknown-elf- bash sim/scripts/run_coprocessor_iverilog.sh cop_top
```

TB 内用任务组织激励，用常量/J02 生成文件作参考，并用独立断言比对；新增用例应只追加激励和期望，
不得放宽既有断言。`cop_top` 的刺激任务为 `ps_wr`/`ps_rd` 与 DMA stream，黄金由 J02
`generate_network_vectors.py` 生成，结果逐字段比对。

## 2. 交付文件指纹

`行数 SHA256 文件`：

```text
43 82f44ec0627728ab287e693a0124966a2d7b78280ae21f8f06ac7efd1a3a2ca2 src/coprocessor/cop_axi_lite_frontend.v
46 15aff88321fab1130bbc189e438beabe4061e598eccbe13c7c3b313ebe0bb0e2 src/coprocessor/cop_cdc_mailbox.v
63 c5eccd3a95c6c8739fba4ad9bf9f51bb583b6c8743d99b4421ac27157a129cdc src/coprocessor/cop_config_regs.v
65 caa57cc8bf0fe5ac442847adae18a793532d31c7af4fe47da7468f9f40e50874 src/coprocessor/cop_core_mmio_gate.v
46 ae0e9a92b9010dbd6d7983012fa5d1458ea6cfbcdaec17e8402236136f6d5bba src/coprocessor/cop_ctrl_regs.v
61 18db51c0fada9c8d15f42a9d57192b2d3a9a2a81073a2452d6447dcd7335bf28 src/coprocessor/cop_dma_loader.v
57 7b3f856df20de31d788a296e26da5f61d119d071d1592b86ff22821b05f1c7a0 src/coprocessor/cop_task_ctrl.v
194 c5bc93aa605b403a29112a863ba8b0a74c31236881d35057e7c56841b30f4f95 src/coprocessor/cop_top.v
147 071a4f197a4651b0da26645b46a65c166bccbacc77c88b2b4f21b4abce69a591 src/coprocessor/cnn_sequencer.v
81 22f8b5d3e70bb51f135a0ae52b59879b14c5f90ce78ac70a1d878ae8682afe9b src/riscv/soc_top.v
105 5543a19e9ac305895d2ea59605b15d06aa0c488f540b1cef31cd4ba6ea44f913 src/riscv_fw/cop_job.c
35 1692bb7235424dfce0a3877256a910a16834f9411d21a133cc1c305f61d95ee6 src/riscv_fw/cop_work_order.h
78 0e7708050fb5d5b1651594314c31311dbb5824eeb1bf277c97db6ed5b92dd042 src/riscv_fw/Makefile
26 ed9fed691756d69a25ad823d41b1fdc31ac14393912248614288538e01f2ae2a sim/coprocessor/tb_cop_axi_lite_frontend.v
34 66133a217901355f313e76369dca62e035790aa92e748a5e5625b10250090e2e sim/coprocessor/tb_cop_cdc_mailbox.v
36 829424c336f1e1e638a7fd1fcb58785d0c0aaf4b0e705459e7b20ec85d817fab sim/coprocessor/tb_cop_config_regs.v
49 50bfb8057e8f87eb90637ab61f0085e88a91a30107a24f789f1b6ef7500a2466 sim/coprocessor/tb_cop_core_mmio_gate.v
59 208e21301510a4332b7e8afe8eaacedc77f1bb45dd0b0df3e019aeb672469980 sim/coprocessor/tb_cop_ctrl_regs.v
29 1b57950f2165727cbdbe43172884aa9f4baf15ac7ebce3ff9dca9d58e2705cc2 sim/coprocessor/tb_cop_dma_loader.v
36 a626c7abb2252d63bde764d818b18938f13f5a68b622a51346c46246a109959a sim/coprocessor/tb_cop_task_ctrl.v
139 cc2eb17bc22a06494ac396969f2ba09cce5037b30cacb9e73b73648f4214faa4 sim/coprocessor/tb_cop_top.v
163 a66ca4bbad1336f4ab7f2984fb634b92a7b62faec99b11d60a9d641f3c0623e5 sim/coprocessor/tb_cnn_sequencer.v
19 cbd5a4cb478b01a8668e625602e3e327f2eba4b3c7ae1dcd45cc489f50786e9e sim/coprocessor/test_cop_work_order.c
94 392e7fdf453770428fd507013eec7d3ac00d31f5836f274e288ad60202b4fb42 sim/scripts/run_coprocessor_iverilog.sh
```

## 3. 模块接口与时序约定

- `cop_core_mmio_gate`：本地无等待口；仅 `be=4'b1111` 整字写。`hit` 表示窗口归属，非法访问仍 hit 并读 0、零副作用。
- `cop_cdc_mailbox`：源侧至多一笔 pending；稳定 payload + toggle 请求，目标接受后 toggle ACK；ACK 不代表 CNN 完成。
- `cop_config_regs`：PS 写 shadow，`CFG_COMMIT` 原子复制 applied；运行任务只读 START 时快照。
- `cop_dma_loader`：valid/ready stream，按 keep 计数并计算 CRC32；短包、超长或 CRC 不符不得置对应 VALID。
- `cop_task_ctrl`：按 target 顺序启动；16-byte 结果项最后提交；ABORT 回 IDLE，SOFT_RESET 清运行态。
  引擎 `done` 会保持到下一次 `start` 才清零，因此发出 `start` 的那一拍不消费 `done`，避免新任务复用上一笔结果。
- `cop_ctrl_regs`：DONE/ERROR/RESULT_VALID 为 sticky；核写 `CLEAR_DONE/CLEAR_ERROR/CLEAR_RESULT_VALID` 执行 W1C。
- `cop_axi_lite_frontend`：单 outstanding；AW/W 独立收集；后端完成才返回响应；不支持 burst。
- `cop_top`：组装上述模块和现役 `cnn_sequencer`；PS 仅可发 ABORT/SOFT_RESET，不可发 START。
- `soc_top`：参数 `ENABLE_COP=0` 默认关闭；关闭时地址解码与接入前一致，不改变核 decode/流水语义。

## 4. 已验证矩阵

| 项目 | JL 证据 | 结论 |
|---|---|---|
| 各新增模块正常一笔 | 上述独立入口、退出码 0 | 冒烟 PASS |
| 最小端到端 | `cop_top`：配置→载入→START→busy→DONE→结果→W1C | PASS |
| 连续两笔任务不误完成 | `cop_top` 第二次 START 后 20 拍仍 `busy`/`WAIT_ENGINE`；去掉保护拍负向对照立即 FAIL | PASS |
| J02 zero 黄金 | 9225 packed words/73795 elements；logits `04fd02` | 逐元素 PASS |
| 协处理器集合 | `run_coprocessor_iverilog.sh all`，退出码 0 | PASS |
| 默认关闭核回归 | `run_iverilog.sh soc`，first=13/1101，second=65/0001 | PASS |
| RV32I 工单固件 | `firmware` 构建 ELF/hex/dis + 主机规则测试 | PASS |

最终原始输出与退出码：`data/logs/2026-10-19-j04-closeout/{cop_top,all}.{log,exit_code}`。

## 5. 未验证矩阵与接手方法

| 未验证项 | 接手人 | 手段 / PASS 判据 |
|---|---|---|
| 完整 CDC 相位、复位、连续任务扫描 | RTL 验证队友 | 扩展 mailbox/top TB；无丢单、撕裂、误 ACK，全部断言 PASS |
| AXI AW/W 相位、B/R 背压、非法响应矩阵 | RTL 验证队友 | 扩展 `tb_cop_axi_lite_frontend.v`；协议 checker 零错误 |
| payload 各 bank 物理地址适配与结果 DMA | SoC 集成队友 | 接真实 BRAM/DataMover；逐字节与 C02 payload/result 黄金一致 |
| 全仓回归、四档 CoreMark、arch-test | 核验证队友 | `run_iverilog.sh all` 与规定矩阵退出 0，无历史回归退化 |
| XSim、综合、实现、资源、WNS/Fmax、DRC、bitstream | NC/FPGA 队友 | Vivado 原始报告达冻结门槛，无 critical warning 漏审 |
| PYNQ、网口/串口、实机上板 | NC | 按 J08 包运行并返回日志、版本、位流/模型 SHA256 |
| 正式 PTQ/QAT、真实精度与真实黄金 | JL 后续 J05/J06 | 真实留出集报告和正式 manifest；本 J04 包不替代 |

## 6. 队友待办（按优先级）

- **P0-1 第一条**：在干净 worktree 先运行第 1 节一键冒烟命令；以退出码 0、所有既有
  `PASS:` 行和 zero 黄金 `logits=04fd02 class=2 margin=2` 为接手基线。
- **P0-2 数据面落地**：在 `cop_top` 的 loader store 接口后接 C02 物理 bank/地址适配，并接结果
  DataMover；增加真实 payload build→load→逐 bank/结果逐字节比对，完全一致才 PASS。
- **P0-3 CDC/AXI 深测**：在 mailbox/top/AXI TB 增加异步相位、复位、pending 第二写、AW/W
  排列和 B/R 背压；第一笔不变、第二笔零副作用、无协议错误才 PASS。
- **P0-4 配置失效规则**：JL 已按 OPEN-3 的保守默认实现并加撤销用例；队友仍需冻结撤销时点，
  并补模型地址/长度/CRC 与 ROI 配置更新的逐字段矩阵。
- **P1**：跑全仓 `run_iverilog.sh all`、CoreMark/arch-test 矩阵；保存原始日志和退出码。
- **P2**：跑 XSim/Vivado/时序/资源/DRC/bitstream，最后由 NC 上板；必须记录源码、位流、
  固件和模型 SHA256，不能用本交接单代签。

## 7. OPEN（保守默认与影响面）

- **OPEN-1 payload bank 适配**：当前 loader 导出 word/address/keep，顶层 TB 用 J02 memory model；
  默认不宣称已写入实体 BRAM。影响模型装载、综合资源和实际推理。
- **OPEN-2 结果外搬**：当前结果在本地 16×16-byte 窗口读回，尚未写 `RESULT_ADDR`；默认固件
  轮询窗口，不宣称结果 DMA 完成。影响 PS 大批量结果读取。
- **OPEN-3 配置改变后的 VALID 撤销**：C03 未逐字段冻结撤销时点。JL 侧已按保守默认实现：
  `CFG_SEQ != CFG_APPLIED` 立即撤销 `MODEL_VALID/ROI_VALID`，`CFG_COMMIT` 后必须重新装载才置位，
  `CFG_VALID = (CFG_APPLIED==CFG_SEQ && fields_valid)`；`cop_config_regs`/`cop_top` 均有撤销用例。
  仍需队友冻结撤销时点后才能依赖该行为。影响跨模型/ROI 重配置。
- **OPEN-4 返回路径 CDC**：命令邮箱按稳定 payload+toggle；状态/多位返回仅冒烟，未完成全相位
  证明。默认固件轮询稳定两次并以 RESULT_SEQ 变化为提交点。影响极端相位可靠性。
- **OPEN-5 IRQ/IRQ_ACK**：本轮未生成可签收的 PS IRQ 链；默认轮询 STATUS，不宣称中断可用。
  影响 PS 驱动方式，不影响已测轮询流程。
- **OPEN-6 FW_DECISION 布局**：固件暂用 `[31:16] seq/[15:8] reasons/[7:0] verdict`；默认仅由
  共用头文件读写，WC 冻结前禁止外部硬编码。影响 WC 协议解析。
- **OPEN-7 AXI/CDC/综合深度**：只做正常一笔与关键拒绝冒烟；默认所有未覆盖情形均标
  UNVERIFIED，不能外推 Vivado、100 MHz 或板端结论。
- **OPEN-8 组合 RAM 读告警**：Icarus 对 shadow/result memory 报敏感列表告警；默认保留行为，
  不据此宣称 BRAM 推断。影响综合资源/时序，交给 Vivado 报告判定。
- **OPEN-9 只读常量未实现**：`VERSION(0x004)`、`CAPABILITY(0x008)`、`ERROR_CODE(0x014)` 当前
  读回固定 0；C03 §4 只给语义、未冻结位图与错误码编码，本轮不臆造取值。WC 驱动冻结前不得把
  0 当作合法版本/能力位，也不得据 0 判断错误原因。影响驱动版本协商与错误定位。
- **OPEN-10 PS 空闲 ABORT**：`CTRL.ABORT` 未加 busy 门禁，空闲时写入会置 `STATUS.ERROR`
  但不产生任务错误脉冲，与 §3.1.1「非驻留拒绝」口径不一致；本轮保留该行为未改，服务停止流程
  需自行按 STATUS 判读。影响停止/恢复流程的错误计数。

每个 OPEN 的补测位置和 PASS 判据均在第 5/6 节给出；不得用“仿真冒烟 PASS”覆盖其状态。

## 8. 本次流程例外与责任边界

用户明确覆盖仓库逐题理解门槛：本次一次性收口不逐题等待；仍保持每提交不超过 100 行、
每步独立 TB + `all`、只做本地 commit、不 push。未执行 merge、tag 或破坏性 git 操作。

**J04 实现完成 ≠ 完整验证通过 ≠ 板级验收。** 本轮未做完整回归矩阵、穷举负例、CDC
全场景扫描、XSim/Vivado、综合实现、bitstream 或上板；JL 只对本单列出的离板冒烟证据负责，
不代 WC/NC/验证队友签字。
