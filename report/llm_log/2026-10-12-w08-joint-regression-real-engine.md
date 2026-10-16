# 2026-10-12 协作记录：服务×EXE 联合离板回归（W08）与真引擎转正（W05-2）

> 标签：#vision #build #工具链 #架构决策
> 平台：ZCode（DeepSeek Flash） ｜ 相关 commit：`6bf6b03`（W08）`edff792`（W05-2）`f9f9a5d`（venv 文档）
> 上下文：NC 返场执行单要求"脚本同时检查退出码与日志"；W05-2 把 file_engine 从"已写未验证"转正；本机无预装 torch/cv2。

## 1. 任务与初始提示词

「按三人清单推进 W08（服务/EXE 联合离板回归 + 工业场景黄金）与 W05-2（真引擎接入重依赖入口），
不依赖板卡；每步出回归证据。」

## 2. 模型第一版方案

- W08 分两层：**栈内联合测试**（`test_vision_joint.py`，stdlib，驱动 EXE 真实逻辑层
  `RemoteRounds + BatchRecords + live_view`，黄金矩阵 pass/missing/extra/wrong/recheck 三重期望：
  判定/横幅差额/实际-工单）+ **打包 e2e**（`test_vision_service_e2e.py` 作为打包门禁第 6 关）。
- W05-2：`test_service_engine.py` 经 HTTP 走通 `file_engine → inspection_run`；黄金值**冻结自
  归档运行**（`data/evidence/2026-10-10-offline-inspection/runs/synthetic-001`：CHECK_FAIL、
  actual 2/0/1、类别 bolt/washer/bolt），并加 `decision == judge(...)重算` 把服务映射与规则引擎焊死。
- 环境：仓库本地 venv（`sim/build/vision-venv`）装 numpy/opencv/torch(cpu)/Pillow。

## 3. 失败现象

1. 打包门禁与检查链的**两组不一致**：runner 按 `test_$name.py` 命名找文件，而新测试命名
   `test_vision_service_engine.py` → `service_engine` 项直接"文件不存在"。
2. 检查链三组 FAIL：`dataset_audit`/`reference_package` 报 `No module named cv2/numpy`——
   测试内部用 `python -I` 启动隔离子进程，**`-I` 忽略 PYTHONPATH**，仓库本地依赖目录对它不可见。
3. venv 首跑 8 组 FAIL：`train_fastener_classifier` 导入 PIL（Pillow 未装）。
4. `pip install opencv-python==4.12.0.0` 不存在（PyPI 实为 `4.12.0.88`）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | runner 日志 "can't open file 'test_service_engine.py'" | 入口命名约定未对齐（`test_$name.py`） | 重命名测试文件 | ✅ 本项通过 |
| 2 | `-I` 子进程 ModuleNotFoundError | `-I`（isolated）忽略 PYTHONPATH 与 user-site，只认 site-packages | 建 repo 本地 venv 装全部依赖，入口 `VISION_PYTHON` 指其 python | dataset_audit/reference_package 通过 |
| 3 | 8 组 FAIL 于 `from PIL import Image` | 重依赖链缺 Pillow（EXE 依赖目录里本来有 12.3.0） | venv 补 `Pillow==12.3.0` | ✅ 检查链 14/14 首次本机全绿 |
| 4 | pip "No matching distribution" | 版本号笔误（.0 与 .88） | 按 PyPI 列表改 `4.12.0.88` | ✅ |

## 5. 最终结论

W08 两层回归落地（栈内 16 组 + 打包 6 关）；W05-2 真引擎经 HTTP 全链验证（exit 0）；
本机检查链 14/14。venv 跑法写入 `docs/offline-inspection.md`（gitignored，不进交付包）。

## 6. 经验沉淀

- 触发条件：跨工具/跨环境复跑测试；测试用 `-I` 隔离子进程；新测试接入既有 runner。
- 排查步骤：先看 runner 的命名/路径约定 → 再看解释器环境（`-I` 边界）→ 逐个补缺失包并**重跑全套**。
- 适用范围：换题目/换板卡仍成立（"隔离子进程不吃 PYTHONPATH"是 Python 语义，不是本项目特性）。
- #skill候选：**"黄金值冻结 + 规则重算双钉"**（归档产物出期望值，再以规则引擎重算对拍防实现漂移）；
  及"`-I` 与 PYTHONPATH 的边界"（可并入 sim-board-consistency 的环境条目）。
