# 协处理器整机构建变体

> 状态（2026-10-27）：变体划分已落脚本；合并后 A/B 均待 Windows 重新门禁，板级均为
> **UNVERIFIED**。历史 bit/hwh 不能替代新源码构建。

## A：首网包（当前 NC 板验候选）

不设置 `COP_WITH_VIDEO`。`build/build_pynq_cop_gate.tcl` 只装入：

- `src/riscv/*.v`、`src/coprocessor/*.v` 和受控 IMEM/DMEM hex；
- `build/create_pynq_cop_bd.tcl` 的 PS、核、协处理器、DMA/GPIO；
- `build/constraints/pynq_cop_board.xdc` 与 `build/constraints/pynq_cop_cdc.tcl`。

此路径不会设置 HDMI IP 仓库，不会装入 `src/vision/*.v`，不会 source
`build/attach_pynq_video.tcl`，也不会装入 HDMI/视觉 XDC。它才可在新门禁通过后进入当前
NC 首网包；在此之前没有有效新包。

2026-10-27 JL 用 `COP_BUILD_NAME=pynq_cop_a_20261027_r1`、未设 `COP_WITH_VIDEO` 实测门禁
PASS：WNS 2.078 ns、DSP 136/220、BRAM36 69/140、latch/DRC=0；IMEM 首字 `00008117`、
INIT 非零、readmem warning=0；CDC-15/3/6=`73/12/7`，allowlist 仍为 5 条。产物 SHA256：
bit `f325a0dc4c2cb143e24ef13df6608e206af5c58f0354b3deec6f039d5875f71f`，
hwh `480d04a3d9abee59e81892378c2457dfe92ea0cf6fc0822d4467b2121dbab358`，
xsa `9e0a56276e89e2a94e3155eea7e267c97b97014ed74c8874524d03eaa462534c`。
该门禁不等于板级验收；B 仍全部 UNVERIFIED。

```powershell
$env:COP_PYTHON="C:\Microsoft VS Code\anaconda\python.exe"
$env:COP_BUILD_NAME="pynq_cop_a_20261027_r1"
Remove-Item Env:COP_WITH_VIDEO -ErrorAction SilentlyContinue
& "D:\vivado\2026.1\Vivado\bin\vivado.bat" -mode batch `
  -source build\build_pynq_cop_gate.tcl
```

## B：视频集成（J07 实验变体）

显式设置 `COP_WITH_VIDEO=1`。在 A 的基础上增加 `src/vision/*.v`、
`build/attach_pynq_video.tcl`、`sim/build/hdmi-source/hdmi_pins.xdc`、
`src/vision/config_cdc.xdc`、`src/vision/capture_cdc.xdc` 和 HDMI IP 仓库；VDMA 使用 HP1。

```powershell
$env:COP_PYTHON="C:\Microsoft VS Code\anaconda\python.exe"
$env:COP_BUILD_NAME="pynq_cop_video_20261027_r1"
$env:COP_WITH_VIDEO="1"
& "D:\vivado\2026.1\Vivado\bin\vivado.bat" -mode batch `
  -source build\build_pynq_cop_gate.tcl
```

B 仅表示离板集成入口已进入源码，综合、实现、时序、CDC 与板上行为均 **UNVERIFIED**；
不得写成“整机可用”。B 的 bit/hwh/xsa 不得放进 A 的 NC 包，A 的历史报告也不得用于 B。

## 环境与目录纪律

| 变量 | 必须值 / 默认 | 作用 |
|:---|:---|:---|
| `COP_PYTHON` | 显式指向真实 Python | 避免 WindowsApps `python3.EXE` 占位符 |
| `COP_BUILD_NAME` | 每次使用全新、可辨认名称 | 隔离 `build/run/` 与 `build/reports/` 证据 |
| `COP_WITH_VIDEO` | A 不设置；B 仅设为 `1` | 只有精确值 `1` 才加入视频文件 |

不得用旧 `COP_BUILD_NAME` 回放报告；脚本发现同名 run 目录会 fail-closed。复跑时改用新名称，
并只读取同名 `build/reports/<name>/gate_summary.txt`。不得删除旧目录后沿用旧名字制造
“同一次构建”的错觉。

## 本次视频集成变更清单

提交 `2eab8f1` 新增/修改：`build/attach_pynq_video.tcl`、
`build/build_pynq_cop_gate.tcl`、`build/constraints/pynq_cop_board.xdc`、
`build/constraints/pynq_cop_cdc.tcl`、`build/create_pynq_cop_bd.tcl`、
`sim/scripts/check_cop_cdc_bounds.tcl`、`sim/scripts/finish_cop_product.tcl`、
`sim/scripts/validate_vision_cdc.tcl`、`src/riscv/pynq_cop_top.v`；
`src/vision/*.v`/两份 CDC XDC 是 B 才装入的既有源文件。
