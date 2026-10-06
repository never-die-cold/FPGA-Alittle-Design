# Part B Radix-4 CoreMark 实测

## 改动与目的

`muldiv.v` 的乘法从 Radix-2 32 次迭代改为 Radix-4 16 次迭代，除法与外部握手
接口不变。模块级边界、整核 M 流控、全量回归和 arch-test 3×2 已通过。

## 双档结果

| 档位 | cycles | retired | CPI | mul wait | RAW wait |
|:---|---:|---:|---:|---:|---:|
| Radix-4 + fwd | 17,114,141 | 10,106,386 | 1.693399 | 5,113,141 | 0 |
| Radix-4 + nofwd | 19,057,438 | 10,106,386 | 1.885683 | 5,113,141 | 1,943,297 |

两档 CRC、观察值和 retired 一致；分类闭合，且 RAW 差等于总周期差。相对旧 fwd
的 21,926,509 cycles，Radix-4 独立节省 4,812,368 拍，即 21.95%。新双档只切
转发时降幅为 10.20%；Radix-4 + fwd 相对原始 nofwd 的组合降幅为 28.30%。

这些收益不得混记：21.95% 属于快速乘法，10.20% 是新工作点上的转发差异，28.30%
才是两项组合结果。预测的 17,114,141 cycles 与实测完全一致，但这仍只是功能仿真；
在 Vivado WNS≥0、资源报告入档前，Radix-4 不能完成时序验收。

## 证据

- `data/logs/2026-10-05-partB-radix4-cycle-breakdown/`：双档原始日志与环境；
- `data/logs/2026-10-05-partB-radix4-arch-test/`：3×2 签名与 RV32IM；
- `bash sim/scripts/run_iverilog.sh all`：退出码 0。
