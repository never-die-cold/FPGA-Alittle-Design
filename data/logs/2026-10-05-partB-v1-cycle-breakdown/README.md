# Part B v1 CoreMark 分类周期证据

- 命令：`bash sim/scripts/run_cpi_matrix.sh`
- 镜像：`src/riscv_fw/coremark.hex`，2K profile / 32 iterations
- 对照：同一 RTL 与 tb，仅切 `ENABLE_FORWARDING`
- 窗口：复位释放至首次写 `tohost_exit`；退休按 `mem_valid`
- 门禁：`cycles = retired + bubbles`、分类和等于 bubbles、共同类别相等、
  RAW 差等于周期差、CRC/retired 一致、CPI 降幅 ≥8.0%

| 类别 | fwd | nofwd |
|:---|---:|---:|
| mul | 9,925,509 | 9,925,509 |
| div | 33 | 33 |
| load-use | 650,771 | 650,771 |
| raw_nofwd | 0 | 1,943,297 |
| control | 1,243,809 | 1,243,809 |
| other | 1 | 1 |
| bubbles | 11,820,123 | 13,763,420 |

结论：乘法等待占转发档总周期 45.27%；无转发 RAW 恰好解释 1,943,297 拍
周期差。原始输出见两份 `coremark-*.log`，机器汇总见 `summary.txt`。
