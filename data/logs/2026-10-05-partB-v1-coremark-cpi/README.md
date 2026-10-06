# Part B v1 D3.1b：CoreMark 双档 CPI

- RTL commit：`a33d41e6929b00a057541a06aa8df9553c4bf703`
- Icarus Verilog：11.0 stable
- 固件 SHA-256：`ed229725ad95d0038af83b745704504c53b6176f6e927d9a147a34a39c762b11`
- 固件：`src/riscv_fw/coremark.hex`，2K profile，32 iterations
- 终止条件：首次提交 `tohost_exit` store
- 退休条件：MEM+WB `mem_valid`

## 一键复现

```bash
CPI_LOG_DIR="$PWD/data/logs/2026-10-05-partB-v1-coremark-cpi" \
  bash sim/scripts/run_cpi_matrix.sh
```

脚本退出码为 1，因为最终 `gain >= 25%` 门禁失败。两档仿真本身均 PASS。

## 原始结果

| 档位 | cycles | retired | bubbles | CPI |
|:---|---:|---:|---:|---:|
| v1+转发 | 21,926,509 | 10,106,386 | 11,820,123 | 2.169570 |
| v1无转发 | 23,869,806 | 10,106,386 | 13,763,420 | 2.361854 |

```text
gain = (2.361854 - 2.169570) / 2.361854 = 8.14%
要求 = 25%
判定 = FAIL
```

两档 `tohost=34713`，`crcfinal=0x8799`，其余 golden/CRC 全部一致。退休数相同，
且两档均满足 `cycles = retired + bubbles`。周期差 1,943,297 拍恰好等于气泡差，说明
结果来自同一动态指令流中转发消除的等待拍，不是计数分母变化。

## 文件

- `matrix.log`：一键脚本完整原始输出；
- `coremark-fwd.log` / `coremark-nofwd.log`：两档独立仿真日志；
- `summary.txt`：CPI、gain 与门禁判定；
- `environment.txt`：commit、Icarus 版本与固件 SHA-256。

本证据只能支持“功能一致、CPI 降幅 8.14%、25% 门禁未达标”。不得写成 Part B CPI
验收通过，也不得通过更换统计窗口或删减等待拍重算为更高数字。
