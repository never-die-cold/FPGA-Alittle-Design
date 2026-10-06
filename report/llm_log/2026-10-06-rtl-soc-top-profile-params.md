# [2026-10-06] 协作记录：soc_top 模块——暴露 Part C 档位参数（ENABLE_FORWARDING / BHT_MODE）

> 标签：#soc #riscv #架构决策 #工具链
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/soc_top.v`）随板级档位与构建 profile 同批提交

## 1. 任务与初始提示词

Part C 的四种配置（转发开/关 × BHT 关 / 1-bit / 2-bit）不仅要在仿真里跑，还要能在 **SoC / 板级**按档综合与上板。要求把档位从顶层一路透传到 `core_top`，且**默认档行为不变**。

## 2. 模型第一版方案

`soc_top` 新增两个参数并透传给 `core_top`：

```verilog
module soc_top #(
    parameter IMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex",
    parameter DMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex",
    parameter ENABLE_FORWARDING = 1'b1,   // 默认 = Part B 转发档
    parameter [1:0] BHT_MODE = 2'd0       // 默认 = BHT 关
) ( ... );
core_top #(.ENABLE_FORWARDING(ENABLE_FORWARDING), .BHT_MODE(BHT_MODE)) u_core ( ... );
```

默认 `(1,0)` 与 Part B 已验证配置一致，行为不变。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；默认档不变。
2. **未决**：四档在 Vivado 综合/时序/资源与板级上板，仍由验证/上板线执行。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 板上要能跑 BHT 档 | 档位必须从顶层透传到 core_top | `soc_top` 增参并连接 `u_core` | ✅ `tb_pynq_z2_clock_config` 断言参数到达 `core_top` |

## 5. 最终结论

`soc_top` 现支持四档（转发开/关 × BHT 关/1/2），默认 `ENABLE_FORWARDING=1、BHT_MODE=0`，与 Part B 等价。`clock_cfg` 断言默认档与显式档都确实到达核。

## 6. 经验沉淀

- 顶层开关要**一路透传到底层**，并用 tb **层次化断言“参数确实到达核”**，避免“以为传了其实没传”。
- 默认值必须等于已验证配置，保证不改变既有行为。 #skill候选
