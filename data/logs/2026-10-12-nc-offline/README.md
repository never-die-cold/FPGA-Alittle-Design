# 2026-10-12 NC离板续工证据

基线 dev/model@3e2e1c9，用户请求离板continue本人事项；用户明确选“本轮快速模式，免逐步出题；提交前仍确认理解”。
仅离板：未打开硬件目标、串口/UVC、未下载位流。本轮只改Tcl、Python、文档与证据，未改RTL或接口字段。

## 1. 实际BD复位缺陷与修复

命令（仓库根目录；日志文件使用新名称）：

```powershell
& D:/Vivado_downloads/2026.1/Vivado/bin/vivado.bat -mode batch -source sim/scripts/validate_capture_subsystem.tcl -log sim/build/c01-reset-new.log -journal sim/build/c01-reset-new.jou -tclargs reset_tests
```

| 运行 | 原始输出/退出码 | 结论 |
|---|---|---|
| 修复前接线+新增检查 | reset-before-console.txt / reset-before.exit.txt=1 | 拒绝aux_reset_in接low；真实BD复现持续复位结构缺陷 |
| 修复后初次矩阵 | reset-after-console.txt / reset-after.exit.txt=1 | 正常检查及aux极性负例通过；外部极性为只读，注入没生效，矩阵正确报失败 |
| 修复后最终矩阵 | reset-final-console.txt / reset-final.exit.txt=0 | 正常设计与6个真实负例通过，恢复正确连线后保存BD |

最终6负例：辅助复位极性错误、高常量为0、低常量为1、外部/辅助/调试复位错误接线；每次恢复后再检查。
READBACK: stream=24 stores=4 mm2s=0 reset_high=0 format=2。
修复前/后入口与检查器版本按文件名保存；复现旧失败可把上方-source改为本目录validate-before-net-fix.tcl，仍应exit=1。
生成的BD路径在reset-final-console.txt中；无bitstream，无实机通过声明。

## 2. 既有候选产物与98个构建输入

```powershell
python sim/scripts/check_c01_artifacts.py sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.bit
```

candidate-artifacts.json/txt及exit=0：XSA内嵌bit/hwh逐字节配对，地址/VDMA/RGB/复位释放全部通过；仍为offline_candidate_only。
bit/hwh/XSA SHA分别86d2adb0…、eaaf68c3…、421c5235…，与历史候选一致，未生成新产物。

首次严格源快照核对（build-input-audit.txt / exit=1）发现PS配置不匹配。诊断build-input-mismatch-diagnostic.txt显示：
原清单37925字节SHA5029fd4d…，Git/checkout为37064字节SHAde589f06…，861个CRLF被转为LF。
未把规范化文件冒充原字节；未覆写旧归档。

```powershell
python sim/scripts/audit_c01_build_inputs.py data/logs/c01-capture-e2a602d6e0da49a2b6da072abca47c70/manifest.json --recover-to sim/build/c01-input-recovery-new --output sim/build/c01-input-recovery-new.json
python sim/scripts/audit_c01_build_inputs.py data/evidence/2026-10-12-c01-exact-build-inputs/manifest.json --output sim/build/c01-input-recheck-new.json
```

目录和输出须为新名称。已交付精确恢复包data/evidence/2026-10-12-c01-exact-build-inputs：98个全部匹配原清单，68个以匹配SHA/长度的CRLF恢复；manifest逐字节复制。
build-input-recovery.json/txt及exit=0；随后无恢复选项的build-input-strict-recheck.json/txt及exit=0，再次98条严格通过。
当前96个输入同字节，build_capture_hdmi.tcl/run_c01_capture.ps1有构建后包装改动；当前RTL/XDC均相符。该核对不独立证明bit到源码映射或实机验收。

## 3. 统一Python回归

使用C:/msys64/usr/bin/bash.exe，PATH=/ucrt64/bin:/usr/bin优先，VISION_PYTHON为本机Python3.12完整路径：

```bash
bash sim/scripts/run_vision_python.sh
```

python-regression.txt / exit=0，14组通过。新增test_c01_build_inputs覆盖：默认拒绝LF变化、精确CRLF恢复、严格复算、内容篡改、原归档不改、越界/重复路径、旧目录拒覆盖、当前源码漂移如实报告。
恢复包inputs及manifest已设置-text，避免再次Git行尾转换；原日志定向保留空白，Markdown与实际脚本仍检查。
staged-evidence-check.txt已从Git索引逐条取原始blob核对，manifest与98个输入的SHA/长度全部通过，确认暂存不会再次转行尾。
source-and-links.txt记录新增源码空白及修改文档本地链接检查PASS；git diff --check与git diff --cached --check均通过。

## 4. 交付及未完成

NC返板顺序/记录/定标准备：docs/nc-offline-readiness-2026-10-12.md；DDR所有权交接：docs/c01-ddr-frame-ownership-v0.md（候选，待WC/JL/NC实际评审）。
清单和C04实现状态更新，已有NC来源/有效轮次确认引用前轮全文；C04整体不代签冻结。
未实现/未验收：custom DDR适配/帧槽保护/颜色动态长测、N02/N03完整实机、N04/N05真实采集、正式INT8整网黄金、CNN RTL、核工业固件、正式硬件LIVE/工业闭环。
逐段讲解和提交前理解题见report/llm_log/2026-10-12-nc-offline-readiness.md。
