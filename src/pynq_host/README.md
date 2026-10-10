# src/pynq_host —— PYNQ 上位机

PS 侧负责配置与结果通信、ARM 软件基线、黄金参考和指标采集；Jupyter 保留为板端调试与复现入口。最终工业操作界面为 Windows EXE，由 `watercopper` 负责：采集卡视频和网口识别结果统一展示，见根目录 [项目主计划](../../plan.md) §1.3。

## 当前实现与规划边界（2026-10-10）

已有 `vision_regs.py`／`vision_demo.py`／`m2_onboard.py`／`onboard_smoke.py` 配置及板端诊断；
`data/golden/vision/localize/reference.py`／`arm_localize.py` 与打包工具提供定位／裁剪黄金参考，不等于实时部署。
`vision_mock_service.py` 提供明确标注 MOCK 的服务；D6 字段白名单已随 PR #67 合并。
远端 `7101a33` 将 `vision_protocol.py` 扩展为 MOCK/LIVE v1.2 校验，整合回归通过；
网络预览的 PROTOTYPE 标识尚未实现，真实 LIVE 服务未验收，见[复验边界](../../data/logs/2026-10-10-dataset-integration/README.md)。
下列 notebook／通用工具仍是规划，不能由 mock 或训练演练推断已实现。

本轮新增 `roi_preprocess.py`、`inspection_model.py`、`inspection_rules.py`、
`inspection_replay.py`、`inspection_artifacts.py`、`inspection_run.py`：共享 ROI、
交付 FP32 权重加载、工单候选判定、文件回放与完整性检查已离板验证并随 PR #67 合并。
这是本机 FILE_REPLAY，不是板端服务；原始数据集缺失，阈值和正式精度未验收。
复现、证据与尚未实现项见[离板检查说明](../../docs/offline-inspection.md)。

后续新增 `model_reference.py`、`numpy_reference.py`、`model_audit.py`、
`reference_tensors.py`、`reference_package.py`：交付原型的 BN 折叠、独立逐层对拍、
预算审计及可移交的 FP32 软件参考包已离板验证并随 PR #67 合并；
见[模块三逐层参考](../../docs/module3-prototype-reference.md)。正式 INT8 与硬件尚未实现。

后续新增 `dataset_manifest.py`、`dataset_audit.py` 和仓库 CLI：720p 采集清单、
会话/精确重复像素/实物编号泄漏、覆盖统计和来源声明已用测试夹具验证，理解题及补测已通过。
十三组统一回归通过；这不验收真实标签或模型精度，见[数据集审计](../../docs/fastener-dataset-audit.md)。

- `demo.ipynb`：板端调试与复现 notebook
- `benchmark.ipynb`：基线对比与指标采集（CPI、延迟、帧率、加速比）
- `golden_ref.py`：软件黄金参考实现（OpenCV / 纯 Python 推理）
- `metrics.py`：数据自动采集与报告生成（→ `data/`）
- 板端正式识别服务未实现；轮次协议与 NC 主责已冻结，见[协议决策单](../../docs/vision-sync-protocol-decisions.md)。
- EXE 在 `src/vision_client/`，已有[Python/OpenCV 预览／mock 原型](../../data/logs/2026-10-06-vision-sync-schema/README.md)；正式工单、统计、导出及真实服务联调待完成。

## 板卡访问

- 校园网内 SSH：`ssh xilinx@<板卡内网IP>`（2026-09-20 建立，SD 卡已烧录 PYNQ 镜像）；notebook 在板卡 Jupyter（默认端口 9090）上运行

## 约定

- 所有 notebook 从头运行（Restart & Run All）必须无报错
- 采集脚本通用部分尽量与题目解耦，作为通用 PYNQ Skill 的原料

> 状态（2026-10-03）：M2 离板软件栈已闭环并完成首次实机验证——`vision_regs.py`（寄存器映射 +
> commit/wait_applied 原子配置协议，R11 提交/R12 确认）真实 MMIO 上板 PASS（配置号 0→2 帧首确认），
> `vision_demo.py` 实机演示序列 PASS（65 次 commit 全确认）；`vision_protocol.py`/`vision_mock_service.py`
> （定位报文契约 + 本地 HTTP mock，供 EXE 联调）；Windows EXE 原型已接真实采集卡源
> （`vision_preview.exe --source 1`，横幅正确无假框）。证据见
> [../../data/logs/2026-10-03-vision-onboard/README.md](../../data/logs/2026-10-03-vision-onboard/README.md)。
> 板端分步自检 `m2_onboard.py`（env/load/smoke/demo）、断连监视 `onboard_smoke.py watch`
> （STREAM/STALL/BUSY 事件 + WATCH-SUMMARY，含 watch-mock 离板自测）、
> 接线见 [ONBOARD.md](ONBOARD.md)。10/03 修复配置断连复测与[10/07 相机恢复](../../data/logs/2026-10-07-pi-pynq/README.md)有证据；现用位流追溯与长时间／冷启动／断连复验仍待补，不混用不同位流结论。
> `board/adv7611_init.py` 仅为外接接收器示例（PYNQ-Z2 无 ADV7611，不用于本板）。
