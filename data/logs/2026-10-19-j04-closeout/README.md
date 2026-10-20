# J04 离板冒烟证据（JL Linux + Windows 复跑）

> 基线：`dev/riscv` @ `7d6355b`；本目录的 Windows 记录由 J04 审查修复生成，修复提交以 `git log` 为准。
> 状态：J04a（JL 侧实现/冒烟）已交接；J04b（完整验证、物理 bank/结果 DMA、CDC/AXI 深测、综合/板验）未完成。详见[实现交接单](../../../docs/runbooks/coprocessor-j04-handoff.md)。

## 1. 命令与环境

Windows/MSYS2 使用 `C:\\msys64\\usr\\bin\\bash.exe`，PATH 加 `/ucrt64/bin` 与 Python 3.12：

```bash
export PATH=/ucrt64/bin:/usr/bin:/c/Users/ASUS/AppData/Local/Programs/Python/Python312:$PATH
COPROCESSOR_PYTHON=python RISCV_CROSS=riscv32-unknown-elf- bash sim/scripts/run_coprocessor_iverilog.sh all
COPROCESSOR_PYTHON=python RISCV_CROSS=riscv32-unknown-elf- bash sim/scripts/run_coprocessor_iverilog.sh cop_top
COPROCESSOR_PYTHON=python RISCV_CROSS=riscv32-unknown-elf- bash sim/scripts/run_coprocessor_iverilog.sh firmware
bash sim/scripts/run_iverilog.sh soc
make -C src/riscv_fw CROSS=riscv32-unknown-elf- PYTHON=python cop_job.hex cop_job.dis
```

本目录的日志与退出码由 [windows-rerun.sh](windows-rerun.sh) 生成；只重跑其中几项就把名字当参数：
`bash data/logs/2026-10-19-j04-closeout/windows-rerun.sh cop_top firmware soc`（不带参数跑全部四项）。

工具版本见 [windows-environment.txt](windows-environment.txt)。JL Linux 的原始记录为
[all.log](all.log)、[all.exit_code](all.exit_code)、[cop_top.log](cop_top.log)、
[cop_top.exit_code](cop_top.exit_code)。

## 2. 结果

| 运行 | 退出码 | 关键输出 |
|---|---:|---|
| JL Linux 协处理器 `all` | 0 | 见 `all.log`；J02 zero logits=04fd02（修复前基线 `7d6355b`） |
| JL Linux `cop_top` | 0 | 见 `cop_top.log`（修复前基线 `7d6355b`） |
| Windows 协处理器 `all` | 0 | [windows-all.exit_code](windows-all.exit_code)；全部既有 PASS |
| Windows `cop_top` | 0 | [windows-cop_top.exit_code](windows-cop_top.exit_code)；AXI/J02/DMA error/ABORT/SOFT_RESET PASS |
| Windows `firmware` | 0 | [windows-firmware.exit_code](windows-firmware.exit_code)；RV32I ELF 构建 + 主机规则测试 PASS |
| Windows `run_iverilog.sh soc` | 0 | [windows-soc.exit_code](windows-soc.exit_code)；first=13/1101，second=65/0001 |
| Windows 核 20 个 TB + 协处理器 `all` | 中止（非失败） | [windows-core-20tbs.partial.log](windows-core-20tbs.partial.log)：72 个 `PASS`、0 个失败；之后进入 CoreMark 四档基准的长仿真，本轮主动中止，**不声称全仓单次跑完** |
| Windows `run_coprocessor_python.sh all` | 0 | [windows-cop-python.log](windows-cop-python.log)；整数算子/网络 Python 参考 |
| Windows `run_vision_iverilog.sh all` | 0 | [windows-vision-rtl.log](windows-vision-rtl.log)；28 个视觉 RTL `PASS` |
| Windows `run_vision_python.sh` | 0 | [windows-vision-python.log](windows-vision-python.log)；需 PATH 里有 `git`（打包用例调 `git rev-parse`） |
| Windows `cop_top` 负向对照（去掉 done 保护拍） | 1 | `FAIL second task finished early busy=0 state=0 seq=2`；证明该用例能判别旧缺陷 |

## 3. 失败与修复

