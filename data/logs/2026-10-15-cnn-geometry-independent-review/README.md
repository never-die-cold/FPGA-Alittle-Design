# CNN 输出尺寸位宽优化（第 1 步）：独立复核（2026-10-15）

基线 `dev/model@891cba2`。本目录由第二个会话（ZCode）做独立交叉验证，
不修改 `src/`、`sim/`、归口证据目录的任何文件，也不提交。
第 1 步的设计、实现与归口结论仍以 `../2026-10-15-cnn-geometry-step1/` 和
`report/llm_log/2026-10-15-cnn-geometry-step1.md` 为准；本目录只记录"另一个人重跑/复算"的结果。

## 受核对象

| 对象 | SHA256 | 备注 |
|---|---|---|
| `src/coprocessor/conv_engine.v`（改后） | `f7fb3878…12b9ac7` | 与 `../2026-10-15-cnn-geometry-step1/verification-inputs.json` 一致 |
| `src/coprocessor/conv_engine.v`（`HEAD`，改前） | `2a474208…08f308e9b5` | 9155 字节，与 10-13 OOC 输入及 `baseline-ooc-input-check.json` 一致 |
| `sim/coprocessor/tb_conv_engine.v` | `6146c7c2…334ab0a` | 528 例几何任务所在版本 |
| `sim/build/coprocessor/conv-vectors/cases.txt` | `35d9cf7a…d1993de7` | 向量清单，由归口会话 20:59 生成，本次只读复用 |

原始哈希文件：`rtl-tb.sha256`、`old-conv-engine.sha256`、`vector-cases.sha256`。

## 本次独立执行

独立 `iverilog -g2001 -Wall` 编译 + 独立 vvp/日志路径（避免与并行会话共用 `sim/build` 输出互相覆盖）。
工具：Icarus Verilog 13.0 stable。

| 运行 | 被测 RTL | 命令要点 | 退出码 | 结果 |
|---|---|---|---|---|
| `compile.log`（0 字节） | 改后 | `-Wall -s tb_conv_engine` | 0 | 无告警 |
| `run-padding_tail.txt` | 改后 | `+case=…/padding_tail +fault_tests` | 0 | PASS×3：用例 + **528 例启动/几何** + 故障恢复 |
| `run-conv1.txt` / `run-conv2.txt` | 改后 | 各用例单跑 | 0 | PASS，逐像素与 Python 一致 |
| `compile-old.log`（0 字节） + `run-oldrtl-padding_tail.txt` | `HEAD` 改前 | 同一 tb、同一批参数 | 0 | PASS×3 |

整网层级（`tb_cnn_sequencer`，同一 independent 编译 + `+fault_tests`）：

| 运行 | 用例 | 退出码 | 结果 |
|---|---|---|---|
| `run-network-pattern.txt` | `+case=…/pattern` | 0 | PASS 9225 words / 73795 elements 与 integer network 全等，logits=`01fd01` class=0 margin=0 cycles=1123109；含失效参数/watchdog/复位/重新运行 |
| `run-network-zero.txt` | `+case=…/zero` | 0 | PASS 同上规模全等，logits=`04fd02` class=2 margin=2 cycles=1123109 |

三者共同给出的一句话：**改前、改后两份 RTL 对同一独立 integer oracle 全部 PASS，且
words/reads/cycles 完全相同**（padding_tail 36/216/2535；conv1 2048/9216/108715；conv2 4096/36864/410966），
即本步在覆盖范围内是行为等价改写，未改变吞吐。

过程更正留痕：首次提取 `HEAD` 版本时被工作区文件覆盖（哈希核对发现仍为 `f7fb3878…`），
重做后才得到 `2a474208…`；上表与 `old-conv-engine.sha256` 均为重做后的记录。

## OOC 对比（数字取自报告，本次未重跑综合）

基线 `../cnn-ooc-5c9bc74c61e7445ca8c56b2f49389102/reports/`；
本步 `../cnn-ooc-da63cadcd3db4a9e9f826cf2e4949e68/reports/`（归口会话运行，退出 0）。

