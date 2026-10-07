# 模块一复现清单（#skill候选）
更新：2026-10-07。对应 [收口报告](../report/module1-closure.md) 与 [原始证据](../data/logs/2026-10-07-module1-closure/)。
适用范围：同 RTL/hex 的四档核对比；不用于官方 CoreMark 或完整 ISA 认证。

## 环境与版本
在仓库根执行；Windows 用 MSYS2 UCRT64 Bash（不要误用 WindowsApps/WSL 的 bash）。
PATH 需含 `C:/msys64/ucrt64/bin`、MSYS2 `usr/bin` 及 Git（本机 `E:/Git/cmd`）；GCC 14.2.0、Icarus 13.0。
PowerShell 用 `RISCV_VIVADO_BIN` 指向 Vivado 2026.1 的 bin，本机为 `D:/Vivado_downloads/2026.1/Vivado/bin`。
arch-test 套件按 `sim/scripts/fetch_arch_test.sh` 取得；本轮 commit 为 `6f7f47bdc61c0c51c0cbf75789678a1235eeefc2`。
固件构建入口为 `src/riscv_fw/Makefile`；预载 coremark.hex/bench_v0_1.hex 已在库。核镜像容量32KB，禁止随意扩大测试 RAM。
先记录 branch/log/status、RTL/tb/镜像哈希；并发协作时结论绑定文件哈希，不能只绑定会移动的 HEAD。

## 功能、签名与四档计数
```bash
bash sim/scripts/run_iverilog.sh all
ARCH_TEST_LOG_DIR=data/logs/<new-run>/arch-complete bash sim/scripts/run_arch_test_matrix.sh
# 快速定位时可单独执行：
bash sim/scripts/run_iverilog.sh bench_bht2
bash sim/scripts/run_arch_test.sh div-01 M bht2
```
all 含原有核/视觉回归、自写 benchmark 四档和 CoreMark 四档；M 指令只在提交拍退休。
arch 矩阵为11条×4档，每档先与官方 reference 比对，再比四档签名 SHA256；有一个不匹配即失败。
创建新的日志目录，不覆盖旧 environment/失败日志；shell 使用 pipefail，留存真实退出码。

## 优化后 XSim 四档
```powershell
./sim/scripts/run_module1_xsim.ps1 -LogDir data/logs/<new-run>/xsim-pass
```
脚本使用同 tb/hex/CRC golden，记录源码/镜像哈希，在 sim/build/module1-xsim 隔离生成物。
默认 Icarus 对拍参考是已归档的 10/07 四档 CoreMark 锚点；自定义 `-IcarusLog` 应仅含四档 CoreMark PASS/BHT 记录。
Windows .bat 参数包含等号时必须保留双引号，generic 和 testplusarg 都一样；native exit=0 后仍须检查 PASS 与计数。

## 核实现、OOC 补证与真实板卡
从全新 checkout 复现，先用以下入口生成五个 routed checkpoint（run 产物不入库）：
```powershell
# Vivado 已加入 PATH，或用完整 vivado.bat 路径
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_nofwd_10ns_postopt 10.000 -core_profile nofwd src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_fwd_10ns_postopt 10.000 -core_profile fwd src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht1_10ns_postopt 10.000 -core_profile bht1 src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht2_10ns_postopt 10.000 -core_profile bht2 src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht2_11p52_postopt 11.520 -core_profile bht2 src/riscv
vivado -mode batch -source sim/scripts/audit_module1_ooc.tcl -tclargs data/logs/<new-run>/ooc-complete
```
build_fmax 的 “RUN DONE”不等于通过；审核 WNS/hold、DRC、内部约束、clocks/版本、资源与 worst paths。
audit 对已布线文件补 min/max、DRC/clock/check_timing；fwd/BHT1 另做11.520ns固定布线 STA。它不重新综合/布线，前置 checkpoint 必须属于正确源码版本。
保存 checkpoint 哈希和原始构建日志；不得对未知版本 checkpoint 宣称当前核已验证。
核 OOC 仅约束内部核时钟，外部接口延迟由 SoC 验收；两者的频率结论分开。
```powershell
vivado -mode batch -source build/build_soc.tcl -tclargs 40 bht2
vivado -mode batch -source board/scripts/program_soc.tcl -tclargs build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit
```
bitstream 只在构建门禁通过后生成；下载后由板前人员观察 LED1101、BTN0按下0000/松开0001并记录观察人。
PROGRAM PASSED 不能替代 LED 观察；软复位不清 DMEM。板级125MHz、100MHz核失败与外推值须保留。

## 汇总与验收
本轮统一证据目录的约定文件：all-final.log/.exit.txt、arch-complete.log、arch-final.exit.txt、arch-complete/、xsim-pass/、ooc-complete.log。
```bash
python sim/scripts/summarize_module1.py data/logs/<new-run>
git diff --check
```
汇总脚本从原始日志重算 CPI、CoreMark/MHz、BHT 命中率和两种收益，验证计数恒等式、golden、档间签名和 XSim 对拍。
原25%仅转发失败及8.14%历史不得改写；当前转发门禁≥8.0%，25%为组合尽力目标。
各轮 source manifest、source SHA256 与脚本变更入档；若被测 RTL/tb/hex 在运行期间改变，重新验证受影响部分。
最后逐段讲解与3道理解题，用户回答后记录判定；未确认理解不得 commit。远程 #20/#21 关闭须引用已入库证据。

## 候选技能边界
触发：核优化后四档公平对比、外部工具对拍、性能指标收口。
步骤：固定版本与镜像→专项/全量→arch golden→XSim→OOC/SoC→原始日志计算→人工理解。
陷阱：把关闭BHT的零事件当0%命中率；把Slack外推当通过频率；把CoreMark计时窗口与CPI窗口混用；把不同分母收益相加；在32KB外验证巨大镜像。
状态：本轮流程已经实际执行并留痕；这里仅标 #skill候选，尚未安装/创建正式技能包。