1. 首次 Windows `all` 退出 4：Icarus 13 在 `cop_top.v` 报 `load_kind`、`loader_crc32`、
   `weight_crc32` “declared after use”。原因是 `wire model_crc_error=...` 在依赖声明之前初始化；
   已把声明与 `assign` 拆开并移到依赖声明之后。修复后 `cop_top` 与 `all` 均退出 0。
   该失败说明“JL Linux 通过”不等于“Windows 可复现”；R02 的 portability 修复即为此。
2. 连续两笔任务：引擎 `done` 保持到下一次 `start` 才清零，而 `cop_task_ctrl` 在进入
   `WAIT_ENGINE` 的第一拍就采样 `engine_done_i`，于是第二笔任务用上一笔的 `done` 瞬间“完成”
   并回写旧结果（负向对照：`busy=0 state=0 seq=2`，日志见第 2 节末行）。已在启动当拍不消费
   `done`，并在 `tb_cop_task_ctrl` 加遗留 `done` 用例、在 `tb_cop_top` 加“第二次 START 后
   20 拍仍 busy”断言。
3. `run_vision_python.sh` 曾因 `sim/scripts/make_arm_localize_pkg.py` 仍指向 `docs/arm-localize-runbook.md`
   （该文件已迁到 `docs/runbooks/`）而失败；已改路径。另需 PATH 里有 `git`，否则打包用例报
   `FileNotFoundError`。
4. Windows 上用 `pwsh` 包 `bash.exe` 且把 stderr 并到 stdout 时，PowerShell 会把 iverilog 的
   `-Wall` 告警记成 `NativeCommandError`，使外层退出码变 1——**判据以脚本自身退出码为准**
   （本目录的 `.exit_code` 文件由脚本 `$?` 写入，不受该影响）。
5. 独立审查指出：启动保护只挡了遗留 `done`，没挡遗留 `error`——上一笔超时/出错后 `engine.error`
   保持到下一次 `start`，W1C 后重试会在第一拍被旧 `error` 误杀（任务层报错、引擎刚开始跑）。
   已对称加保护；`tb_cop_task_ctrl` 增加“遗留 error 后重试仍能跑完”和“启动后真出错”两段，
   负向对照去掉保护即 `$fatal`。同轮还修了 `windows-rerun.sh` 吞退出码、
   `%.dis` 规则用管道掩盖 objdump 失败、以及 §2 指纹漏更新（Makefile 一项）。

## 4. 固件产物

| 产物 | 行数 | SHA256 |
|---|---:|---|
| `src/riscv_fw/cop_job.hex` | 4094 | `04df882158857beb694063aa5c56442ce449d07f29487a57ceffc20ed5ad12fe` |
| `src/riscv_fw/cop_job.dis` | 286 | `0abcb4ad3da8d297142dcaeb27410ad628c13cef858247fffb0a827b21635a89` |
| `src/riscv_fw/cop_job.elf` | — | `2a6d78bb87eaf22002b6a31c0fd2952cbc6585434890fe1ec62a0407ecaf14f0`（不入库） |

`cop_job.hex/dis` 由 `riscv32-unknown-elf-` 生成，生成脚本固定写 LF（`bin2hex.py` 用 `newline="\n"`，
`%.dis` 规则过 `tr -d '\r'`），否则 Windows 默认换行转换会让入库指纹随平台变化。
`cop_job.elf` 只记录哈希，不提交。若再改固件，以上哈希与交接单 §2 指纹需同步重建。

## 5. 边界

- 未运行 Vivado、综合、实现、bitstream；未上板。
- 全仓 `run_iverilog.sh all` 没有单次跑完：核 20 个 TB、协处理器 `all`、协处理器 Python、视觉 RTL、
  视觉 Python 均已单独跑过且退出 0，CoreMark 四档基准与 `v1_*` 变体本轮未重跑（本次未改核 RTL）。
- `cop_top`/DMA 仅用 J02 诊断权重与内存模型；物理 bank/结果 DMA 仍是 OPEN-1/2。
- `VERSION`/`CAPABILITY`/`ERROR_CODE` 仍读 0（OPEN-9）；PS 空闲 ABORT 未按非驻留拒绝处理（OPEN-10）。
- 本证据不改变 J04b 状态，也不代表 M2/M3 验收；`prototype`/诊断黄金不能写成硬件识别。
