# J04 协处理器实现交接单

> 状态：JL 侧“实现 + 可交接”收口；不等于完整验证通过或板级验收，JL 不代 WC/NC 签字。
> 源码锚点：分支 `codex/night-2026-10-18`，功能 HEAD `9fdd035`；最终文档 HEAD 以 `git log -1` 为准。

## 1. 一键冒烟与独立入口

仓库根目录执行：

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh all
```

独立入口均使用同一前缀：`mmio_gate`、`ctrl_regs`、`mailbox`、`config_regs`、
`dma_loader`、`task_ctrl`、`axi_lite`、`firmware`、`cop_top`。例如：

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh cop_top
```

TB 内用任务组织激励，用常量/J02 生成文件作参考，并用独立断言比对；新增用例应只追加激励和期望，
不得放宽既有断言。`cop_top` 的刺激任务为 `ps_wr`/`ps_rd` 与 DMA stream，黄金由 J02
`generate_network_vectors.py` 生成，结果逐字段比对。

## 2. 交付文件指纹

`行数 SHA256 文件`：

```text
43 82f44ec0627728ab287e693a0124966a2d7b78280ae21f8f06ac7efd1a3a2ca2 src/coprocessor/cop_axi_lite_frontend.v
46 15aff88321fab1130bbc189e438beabe4061e598eccbe13c7c3b313ebe0bb0e2 src/coprocessor/cop_cdc_mailbox.v
61 bab581f6767d0044873635e86f2f960e1caaa7266346b31a70393ae7b8e9544c src/coprocessor/cop_config_regs.v
65 caa57cc8bf0fe5ac442847adae18a793532d31c7af4fe47da7468f9f40e50874 src/coprocessor/cop_core_mmio_gate.v
46 f2d5506fc7084f34b99db7090028bc14cdbbc2695f7bf8e4bb76bab5b6908e6a src/coprocessor/cop_ctrl_regs.v
61 18db51c0fada9c8d15f42a9d57192b2d3a9a2a81073a2452d6447dcd7335bf28 src/coprocessor/cop_dma_loader.v
55 1e903e2c94dc616647641484c661c8bd942e3cbbc632265c65695974f511e215 src/coprocessor/cop_task_ctrl.v
187 8a67ff5d537fbd4ecb5c86a34a900fff16ebbcc2b24c125d59e65bc79e329c01 src/coprocessor/cop_top.v
147 071a4f197a4651b0da26645b46a65c166bccbacc77c88b2b4f21b4abce69a591 src/coprocessor/cnn_sequencer.v
81 22f8b5d3e70bb51f135a0ae52b59879b14c5f90ce78ac70a1d878ae8682afe9b src/riscv/soc_top.v
52 7a1d067eaaac1cb5ee17eae49132f7c0bb649f4cd39c882ec87122d7969cebbd src/riscv_fw/cop_job.c
35 1692bb7235424dfce0a3877256a910a16834f9411d21a133cc1c305f61d95ee6 src/riscv_fw/cop_work_order.h
78 0e7708050fb5d5b1651594314c31311dbb5824eeb1bf277c97db6ed5b92dd042 src/riscv_fw/Makefile
26 ed9fed691756d69a25ad823d41b1fdc31ac14393912248614288538e01f2ae2a sim/coprocessor/tb_cop_axi_lite_frontend.v
34 66133a217901355f313e76369dca62e035790aa92e748a5e5625b10250090e2e sim/coprocessor/tb_cop_cdc_mailbox.v
32 9f3aa23ef7940657715500dcf393b50b001cdda0ac68f68bb477dd09ea5a0b47 sim/coprocessor/tb_cop_config_regs.v
49 50bfb8057e8f87eb90637ab61f0085e88a91a30107a24f789f1b6ef7500a2466 sim/coprocessor/tb_cop_core_mmio_gate.v
57 0064461f55c00473c5612b5f689942a0cea64ee99a561abec83b6b639de93297 sim/coprocessor/tb_cop_ctrl_regs.v
29 1b57950f2165727cbdbe43172884aa9f4baf15ac7ebce3ff9dca9d58e2705cc2 sim/coprocessor/tb_cop_dma_loader.v
31 20ae79bc4a37e902e8995ea12d3740deac28d356301d0e2583ef2078d11baa1b sim/coprocessor/tb_cop_task_ctrl.v
130 be290730d5dca5dc1bb833f928f857bcd5edc74583f3f2c0306818d7a7008b6d sim/coprocessor/tb_cop_top.v
163 a66ca4bbad1336f4ab7f2984fb634b92a7b62faec99b11d60a9d641f3c0623e5 sim/coprocessor/tb_cnn_sequencer.v
87 aed7264e972652da38b0815f37a47c48b12e7daaf2a7953e93e71ab749f5489c sim/scripts/run_coprocessor_iverilog.sh
```

## 3. 模块接口与时序约定

- `cop_core_mmio_gate`：本地无等待口；仅 `be=4'b1111` 整字写。`hit` 表示窗口归属，非法访问仍 hit 并读 0、零副作用。
- `cop_cdc_mailbox`：源侧至多一笔 pending；稳定 payload + toggle 请求，目标接受后 toggle ACK；ACK 不代表 CNN 完成。
- `cop_config_regs`：PS 写 shadow，`CFG_COMMIT` 原子复制 applied；运行任务只读 START 时快照。
- `cop_dma_loader`：valid/ready stream，按 keep 计数并计算 CRC32；短包、超长或 CRC 不符不得置对应 VALID。
- `cop_task_ctrl`：按 target 顺序启动；16-byte 结果项最后提交；ABORT 回 IDLE，SOFT_RESET 清运行态。
- `cop_ctrl_regs`：DONE/ERROR/RESULT_VALID 为 sticky；核写 `CLEAR_DONE/CLEAR_ERROR/CLEAR_RESULT_VALID` 执行 W1C。
- `cop_axi_lite_frontend`：单 outstanding；AW/W 独立收集；后端完成才返回响应；不支持 burst。
- `cop_top`：组装上述模块和现役 `cnn_sequencer`；PS 仅可发 ABORT/SOFT_RESET，不可发 START。
- `soc_top`：参数 `ENABLE_COP=0` 默认关闭；关闭时地址解码与接入前一致，不改变核 decode/流水语义。

## 4. 已验证矩阵

| 项目 | JL 证据 | 结论 |
|---|---|---|
| 各新增模块正常一笔 | 上述独立入口、退出码 0 | 冒烟 PASS |
| 最小端到端 | `cop_top`：配置→载入→START→busy→DONE→结果→W1C | PASS |
| J02 zero 黄金 | 9225 packed words/73795 elements；logits `04fd02` | 逐元素 PASS |
| 协处理器集合 | `run_coprocessor_iverilog.sh all`，退出码 0 | PASS |
| 默认关闭核回归 | `run_iverilog.sh soc`，first=13/1101，second=65/0001 | PASS |
| RV32I 工单固件 | `firmware` 构建 ELF/hex/dis + 主机规则测试 | PASS |
