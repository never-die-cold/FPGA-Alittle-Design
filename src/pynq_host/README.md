# src/pynq_host —— PYNQ 上位机

PS 侧负责配置与结果通信、ARM 软件基线、黄金参考和指标采集；Jupyter 保留为板端调试与复现入口。最终工业操作界面为 Windows EXE，由 `watercopper` 负责：采集卡视频和网口识别结果统一展示，见根目录 [项目主计划](../../plan.md) §1.3。

## 规划内容

- `demo.ipynb`：板端调试与复现 notebook
- `benchmark.ipynb`：基线对比与指标采集（CPI、延迟、帧率、加速比）
- `golden_ref.py`：软件黄金参考实现（OpenCV / 纯 Python 推理）
- `metrics.py`：数据自动采集与报告生成（→ `data/`）
- 板端服务：向 EXE 提供位置、类别、工单判定、帧/检查关联与设备状态，接收配置；协议与实现主责待冻结。
- EXE：采集卡预览、框与类别叠加、工单配置、统计、异常截图和记录导出；技术栈和代码目录待确定。

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
> 接线与环境备忘见 [ONBOARD.md](ONBOARD.md)。源断连/重连实测待补。
> `board/adv7611_init.py` 仅为外接接收器示例（PYNQ-Z2 无 ADV7611，不用于本板）。
