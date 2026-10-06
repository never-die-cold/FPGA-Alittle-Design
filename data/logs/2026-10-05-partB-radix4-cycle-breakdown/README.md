# Part B Radix-4 CoreMark 双档实测（2026-10-05）

## 一键复现

```bash
CPI_LOG_DIR="$PWD/data/logs/2026-10-05-partB-radix4-cycle-breakdown" \
  bash sim/scripts/run_cpi_matrix.sh
```

`environment.txt` 记录 HEAD、未提交 RTL/sim diff 指纹、Icarus 版本和 CoreMark hex
SHA-256；两档只切 `ENABLE_FORWARDING`，其余输入与计数窗口相同。

## 结果

| 档位 | cycles | retired | bubbles | CPI |
|:---|---:|---:|---:|---:|
| Radix-4 + fwd | 17,114,141 | 10,106,386 | 7,007,755 | 1.693399 |
| Radix-4 + nofwd | 19,057,438 | 10,106,386 | 8,951,052 | 1.885683 |

两档 CRC/观察值与 retired 一致；共同类别逐项相同；`raw_nofwd=1,943,297` 恰好
等于周期差；分类之和等于 bubbles。乘法等待为 `5,113,141 = 300,773 × 17`，
证明每条动态乘法占启动 1 拍加 Radix-4 迭代 16 拍。

- 仅转发：新双档 CPI 降幅 10.20%，通过 ≥8.0% 回归门禁；
- 仅 Radix-4：相对旧 fwd 周期下降 21.95%；
- 组合结果：相对原始 nofwd 周期下降 28.30%。

三项分别记账。`errors=1` 是短时 CoreMark 官方计时告警字段，CRC/golden 与 tb 判据
均通过；Vivado WNS 和资源仍待验证。
