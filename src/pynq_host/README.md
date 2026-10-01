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

> 状态：M2 原型已起步（2026-10-01）——`vision_regs.py`（寄存器映射绑定，mock 自测 6/6）、
> `vision_demo.py`（A1/A4 演示序列，上板当日运行）、`board/adv7611_init.py`（I2C/EDID 骨架，
> 寄存器值表待对照 ADI 官方脚本核对后启用，EDID 生成已自检）；M3 应用闭环、M4 发布包的
> 收口时间与验收以主计划为准。
