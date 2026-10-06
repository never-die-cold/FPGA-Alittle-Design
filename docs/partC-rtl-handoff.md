# Part C RTL 交接单

日期：2026-10-06。状态：三级核、转发、Radix-4 与可切换 BHT 已完成 Icarus 功能回归；
arch-test 四档、XSim、Vivado WNS/资源和上板仍待验证。

## 一键复现

```bash
bash sim/scripts/run_iverilog.sh v1_nofwd
bash sim/scripts/run_iverilog.sh v1_fwd
bash sim/scripts/run_iverilog.sh v1_fwd_bht1
bash sim/scripts/run_iverilog.sh v1_fwd_bht2
bash sim/scripts/run_iverilog.sh all
```

四档均使用 `tb_core_coremark.v`、同一 `coremark.hex`、同一复位/终止条件和计数代码；
仅 elaboration 参数 `ENABLE_FORWARDING/BHT_MODE` 不同。

## RTL 线实测锚点

| 入口 | cycles | retired | CPI | lookup | hit | miss |
|:---|---:|---:|---:|---:|---:|---:|
| `v1_nofwd` | 19057438 | 10106386 | 1.886 | 0 | 0 | 0 |
| `v1_fwd` | 17114141 | 10106386 | 1.693 | 0 | 0 | 0 |
| `v1_fwd_bht1` | 16335562 | 10106386 | 1.616 | 1854101 | 1587055 | 267046 |
| `v1_fwd_bht2` | 16232079 | 10106386 | 1.606 | 1854101 | 1690538 | 163563 |

四档 CRC 均为 `e9f5/e714/1fd7/8e3a/8799`。2-bit 命中率约 91.18%，相对
`v1_fwd` 净省 882062 拍（约 5.15%）；当前同 RTL 的 `v1_nofwd` 到
`v1_fwd_bht2` 为约 14.83%。这些是 Icarus 数据，不代表 Vivado 时序或板级结果。

## 验证线待办

1. 记录验收 commit，四档跑 arch-test 同集合并核对签名。
2. 用 Vivado 2026.1 XSim 对拍四档 cycles、CRC、lookup/hit/miss。
3. 核 OOC/SoC 分开跑 WNS、Fmax、LUT/FF/BRAM；BHT 开关只用参数切换。
4. WNS≥0 后方可生成位流；实际下载并观察约定 LED 后才能写“已上板”。
