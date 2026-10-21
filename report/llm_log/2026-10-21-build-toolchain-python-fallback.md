# [2026-10-21] 协作记录：工具链前缀传播、Python 路径稳定与裸命令事实

> 标签：#build #toolchain #环境 #回归 #可复现
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`09fbebf` `8317fa6`

## 1. 任务与初始提示词

缺陷 1：`run_coprocessor_iverilog.sh all` 在某机器失败——只有 `riscv64-unknown-elf-` 时，
`firmware-rules/build.log` 报 `riscv32-unknown-elf-objdump: not found`，`all` 中途终止。
要求：父脚本调用子脚本前传 `RISCV_CROSS`；子脚本自己也做 riscv64 回落；两者都不可用时
显式 SKIP 并打印原因；验收是 `all` 完整跑完并退出 0，最后一项是 `run_network` 的 PASS。

## 2. 模型第一版方案

父脚本同时检查 `gcc/objdump/objcopy`，缺失则回落到 riscv64，并 `export RISCV_CROSS`；
`test_firmware_rules.sh` 独立执行同样的回落；都不可用时打印 `SKIP` 并返回 0。
另外把含 `/` 的 `COPROCESSOR_PYTHON` 规范化为绝对路径，避免 `make -C src/riscv_fw` 后相对路径失效。

## 3. 失败现象

1. 父脚本只在 `gcc` 缺失时回落且未 export，子进程仍读默认 `riscv32-unknown-elf-`，
   `objdump: not found`，`all` 假红/中途终止。
2. 修复工具链后，`COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python` 在
   `make -C src/riscv_fw` 后变成相对错误路径，退出 2。
3. 不带任何环境变量的裸命令 `bash sim/scripts/run_coprocessor_iverilog.sh all`
   仍因系统 `python3` 缺 NumPy 在 `firmware_e2e` 生成 golden 时退出 1。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 子进程仍用 riscv32 | 环境变量未跨进程 | 父脚本 export + 子脚本回落 | 子进程用 riscv64 |
| 2 | 无任何工具链 | 不能制造假失败 | 显式 `SKIP` 并打印原因 | `all` 不假红 |
| 3 | venv 相对路径退出 2 | `make -C` 改变 cwd | 启动时规范化为绝对路径 | `all` 继续 |
| 4 | 裸命令退出 1（NumPy） | 环境事实，不是测试失败 | 保留记录，checkpoint 写明需显式 venv | 双事实并存 |

## 5. 最终结论

可复现门禁命令：

```bash
RISCV_CROSS=riscv64-unknown-elf- \
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
bash sim/scripts/run_coprocessor_iverilog.sh all
```

退出 0，最后一条为 zero 的 `9225 packed words/73795 elements match integer network`。
裸命令仍退出 1（系统 Python 缺 NumPy），已登记 OPEN-ENV-1，不隐藏、不改测试凑 PASS。

## 6. 经验沉淀

- 触发条件：父脚本选好工具链，子脚本/`make -C` 里又按默认值重新选。
- 排查步骤：把前缀显式 export 或命令行传入；子脚本独立回落；相对路径在 `cd` 前转绝对；
  无工具链时 SKIP 并写原因，不制造假红/假绿。
- 适用范围：所有多进程回归入口；换 CI 镜像仍要复测。
#skill候选
