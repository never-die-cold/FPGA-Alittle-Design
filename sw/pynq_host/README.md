# sw/pynq_host —— PYNQ 上位机

PS 侧 Jupyter Notebook：寄存器配置、黄金参考比对、性能与资源数据自动采集、结果展示。

## 规划内容

- `demo.ipynb`：主演示 notebook（一键跑通全链路演示）
- `benchmark.ipynb`：基线对比与指标采集（CPI、延迟、帧率、加速比）
- `golden_ref.py`：软件黄金参考实现（OpenCV / 纯 Python 推理）
- `metrics.py`：数据自动采集与报告生成（→ `data/`）

## 约定

- 所有 notebook 从头运行（Restart & Run All）必须无报错
- 采集脚本通用部分尽量与题目解耦，作为通用 PYNQ Skill 的原料

> 状态：🚧 待开发
