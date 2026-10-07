# Part C 主档（v1_fwd+BHT2）真实上板记录（2026-10-06）

> 用途：`dev/rtl@3c6b794` 的 Part C 主档 `v1_fwd_bht2` 的 40 MHz SoC 位流在真实 PYNQ-Z2 上的 JTAG 下载与肉眼验收。
> 按 `board/README.md` 约定：只追加不改；与 v0 / Part B 证据**分开**，不借用低档证据。
> 仿真/构建/OOC 证据见 [`data/logs/2026-10-06-partC-verify/`](../../../data/logs/2026-10-06-partC-verify/README.md)。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测件 | v1 三级流水 + 转发 + 2-bit BHT（主档 `bht2`），提交 `dev/rtl@3c6b794` |
| 核时钟 | 40 MHz（安全基准档） |
| 验证人 | 验证线 ｜ 日期 2026-10-06 |

## 硬件与连接

- 板卡：PYNQ-Z2（XC7Z020-1CLG400C），全队共用
- 连接：板载 Micro-USB（JTAG）直连本机 Windows；本机 Vivado 2026.1

## bitstream

| 项 | 值 |
|:---|:---|
| 路径 | `build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit`（不入库） |
| SHA256 | `0D670A2315DBBC2D48FBEBCDDE8F99B791686B04D0E65EB7CC6C7A921C829BB9` |
| 大小 | 4,045,766 B |
| 构建时序 | WNS **+5.599 ns**（40 MHz 档，profile=bht2） |

## 下载

- 方式：JTAG，`board/scripts/program_soc.bat build\run\soc_40mhz_bht2\pynq_z2_soc_40mhz_bht2.bit`
- 结果：`FOUND: xc7z020_1` → `PROGRAM PASSED`

## 上板现象（实测）

| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 依赖旧 DMEM（契约 §4 允许） | ✅ 与之前一致 |

## 结论

- **Part C 主档（v1_fwd+BHT2）40 MHz 档真实上板验证通过**：约定现象 LED=`1101`（静止）达成，与 v0/Part B 语义一致。
- 核 OOC 频率另见 `data/logs/2026-10-06-partC-verify/`（主档 bht2 @10ns WNS −1.955，外推 Fmax ≈83.6 MHz）——**核频率与 SoC 40 MHz 档分开表述，不得混用**。

## 关联

- `data/logs/2026-10-06-partC-verify/README.md`（功能 + 四档 + OOC + 构建证据）
- `report/llm_log/2026-10-06-partC-verify.md`（本次协作记录）
