# Part B v1 D3.1a：退休/CPI 口径自检

- RTL commit（工作区基点）：`05cbf7714dd50026da03adb6d64eeb4869259c20`
- Icarus Verilog：11.0 stable
- Python：3.10.12
- 固件：`src/riscv_fw/bench_v0_1.hex`
- 终止条件：首次提交 `tohost_exit` store
- 退休条件：同一统计窗口内 `dut.mem_valid == 1`

## 一键命令

```bash
bash sim/scripts/run_iverilog.sh bench_fwd
bash sim/scripts/run_iverilog.sh bench_nofwd
python3 data/scripts/cpi_harness.py \
  data/logs/2026-10-05-partB-v1-cpi/bench-fwd.log benchmark-v0.1-fwd
python3 data/scripts/cpi_harness.py \
  data/logs/2026-10-05-partB-v1-cpi/bench-nofwd.log benchmark-v0.1-nofwd
```

## 结果

| 档位 | cycles | retired | bubbles | CPI（精确重算） |
|:---|---:|---:|---:|---:|
| v1+转发 | 3447 | 1205 | 2242 | 2.861 |
| v1无转发 | 3874 | 1205 | 2669 | 3.215 |

短 benchmark 降幅为 `(3874-3447)/3874 = 11.02%`。该程序仅用于 D3.1a
口径自检；正式 `>=25%` 门禁必须由 D3.1b 的同一 CoreMark 双档结果判定。

首次运行曾出现 fwd/nofwd 退休数 1206/1205。退休 trace 证明两档动态序列一致，
多出的唯一一条是终止 store 后的自旋 `jal x0,0`。计数器增加 `!exit_seen` 窗口门控后，
两档均为 1205，终止 store 计入、终止后的自旋不计。

## 全量回归状态

`bash sim/scripts/run_iverilog.sh all` 的核、CoreMark、SoC 与全部 Verilog 视觉测试均
PASS；总命令最终退出码为 1，因为当前环境没有 `python` 命令，最后的既有视觉 Python
门禁报 `python: command not found`。因此本轮不得写成“all 全绿”。原始输出见 `all.log`。

文件说明：

- `bench-fwd.log` / `bench-nofwd.log`：修正窗口后的短 benchmark 原始日志；
- `bench-*-retire.trace`：定位终止后多计一条的退休序列；
- `all.log`：全量回归原始输出及环境阻塞。