| 指标 | 10-13 基线 | 本步 | 变化 |
|---|---|---|---|
| WNS (ns) @100 MHz | +0.058 | **+0.118** | +0.060 |
| WHS (ns) | +0.049 | +0.051 | +0.002 |
| TNS / 失败端点 | 0 / 0 | 0 / 0 | 时序约束全满足 |
| Slice LUTs | 10100 | 9955 | −145 |
| LUT as Logic | 9844 | 9699 | −145 |
| CARRY4 | 1478 | 1452 | −26 |
| Slice Registers | 6940 | 6940 | 0 |
| DSPs | 192 | 192 | 0 |
| Block RAM | 0 | 0 | OOC 为外置存储端口 |
| DRC | 593：DPIP-1 432 / DPOP-1 32 / DPOP-2 128 / ZPS7-1 1 | 完全相同 | 无新增告警 |

临界路径身份变化（本次独立发现，最关键的一条）：

- 基线 top-10 全部是 `layer_reg[2]` → `engine/` 的几何寄存器（`ow_reg`/`ox_reg`/`ky_reg`/`error_reg`），
  16–18 级逻辑、10–11 个 CARRY4，最差 9.889 ns → 正是 `output_size` 参与的比较链。
- 本步 top-10 全部换成 `limit_reg[6]` → `engine/accumulators_reg|multipliers_reg` 的 `CE`，
  11–12 级逻辑、6 个 CARRY4，最差 9.593 ns。
- 也就是：改动瞄准的几何路径已被压出前 10，当前瓶颈是与 `cfg_cycle_limit` 相关的超时比较链，
  与归口会话记录的下一步（超时比较）顺序一致。

新瓶颈路径的构成（观察，供下一步参考，不构成实现方案）：
起于 `limit_reg[6]/Q`，经约 6 个 CARRY4 的比较链进入 `engine/*/CE`；后半段是两条高扇出网络
（`fo=609`、`fo=512`，分别 1.191 ns、1.243 ns 的布线延时）驱动的 512 位累加器使能。
因此这一步的余量不仅取决于比较级数，也取决于使能网络的扇出与布线；两者都属于后续
"超时比较/参数缓存"一类改动的范围。综合布局布线对源码改动敏感，绝对数字（0.118 ns）
只对应当前这次快照与种子，不必逐位复现。

## 结论与边界

支持：本步在覆盖范围内行为等价（独立复跑两份 RTL + 独立 oracle）、资源小幅下降、
目标路径消失、WNS 提升且无新增 DRC。

不能据此宣布：绝对余量仍薄（0.118 ns / 10 ns ≈ 1.2%），仍是控制器 OOC，不含实体 BRAM/SoC，
未涉及 C01 驱动、板端、MMIO/DMA 与整机 LIVE；本目录不构成 commit 依据，提交决定权归用户与归口会话。

## 环境与协作备注（供复现）

- 本机 `python3` 是 Microsoft Store 桩，静默失败（退出 49），会让 `run_coprocessor_iverilog.sh`
  在向量生成处无输出直接中止；复现时需显式设置 `COPROCESSOR_PYTHON`/`VISION_PYTHON` 指向 Python 3.12。
- 20:53 的 `ooc-wrapper.exit.txt`（退出 42）为瞬时环境故障：同机 20:59 直接调用
  `D:/Vivado_downloads/2026.1/Vivado/bin/vivado.bat` 可正常识别 BASIC 许可证（有效至 14-sep-2027），
  20:58 起的正式 OOC 正常完成；许可证文件位于 `C:/Users/ASUS/AppData/Roaming/XilinxLicense/Xilinx.lic`。
- 本次曾并发启动一次重复 OOC（输入哈希与归口会话完全相同），发现后已中止，
  并删除其未完成目录 `../cnn-ooc-3526468564a84b05aa73efba08cdac80/`（无 `exit.txt`、无报告），
  仅保留归口会话的完整目录。
