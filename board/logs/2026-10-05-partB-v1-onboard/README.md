# Part B v1（三级流水 + 转发）真实上板记录（2026-10-05）

> 用途：`dev/rtl@85b94a5` 的 v1 核（三级流水 + 转发）在真实 PYNQ-Z2 上的 JTAG 下载与肉眼验收。
> 按 `board/README.md` 约定：只追加不改；与 v0（`board/logs/2026-09-26-soc-onboard/`）证据**分开**，不借用 v0 证据表述 v1。
> 仿真与构建证据见 [`data/logs/2026-10-05-partB-v1-onboard/`](../../../data/logs/2026-10-05-partB-v1-onboard/README.md)。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测件 | v1 三级流水核 + `soc_top`/`pynq_z2_top`（双频 40/125），提交 `dev/rtl@85b94a5` |
| 核时钟 | **40 MHz**（安全基准档；125 MHz 档时序 FAIL，未使用） |
| 验证人 | 验证线 ｜ 日期 2026-10-05 |

## 硬件与连接

- 板卡：PYNQ-Z2（XC7Z020-1CLG400C），全队共用
- 连接：板载 Micro-USB（JTAG）直连本机 Windows
- 供电 / 启动：正常 SD 卡启动；本机 Vivado 2026.1

## bitstream

| 项 | 值 |
|:---|:---|
| 路径 | `build/run/soc_40mhz/pynq_z2_soc_40mhz.bit`（不入库） |
| SHA256 | `5AA58E39451CA7F31EB46545988FDFA9CE556AE17C539932EDA8CAE38CDFB4F4` |
| 大小 | 4,045,766 B |

## 下载

- 方式：JTAG，`board/scripts/program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit`
- 结果：`FOUND: xc7z020_1` → `PROGRAM PASSED`

## 上板现象（实测）

| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 依赖旧 DMEM（`design_v1.md` §4 允许） | `0001`（与 Part A/v0 一致） |

## 结论

- **v1 三级流水真实上板 PASS**：约定现象 LED=`1101` 达成，且与 v0 语义一致。
- 125 MHz 档时序未收敛，按交接单未生成/未使用该档位流（非阻塞加分项）。

## 关联

- `data/logs/2026-10-05-partB-v1-onboard/README.md`（XSim + 双频构建 + 下载证据）
- `report/llm_log/2026-10-05-partB-v1-onboard-verify.md`（本次验证协作记录）
- `docs/partB-rtl-handoff.md`（团队交接单）
- `board/logs/2026-09-26-soc-onboard/`（v0/Part A 上板证据，独立）
