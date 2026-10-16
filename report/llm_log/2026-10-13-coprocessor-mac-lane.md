# [2026-10-13] 协作记录：协处理器 mac_lane 模块——signed INT8 乘法 lane

> 标签：#coprocessor #架构决策 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`fd66a4e`（J03 signed MAC lane）；本文档随本轮补录提交

## 1. 任务与初始提示词

J03 RTL 最小单元：实现 **signed INT8 乘法 lane**，作为 `dot8`/`mac_array` 的复用积木（累加不在本单元）。

## 2. 模型第一版方案

```verilog
module mac_lane (
    input  wire signed [7:0]  act_i,
    input  wire signed [7:0]  weight_i,
    output wire signed [15:0] product_o
);
    assign product_o = act_i * weight_i;
endmodule
```

signed × signed INT8（8×8）→ signed 16 位乘积。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 关键在**有符号语义**（`signed` 声明 + 8×8→16 位宽）。
2. **未决**：时序/综合/资源、DSP 映射未验证。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | signed 乘积易被当无符号 | 用 `signed` 声明，位宽 8×8→16 | `mac_lane` | ✅ `tb_mac_lane` 7 向量 PASS |

## 5. 最终结论

`mac_lane` 落地，`test` 覆盖 7 个 signed 向量全部 PASS；作为 `dot8`/`mac_array` 的基本积木。

## 6. 经验沉淀

- 把**最小乘法单元独立出来**便于复用与逐级对拍；
- signed INT8 乘积必须显式 `signed` 且位宽 **8×8→16**。 #skill候选
