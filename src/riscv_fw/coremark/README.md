# src/riscv_fw/coremark —— CoreMark 移植与构建

> 契约：`docs/coremark_tb_contract.md`（接口/观测/判据唯一口径）
> 计划：`docs/coremark_plan.md` 阶段 C/D

## 目录

| 路径 | 内容 | 规则 |
|:---|:---|:---|
| `vendor/` | EEMBC 官方源码原样入库（commit `1f483d5b`，2025-05-01） | **禁止改动**；算法文件与 `coremark.h` 永不改 |
| `core_portme.c/h` | 本核移植层（D1/D2，已实现） | 无 libc；`get_time()` 读取 `0x8000_8000`，仿真由 tb 计数器模拟 |
| `core_main.c` | 官方 `core_main.c` 派生副本（D3，已实现） | 仅加结果导出钩子；diff 入证据 |
| `link_coremark.ld` | 32KB 链接布局（C3，已实现） | 排除观测块 `0x8000_7F00–0x7FFF` 与 `tohost` |
| 构建 | `Makefile` 的 `coremark` 目标（C3，已实现） | 产出 `coremark.hex/.dis`，固定 2K/32 迭代 profile |

## 固定 profile（契约 §4.1 / 计划 C4）

- `TOTAL_DATA_SIZE=2000`（2K performance）、seeds `0/0/0x66`、`ITERATIONS=32`、三算法全跑、`MEM_STATIC`
- `HAS_FLOAT=0`、`HAS_TIME_H=0`、`MAIN_HAS_NOARGC`；编译 `-march=rv32im -mabi=ilp32 -mcmodel=medany -mno-relax -O2 -ffreestanding -nostdlib -nostartfiles`

## 证据

- 上游 commit / 逐文件 SHA-256 / 规则：`data/evidence/2026-09-23-coremark-source.md`
- 观测块字段表与结束协议：契约 §4.3 / §4.4；判据：契约 §5
- 回归入口：`bash sim/scripts/run_iverilog.sh coremark`；完整运行条件与 PASS 证据：`data/logs/2026-09-23-coremark/`
- SoC 板上计数器及 DMEM 镜像预载仍未实现；当前跑分为 iverilog 仿真外推口径。
