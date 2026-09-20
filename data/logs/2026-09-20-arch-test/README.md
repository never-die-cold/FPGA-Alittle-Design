# riscv-arch-test 接入证据（2026-09-20）

> 用途：v0 核 RV32I 子集先行的架构测试回归——编译 → 仿真 → 签名比对全链路证据；
> 与 self-check tb 互补：**「优化不改语义」的第三方判据**（Part B/C 改动后必须重跑）。
> 步骤文档与跑法见 [`sim/README.md`](../../../sim/README.md)；本次为首次接入。

## 套件与目标配置

| 项 | 值 |
|:---|:---|
| 套件 | [riscv-non-isa/riscv-arch-test](https://github.com/riscv-non-isa/riscv-arch-test) `old-framework-2.x`（自带 `references/*.reference_output` 参考签名，无需额外 ISS） |
| 套件版本 | `6f7f47b`（浅克隆；获取：`bash sim/scripts/fetch_arch_test.sh`，不入库，见 .gitignore） |
| 目标配置 | `sim/arch_test/target/pynq_z2_v0/`（`model_test.h` + `env/link.ld` + 框架 Makefile 配置） |
| 被测版本 | v0 两级流水核（`src/riscv/*.v`，与 main@`6c324fb` 一致） |
| 工具 | riscv32-unknown-elf-gcc 14.2.0 / iverilog 13.0 / MSYS2 UCRT64 |

## 机制

1. `make`（框架 `compile_template` + 本仓库 target 配置）编译测试源 → ELF；
2. `run_arch_test.sh` 从 ELF 符号表取 `begin_signature`/`end_signature` 地址，objcopy→bin→hex；
3. `tb_arch_test.v` 将统一镜像**同时预载 imem 与 dmem**，跑固定周期（默认 200000）后读签名区；
4. 逐字与 `references/<test>.reference_output` 比对，写 `.signature.output`（兼容框架 `make verify` 的文件约定），PASS/FAIL 自检。

## 结果（RV32I 子集，3 个测试全过）

| 测试 | 覆盖点 | 签名区 | 参考字数 | 结果 | 原始日志 |
|:---|:---|:---|:---:|:---:|:---|
| `add-01` | ADD（R 型算术，边界值/符号组合） | `80003250..80003b80` | 588 | ✅ PASS | `run_add-01.log` |
| `addi-01` | ADDI（I 型立即数） | `80002190..80002a60` | 564 | ✅ PASS | `run_addi-01.log` |
| `and-01` | AND（按位逻辑） | — | 584 | ✅ PASS | `run_and-01.log` |

## 复跑方法

```bash
bash sim/scripts/fetch_arch_test.sh          # 首次：下载套件（或设置 ARCH_TEST_DIR）
bash sim/scripts/run_arch_test.sh add-01     # 单测：编译 + 仿真 + 签名比对
bash sim/scripts/run_arch_test.sh addi-01
bash sim/scripts/run_arch_test.sh and-01
```

## 边界与后续

- 参考签名来自套件自带 `references/`（生成自 Spike/CTF 流程），非本机 ISS——依赖套件版本可追溯（记录 commit）
- 本次仅 RV32I 的 I 算术/逻辑子集；load/store、跳转、M/C/Zifencei、privilege 后续按需纳入（`device/` 只启用 I）
- 未覆盖非对齐访问与特权态（v0 契约：工具链保证对齐、无异常支持）；套件对未对齐测试有官方免责声明
- 固定运行周期（200000）：HALT 为自旋，不依赖停机检测；周期数不足会表现为签名不匹配（可调 `ARCH_TEST_CYCLES`）

## 关联

- `report/llm_log/2026-09-20-arch-test-integration.md`（接入过程 + 理解门槛）
- `sim/README.md` §riscv-arch-test
