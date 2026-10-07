# [2026-10-06] 协作记录：core_top 模块——PC/flush 选择展开为互斥掩码相或（降深度）

> 标签：#riscv #流水线 #时序优化 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/core_top.v`）随本轮 PC/flush 降深度同批提交；配套见 `2026-10-06-rtl-if-stage-valid-only-flush.md`、`2026-10-06-rtl-id-ex-stage-branch-target.md`

## 1. 任务与初始提示词

`core_top` 里 PC 地址/`pc_sel`/`redirect` 是一串**优先级选择链**（`redirect ? … : predicted ? … : pc`、`redirect_target + 4`），叠加在 `instr_hold → pc_reg` 关键路径上。要求**保持三级**、不改误预测 1 槽/正确预测零气泡，把地址选择改为**互斥条件掩码相或**，并**把控制（recover_valid/redirect）与地址数据选择分离**。

## 2. 模型第一版方案

按四种互斥方向组合展开：

```verilog
assign branch_fetch_taken   = branch_resolve && branch_taken;
assign branch_recover_taken = branch_resolve && branch_taken && !bp_predict_taken;
assign branch_recover_fall  = branch_resolve && !branch_taken && bp_predict_taken;
assign predicted_redirect   = branch_resolve && branch_taken && bp_predict_taken;
assign recover_valid        = jump_redirect || branch_recover_taken || branch_recover_fall;
assign redirect = recover_valid;  assign flush = redirect;
assign fallthrough_pc = pc_id + 32'd4;
assign fetch_addr = ({32{jump_redirect}} & redirect_target) |
                    ({32{branch_fetch_taken}} & branch_target) |
                    ({32{branch_recover_fall}} & fallthrough_pc) |
                    ({32{!(jump_redirect||branch_fetch_taken||branch_recover_fall)}} & pc);
assign pc_sel  = (jump_redirect||branch_fetch_taken||branch_recover_fall) ? 2'b01 : 2'b00;
assign pc_target = ({32{jump_redirect}} & redirect_target) |
                   ({32{branch_recover_taken}} & branch_target) |
                   ({32{branch_recover_fall}} & fallthrough_pc) |
                   ({32{predicted_redirect}} & branch_target_next);
```

`recover_pc` 为组合观察值，**不新增恢复寄存器/流水级**。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；**未决**：优化后 WNS/Fmax/资源未验证，交验证线实跑 11.520 ns 与四档 10 ns。
2. 不保证综合后逻辑级数；布线占比与新增扇出可能影响结果。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 优先级选择链深 | 用互斥条件掩码相或替代串行优先级 | 展开 `fetch_addr`/`pc_target` | ✅ `pc_control` **768 例等价** |
| 2 | redirect 与地址选择纠缠 | 分离 `recover_valid`（控制）与地址数据 | 独立表达式 | ✅ `bht_flow` 三档 PASS |
| 3 | 不能加流水级 | `recover_pc` 仅组合观察 | 无新寄存器 | ✅ 四档 cycles 不变（19057438/17114141/16335562/16232079） |

## 5. 最终结论

`core_top` 的 PC/flush 地址选择改为**互斥条件掩码相或**，去掉了 `redirect→predicted→pc` 与 `redirect_target+4` 的长优先级链；`recover_valid/redirect` 控制与地址数据分离；**三级不变、功能等价**（768 例 + 四档 CoreMark CRC/retired/cycles 全一致）。**时序收益待 Vivado 复测**（`11.520 ns` 与四档 `10 ns`）。

## 6. 经验沉淀

- 长**优先级选择链**可改写为**互斥条件掩码相或**（`{32{cond}} & value` 相或），缩短路径且逻辑等价；
- **控制（redirect/valid）与地址数据分开计算**，避免互相拖深；
- 降深度时守住“不加流水级 / 不加恢复寄存器”，保证三级与四档语义不变。 #skill候选
