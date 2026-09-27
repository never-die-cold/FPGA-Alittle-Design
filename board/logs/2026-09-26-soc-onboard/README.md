# Part A SoC 真实上板记录（2026-09-26）

> 用途：`dev/rtl@db9fe33`（Part A SoC：`soc_top` + `pynq_z2_top`）在真实 PYNQ-Z2 上的 JTAG 下载与肉眼验收记录。
> 按 `board/README.md` 约定：只追加不改；每条含日期 / 接线 / 源码 commit / bitstream 路径与哈希 / 现象。
> 仿真与构建证据见 [`data/logs/2026-09-26-soc-onboard/`](../../../data/logs/2026-09-26-soc-onboard/README.md)。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测件 | Part A SoC（`src/riscv/soc_top.v` + `src/riscv/pynq_z2_top.v`），提交 `db9fe33`（`dev/rtl`，验证时未并入 main） |
| 验证人 | 验证线（waltercooper） |
| 日期 | 2026-09-26 |

## 硬件与连接

- 板卡：PYNQ-Z2（XC7Z020-1CLG400C），全队共用 1 块
- 连接：板载 Micro-USB（JTAG/UART）直连本机 Windows；PYNQ Linux 串口正常
- 供电 / 启动：正常 SD 卡启动（PYNQ v3.x）
- 本机：Vivado 2026.1

## bitstream

| 项 | 值 |
|:---|:---|
| 路径 | `build/run/soc/pynq_z2_soc.bit`（不入库，`.gitignore *.bit`） |
| SHA256 | `8D28219BBE8CE1022E6A73DFCD624E279101712DCFA4E58A76BC8BC18F53E71C` |
| 大小 | 4,045,766 B |

## 下载

- 方式：JTAG，Vivado **Hardware Manager（GUI）** Open Target → Auto Connect → 选器件 `xc7z020_1` → Program Device → 选上述 `.bit` → Program
- 等价命令行脚本：`board/scripts/program_soc.tcl`（按 `PART=xc7z020*` 唯一选器件）
- 结果：器件 `xc7z020_1` 配置成功

## 上板现象（实测）

| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 契约未定义 | `0001`（可重复） |
| 断电重下 | `1101` | ✅ `1101` |

## 说明：BTN0 松开后为何是 `0001`（非阻塞）

`main_v0.c` 把 `tohost` 当前值当种子：`sum = 4*seed + 13`。
软复位只复位核寄存器、**不清 dmem**；`tohost` 位于 `.tohost` 段（`start.S` 清的 `.bss` 不含它）→ 第二次运行 `seed = 13` → `sum = 65` → 低 4 位 `0001`。
断电/重新配置会重新初始化 dmem，故回到 `1101`。**属契约/测试覆盖缺口，非 RTL 缺陷**（详见 data/logs 证据 README）。

## 结论

- **Part A SoC 真实上板 PASS**（主判据：下载后 LED = `1101` 达成；复位清零正确）。
- 遗留：BTN0 释放后"重跑"的 LED 期望未在契约/tb 中定义，建议反馈 RTL 线补覆盖。

## 关联

- `data/logs/2026-09-26-soc-onboard/README.md`（仿真 + 构建 + 下载证据）
- `report/llm_log/2026-09-23-partA-soc-onboard.md`（被测件决策记录）
- `report/llm_log/2026-09-26-partA-soc-onboard-verify.md`（本次验证协作记录）
