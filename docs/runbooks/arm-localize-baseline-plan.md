# PYNQ ARM 定位与逐目标裁剪基线：实施清单

日期：2026-10-03；起点：`codex/vision-offboard` / `8a2384c`。
状态：全部交付完成；第 1 步与最终集中三题均通过，用户已授权按功能与证据拆分提交。

## 目标与边界

板端 Python 读取固定灰度图片文件，复用定位参考输出目标框、逐目标小图和计算耗时。
输入是文件；本轮不修改核、视觉 RTL 或现有 Overlay，不使用实时 HDMI/PL 快照。
不输出类别、工单通过结论或相机识别精度。
依赖仅限 Python 标准库；无需 OpenCV、torch、PYNQ 或 root 权限。

## 当前事实

- 已实现并验证：文件运行器、PGM/hex、便携包、五项 Python 回归及 ARM 三场景 15 次采样对比。
- 已实现但未完成实际应用验收：软件定位/裁剪基线；尚无真实相机数据。
- 未实现：实时图像读取与正式识别功能，纯 Python 性能优化尚未实施。
- 未接入：实时 PL 图像读取、CNN 和工业检查服务。

## 数据与结果设计

- 首步输入为 JSON 灰度矩阵：`{"pixels": [[...], ...]}`；非空矩形、GRAY8 整数像素。
- 输入文件 SHA256、frame/config 标识、分割参数、输出尺寸随结果保存。
- 复用已有阈值分割与 4 连通定位，不另写定位算法。
- bbox 为原图坐标闭区间；宽高分别是 `x1-x0+1`、`y1-y0+1`。
- 裁剪复用中心对齐 16.16 双线性与两级 8-bit lerp。
- `RECHECK_BORDER` / `RECHECK_TARGET_LIMIT` 保留状态，禁止把待复检目标送入裁剪/推理。
- 首步小图以 JSON 像素矩阵保存；第二步增加 PGM 图片与逐像素 hex。
- 64×64 仅是可覆盖的基线测试尺寸，不视为正式 CNN 输入契约。
- 耗时分别测定位、裁剪；文件读取和结果写盘单列或明确排除。
- 保存 Python 版本、系统及机器架构，区分 Windows PC 与 PYNQ ARM 结果。

## 小步交付清单

每步新增/修改代码总计不超过 100 行，含测试及回归接入；文档/固定数据另计。
第 1 步按原流程执行；用户随后明确要求“一步到位”，豁免剩余单步行数/等待，最后集中三题；不自动 commit。

| 步骤 | 交付物 | 文件范围 | 预计代码行数 | 验证 |
|:---|:---|:---|:---|:---|
| 0（已完成） | 本设计清单、已有参考基线日志 | docs/、data/logs/、report/llm_log/ | 0 | 现有 vision_python 三项回归 |
| 1（完成，理解通过） | 文件输入与 JSON/计时 | src/pynq_host/、sim/vision/、sim/scripts/、固定输入 | 初版 99 | PC/ARM 精确一致 |
| 2（完成） | PGM/hex 与当前有效清单 | 运行器与测试 | 按用户豁免批量实施 | 顺序、哈希、编号、失败不发布、旧批次隔离 PASS |
| 3（完成） | 标准库便携包与说明 | src/pynq_host/、sim/scripts/、sim/vision/、docs/ | 同上 | -I 隔离执行、缺/改文件门禁、相对路径 CLI PASS |
| 4（完成） | 三场景原始采样与报告 | 性能/对比脚本、日志/证据 | 同上 | 每场景预热 1 次、测 5 次；15 组数值/文件字节一致 |

若任一步预计超限，先提出拆分，不把额外代码塞进当前步。
以上为原流程；用户批量交付指令优先，豁免记录在 llm_log §8。
跨目录范围提前说明：src/pynq_host/、sim/vision/、sim/scripts/、docs/、data/evidence/、data/logs/、report/llm_log/。

## 基线复验

通用入口：`bash sim/scripts/run_iverilog.sh vision_python`。
PC 本次使用 Codex bundled Python，并在 MSYS2 Bash 内设置 `PATH=/usr/bin:/bin:$PATH`。
原始结果：三个 `PASS:`，进程退出 0。
日志：`data/logs/2026-10-03-arm-localize-baseline/pc-reference-baseline.log`。
两次 PATH 配置失败的启动日志保留为 `pc-reference-baseline-attempt1/2.log`；未进入测试。

## 板端验收前置

用户确认 SSH 为 `xilinx@169.254.87.99`，另有 `192.168.2.99` 别名。
用户完成公钥配置后继续第 1 步；SSH 已连接，架构 `armv7l`，Python `3.10.4`。
已生成专用密钥 `sim/build/arm-localize-ssh/id_ed25519`，经 `git check-ignore` 确认忽略。
私钥由沙箱创建，原 ACL 使联网账户读不到；现限定为 Windows ASUS 用户、SYSTEM 与 Administrators。
SSH 原始日志：本轮 `board-env.log`（受限网络尝试）和 `board-env-approved.log`（可达、认证失败）。
便携包仅运行软件参考；不加载 bit、不触碰 MMIO，不影响 JL 的核工作。
板端环境日志：`board-env-key-fixed.log`；工作目录 `/home/xilinx/arm_localize_step1`。

## 第 1 步复现与结果

仓库根目录执行（以下 `python` 指当前 Python 3）：

```bash
bash sim/scripts/run_iverilog.sh vision_python
python src/pynq_host/arm_localize.py data/evidence/2026-10-03-arm-localize-baseline/two_targets.json data/evidence/2026-10-03-arm-localize-baseline/pc-result.json --size 64 64 --frame-id 7 --config-id 3
```

板端复跑：将 `arm_localize.py`、`data/golden/vision/localize/reference.py` 与 `two_targets.json`
复制到同一目录，然后执行：

```bash
python3 -B arm_localize.py two_targets.json result.json --size 64 64 --frame-id 7 --config-id 3
```

取回 result.json 保存为仓库 `data/evidence/2026-10-03-arm-localize-baseline/arm-result.json`，再执行：

```bash
python sim/vision/test_arm_localize.py data/evidence/2026-10-03-arm-localize-baseline/pc-result.json data/evidence/2026-10-03-arm-localize-baseline/arm-result.json
```

框坐标 `[1,1,2,4]` / `[7,2,9,5]`；输出两个 64×64 小图，ARM/PC 全部像素一致。
ARM 本次单次定位 1.240646 ms，裁剪 259.325834 ms；计时不含文件 I/O。
这是 12×8 合成图冒烟，不是 720p 性能或真实相机识别验收；没有承诺帧率。
原始输出在本轮日志目录的 `step1-python-regression.log`、`step1-pc-run.log`、
`step1-arm-run.log`、`step1-arm-pc-compare.log`，均退出 0。

## 最终交付

入口与统计以 docs/arm-localize-results.md 为准；操作见 docs/arm-localize-runbook.md。
最终板端目录为 /home/xilinx/arm_localize_final_v3/arm_localize，最终证据为 arm-board-final/。
第 1 步耗时为历史单次记录；最终性能见三场景五次采样报告。
集中讲解与三题见 docs/arm-localize-walkthrough.md；最终答案、判定与拆分提交记录见本轮 llm_log。
