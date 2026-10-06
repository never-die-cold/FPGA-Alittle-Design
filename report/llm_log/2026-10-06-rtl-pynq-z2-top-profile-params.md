# [2026-10-06] 协作记录：pynq_z2_top 模块——板级顶层透传 Part C 档位

> 标签：#soc #build #riscv #工具链
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/pynq_z2_top.v`）随板级档位与构建 profile 同批提交

## 1. 任务与初始提示词

让**板级顶层** `pynq_z2_top` 能选择 Part C 档位：`40/125 MHz × {nofwd, fwd, bht1, bht2}`，供 Vivado 综合与上板按档产出位流。

## 2. 模型第一版方案

`pynq_z2_top` 新增 `ENABLE_FORWARDING`、`BHT_MODE` 参数，透传给 `soc_top`（再由 `soc_top` 透传给 `core_top`）；时钟/复位链路（MMCM ÷25/÷8、锁定前保持复位）不变：

```verilog
soc_top #(
    .IMEM_INIT_FILE(IMEM_INIT_FILE), .DMEM_INIT_FILE(DMEM_INIT_FILE),
    .ENABLE_FORWARDING(ENABLE_FORWARDING), .BHT_MODE(BHT_MODE)
) u_soc ( .clk(core_clk), .rst_n(~reset_pipe[1]), .led(led) );
```

默认 `(1,0)` = Part B fwd 档，行为不变。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；默认档不变。
2. **未决**：四档位流的 Vivado WNS/DRC/资源与实机下载，仍由验证/上板线执行。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 板级要按档综合/上板 | 顶层需暴露档位并透传 | 增参并连接 `soc_top` | ✅ `tb_pynq_z2_clock_config` 断言显式档到达 `core_top` |

## 5. 最终结论

`pynq_z2_top` 支持四档位选择，默认等价 Part B；`tb_pynq_z2_clock_config` 断言默认档与显式档（`ENABLE_FORWARDING=0, BHT_MODE=2`）都确实到达 `core_top`。

## 6. 经验沉淀

- 板级顶层参数与仿真 tb 用**同一命名**，脚本/证据才能一一对照（`-tclargs ... bht2` ↔ `BHT_MODE=2`）。
- 板级只透传、不改时钟/复位，控制变量最小化。 #skill候选
