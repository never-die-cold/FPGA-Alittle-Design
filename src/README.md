# src —— 设计源码

> 本目录只放可综合/可运行的源码与契约，不放运行日志、截图、临时构建产物。
> 目录地图见 [`docs/project-map.md`](../docs/project-map.md)；开工纪律见 [`docs/workflow.md`](../docs/workflow.md)。

## 子目录

| 目录 | 职责 | 入口 |
|:---|:---|:---|
| `riscv/` | 自研 RV32IM 核、流水线/转发/BHT、最小 SoC；v0/v1 接口契约 | [README](riscv/README.md)、[plan](riscv/plan.md)、[design_v0](riscv/design_v0.md)、[design_v1](riscv/design_v1.md) |
| `vision/` | HDMI 视觉预处理、捕获状态、AXI 配置、OSD | [README](vision/README.md)、[design_v0](vision/design_v0.md) |
| `coprocessor/` | INT8 CNN 算子、整网控制器、整数参考 | [README](coprocessor/README.md)、[design_v0](coprocessor/design_v0.md) |
| `riscv_fw/` | RISC-V 裸机固件、CoreMark、测试程序与 hex/dis | [README](riscv_fw/README.md)、[Makefile](riscv_fw/Makefile) |
| `pynq_host/` | PS 侧配置、定位/ROI、检查服务、FILE/LIVE 骨架 | [README](pynq_host/README.md)、[ONBOARD](pynq_host/ONBOARD.md) |
| `vision_client/` | Windows EXE：UVC 预览、轮次叠加、记录/CSV | [README](vision_client/README.md) |

## 常用入口

```bash
bash sim/scripts/run_iverilog.sh all          # RTL 全套 tb（含 CoreMark 长测）
bash sim/scripts/run_vision_python.sh         # 视觉 Python 测试
bash sim/scripts/run_coprocessor_python.sh    # CNN 整数参考测试
```

Vivado 构建见 [`build/README.md`](../build/README.md)；上板见 [`board/README.md`](../board/README.md)。

## 生成物与证据边界

- `src/riscv_fw/*.elf`、`*.bin`、`*.o` 是本地编译产物，不入库；`*.hex`、`*.dis` 是测试证据，入库。
- 不要手改 `.dis`/`.hex`；改 `.c`/`.S` 后按 `src/riscv_fw/README.md` 重新生成。
- 接口变更先改对应 `design_*.md` 契约，再改 RTL/软件；契约是唯一权威。
