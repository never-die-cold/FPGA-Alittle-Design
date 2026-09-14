# sim —— 仿真脚本与结果

各模块 testbench、仿真脚本与波形结果。**所有 RTL 模块必须先过仿真再上板。**

## 规划结构

```
sim/
├── riscv/           # RISC-V 核各级与整核 testbench
├── coprocessor/     # 协处理器 testbench
├── vision/          # 预处理流水线 testbench（含测试图样生成）
├── soc/             # SoC 级联调仿真
├── scripts/         # xsim 批处理脚本（可复跑）
└── tools/           # 辅助工具（RV32I 编解码自测等）
```

辅助工具用法：`python sim/tools/verify_rv32i.py`（阶段 0 指令编码自测：22 组汇编→机器码 + 10 组反汇编双向校验，输出 `ALL OK` 即通过）

## 仿真工具（过渡约定，2026-09-11）

- **过渡期**（Vivado 未安装，issue #2）：统一用 **Icarus Verilog 13.0**（MSYS2 ucrt64 包 `mingw-w64-ucrt-x86_64-iverilog`）跑 RTL 仿真
- **Vivado 到货后**：XSim 跑同一套 tb 复核，两工具结论须一致
- 用法（MSYS2 UCRT64 shell 中）：
  - 一键跑全部 tb：`bash sim/scripts/run_iverilog.sh`（编译 `src/riscv/*.v` + `sim/riscv/tb_core_*.v`，产物在 `sim/build/`）
  - `tb_core_smoke.v`：加载 `src/riscv_fw/hello_v0.hex`，检查 `tohost==13 && tohost_exit==0`（程序级冒烟）
  - `tb_core_test.v`：加载 `src/riscv_fw/hello_test.hex`，检查 `tohost_exit==0`（RV32I 逐指令自检 38 用例；失败值为用例编号）
- tb 接口以 [`src/riscv/design_v0.md`](../src/riscv/design_v0.md) 为唯一权威

> 当前状态：v0 核（RV32I）两个 tb 均 PASS（2026-09-11），见 `report/llm_log/2026-09-11-riscv-v0-rtl.md` 与逐指令 tb 记录

## 约定

- 每个 testbench 输出 PASS/FAIL 自检结果，禁止只靠肉眼看波形
- 关键波形截图归档到 `report/`，供设计报告引用
- 黄金参考数据放 `data/`，仿真比对脚本引用相对路径

> 状态：🚧 进行中（v0 核 RV32I 已过冒烟与逐指令自检）
