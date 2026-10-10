# src/pynq_host —— PYNQ 上位机

PS 侧负责配置与结果通信、ARM 软件基线、黄金参考和指标采集；Jupyter 保留为板端调试与复现入口。最终工业操作界面为 Windows EXE，由 `watercopper` 负责：采集卡视频和网口识别结果统一展示，见根目录 [项目主计划](../../plan.md) §1.3。

## 当前实现与规划边界（2026-10-09）

已有 `vision_regs.py`／`vision_demo.py`／`m2_onboard.py`／`onboard_smoke.py` 配置及板端诊断；
`data/golden/vision/localize/reference.py`／`arm_localize.py` 与打包工具提供定位／裁剪黄金参考，不等于实时部署。
`vision_protocol.py`／`vision_mock_service.py` 为明确标注 MOCK 的接口；D6 未知字段缺口见[核查注记](../../docs/vision-sync-protocol-decisions.md)。
下列 notebook／通用工具仍是规划，不能由 mock 或训练演练推断已实现。

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
