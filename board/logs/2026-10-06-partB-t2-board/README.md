# Part B T2 SoC 真实上板记录（2026-10-06）

> 用途：`dev/rtl@b93afaa`（T2）的 40 MHz SoC 位流在真实 PYNQ-Z2 上的 JTAG 下载与肉眼验收。
> 按 `board/README.md` 约定：只追加不改；与 v0 / 前一版 v1 证据**分开**。
> 仿真与构建证据见 [`data/logs/2026-10-06-partB-t2-board/`](../../../data/logs/2026-10-06-partB-t2-board/README.md)。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测件 | v1 三级流水核 + SoC（T2：`id_ex` 分支比较解耦 + `core_top` 转发接线简化），提交 `dev/rtl@b93afaa` |
| 核时钟 | **40 MHz**（安全基准档） |
| 验证人 | 验证线 ｜ 日期 2026-10-06 |

## 硬件与连接

- 板卡：PYNQ-Z2（XC7Z020-1CLG400C），全队共用
- 连接：板载 Micro-USB（JTAG）直连本机 Windows；本机 Vivado 2026.1

## bitstream

| 项 | 值 |
|:---|:---|
| 路径 | `build/run/soc_40mhz/pynq_z2_soc_40mhz.bit`（不入库） |
| SHA256 | `E7BB4041FD13D3C4FE28FCEC797A29E2F8180525F28AB63842FA87314F7761E5` |
| 大小 | 4,045,766 B |
| 构建时序 | WNS **+7.388 ns**（40 MHz 档） |

## 下载

- 方式：JTAG，`board/scripts/program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit`
- 结果：`FOUND: xc7z020_1` → `PROGRAM PASSED`

## 上板现象（实测）

| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 依赖旧 DMEM（`design_v1.md` §4 允许） | ✅ 与之前一致 |

## 结论

- **T2 代码 40 MHz 档真实上板验证通过**：约定现象 LED=`1101`（静止）达成，且与 v0 / 前一版 v1 语义一致。
- 本次**只做 40 MHz 档**；T2 核 OOC Fmax（11.52 ns 通过 / 10 ns 差 9 ps）见 `data/logs/2026-10-06-partB-t2-fmax/`。

## 关联

- `data/logs/2026-10-06-partB-t2-board/README.md`（XSim + 构建 + 下载证据）
- `report/llm_log/2026-10-06-partB-t2-onboard-verify.md`（本次协作记录）
- `board/logs/2026-10-05-partB-v1-onboard/`（前一版 v1 上板，独立）
