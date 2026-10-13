# 用户离开期间的离板续工证据

2026-10-12，`dev/model@3e2e1c9`。用户已连接硬件并授权继续可离板执行的事项；本轮未操作板卡、串口/UVC或加载位流，未提交/推送。
返场动作与人工审查结果见[执行单](../../../docs/nc-return-checklist-2026-10-12.md)。

## 环境与复现

仓库根目录；MSYS2 `C:/msys64/usr/bin/bash.exe`，PATH 优先 `/ucrt64/bin:/usr/bin`；Python 3.12.10。
设置 `VISION_PYTHON=/c/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe`。
协处理器入口的 python3 使用既有 `sim/build/pr-review/tools/python3`（原样 exec 上述解释器）；仅该入口将该目录放 PATH 首位。
以下均为仓库既有入口；重跑时用新日志名，产物审计的 --output 文件必须不存在。

| 命令 | 本轮原始输出 / 退出码 |
| --- | --- |
| `bash sim/scripts/run_iverilog.sh all` | rtl-all.txt / rtl-all.exit.txt=0；核、四档benchmark/CoreMark、25视觉RTL tb及14视觉Python组全量通过 |
| `bash sim/scripts/run_vision_python.sh` | vision-python.txt / vision-python.exit.txt=0；14组通过 |
| `bash sim/scripts/run_inspection_python.sh` | inspection-python.txt / inspection-python.exit.txt=0；13组通过 |
| `bash sim/scripts/run_coprocessor_python.sh all` | coprocessor-python.txt / coprocessor-python.exit.txt=0；3组通过 |
| `python -u sim/vision/test_n03_board_capture.py` | n03-fake-driver.txt / n03-fake-driver.exit.txt=0；5类假驱动用例通过 |
| `python -u sim/vision/test_n03_buffer_lifecycle.py` | n03-buffer-lifecycle.txt / n03-buffer-lifecycle.exit.txt=0；释放分支重放通过 |
| `python sim/scripts/check_c01_artifacts.py sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.bit --output <新JSON>` | candidate-artifacts.json/txt / candidate-artifacts.exit.txt=0；offline_candidate_only |
| `python sim/scripts/audit_c01_build_inputs.py data/evidence/2026-10-12-c01-exact-build-inputs/manifest.json --output <新JSON>` | build-inputs.json/txt / build-inputs.exit.txt=0；98项严格匹配，当前changed=2/missing=0 |
| `iverilog -g2001 -tnull -s core_top src/riscv/*.v`；`iverilog -g2001 -tnull -s vision_axi src/vision/*.v` | verilog2001-core/vision.txt为空，对应.exit.txt=0；仅语法/展开，不替代综合或时序验收 |

## 证据与边界

head/status-before、staged/unstaged-before.patch 保留开工状态；source-inputs-before.json 保存被测源码/测试/黄金文件哈希。
C04与采集口径的逐行源码依据保存于 *-excerpts.txt；它们是静态审查，不宣称新增功能通过。
第一次沙箱全量运行在长算例期间因后续Python不可用而中止，rtl-all-sandbox-incomplete.*保留；不算全量PASS。已换可用通道从头重跑。
Python的首次授权执行审批曾超时，重试成功；未把审批超时当功能失败。候选配对与98输入完整性不独立证明bit-to-source或当前板端版本。
diff-check/staged-diff-check.txt及对应.exit.txt保留空白检查；最终源文件和索引是否变化在收尾核对中记录。
new-doc-check.txt记录3份新Markdown的11个本地链接和空白检查；index-check.txt证明原有暂存差异哈希未变。
coremark-profiles.json保存四档短基准与四档CoreMark的周期/退休/气泡数及原始行号；长算例退休数均为10,106,386，CRC由tb逐项断言通过。
source-check.json最终核对334个被测文件，changed_count=0；final-scope-check.txt确认原有暂存/未暂存差异均未变，HEAD前后相同。
python-environment.json保存Python/NumPy/Torch/OpenCV/Pillow版本；N03日志中的Overlay/HDMI阶段由假驱动产生，不是本轮实机动作。
未实现/未验收仍包括custom DDR保护、正式INT8整网/CNN/核工业固件、真实硬件LIVE、完整N02–N05、C04与工业/发布验收。
