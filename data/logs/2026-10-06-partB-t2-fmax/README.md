# Part B T2 核 OOC Fmax 复测（2026-10-06）

> 用途：验证线对 `dev/rtl@b93afaa`（T2：`id_ex` 分支比较解耦 ALU + `core_top` 转发接线简化，降深度）做 **Vivado 核 OOC 复测**，供 RTL 线判定是否实施 T3/T4。
> 口径：`build/build_fmax.tcl`（OOC post-route，默认 directive，`xc7z020clg400-1`，同 v0 基线方法 `docs/core_comparison.md` §3）。脚本的 `Fmax = 1/(period − WNS)` 是**单点 Slack 外推估计**，非某频率实测通过。
> 本目录归验证线；原始日志与报告副本只追加不改。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测提交 | `dev/rtl@b93afaa`（T2；未并入 main） |
| 命令 | `vivado -mode batch -source build/build_fmax.tcl -tclargs core_top <label> <period_ns> src/riscv` |
| 工具 | Vivado 2026.1；器件 `xc7z020clg400-1` |
| 验证人 | 验证线 ｜ 日期 2026-10-06 |

## 结果

| label | 约束 period | 约束频率 | WNS (ns) | TNS (ns) | 失败端点 | 该约束是否通过 | 外推 Fmax (MHz) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `v1_t2_11p52ns` | 11.520 ns | 86.81 MHz | **+0.187** | 0.000 | **0** | **通过** | 88.2 |
| `v1_t2_10ns` | 10.000 ns | 100.00 MHz | **−0.009** | −0.009 | **1** | **失败** | 99.9 |

### 最差路径前 3 条（source / destination / logic levels / route%）

**`v1_t2_11p52ns`（全部 MET）**
```text
#1  u_if_stage/flush_q_reg/C        -> u_pc/pc_reg[13]/D               | LL 9  | route 81.195% | data 11.151ns
#2  u_if_stage/flush_q_reg/C        -> u_mem_wb/mem_result_reg[13]/D   | LL 9  | route 81.189% | data 11.148ns
#3  u_if_stage/instr_hold_reg[3]/C  -> u_mem_wb/mem_addr_reg[31]/D     | LL 13 | route 67.567% | data 10.850ns
```

**`v1_t2_10ns`**
```text
#1 (VIOLATED -0.009)  u_if_stage/flush_q_reg/C  -> u_pc/pc_reg[15]/D   | LL 11 | route 72.385% | data 9.832ns
#2                   u_if_stage/flush_q_reg/C  -> u_pc/pc_reg[13]/D   | LL 11 | route 72.348% | data 9.818ns
#3                   u_if_stage/stall_q_reg/C  -> u_pc/pc_reg[17]/D   | LL 13 | route 66.014% | data 9.801ns
```

## 结论（事实 + 规则对照）

- **11.520 ns WNS +0.187 ≥ 0 → 实测达到 v0 基线 86.8 MHz**（外推 Fmax ≈ 88.2 MHz）。
- **10.000 ns WNS −0.009 < 0 → 未达 100 MHz**；**仅差 9 ps、仅 1 个失败端点**（外推 ≈ 99.9 MHz）。
- **关键路径走向**：两条运行的最差路径主要从 `u_if_stage` 控制寄存器（`flush_q`，另一条从 `stall_q`）出发，**终点多为 `u_pc/pc_reg`（PC 选择 / 目标地址）** → 按规则倾向 **T4**；但 10 ns 第 3 条仍从 **`stall_q`** 出发（T3 触发信号），T3/T4 由 RTL 线裁定。
- 这是**核 `core_top` 的 OOC 结果**；**SoC 125 MHz 不用于替代本门禁**（本次未做 SoC/上板）。

## 复现

```bat
vivado -mode batch -source build\build_fmax.tcl -tclargs core_top v1_t2_11p52ns 11.520 src\riscv
vivado -mode batch -source build\build_fmax.tcl -tclargs core_top v1_t2_10ns 10.000 src\riscv
```
- 原始日志：`v1_t2_11p52ns.log`、`v1_t2_10ns.log`
- 报告副本：`reports/v1_t2_11p52ns/`、`reports/v1_t2_10ns/`（`timing_impl.rpt` / `timing_worst_paths.rpt` / `timing_synth.rpt` / `utilization_*` / `design_analysis_impl.rpt`）

## 边界

- 只读复测，不改 RTL / tb；`b93afaa` 未并入 main
- `build/reports/fmax/` 为构建设备目录（忽略）；关键报告已复制入本目录
- `build_fmax.tcl` 不生成 check_timing（check_timing 只在 SoC 构建里）
