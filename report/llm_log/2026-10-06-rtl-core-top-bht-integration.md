# [2026-10-06] 协作记录：core_top 模块——BHT 预测 / 误预测恢复接入（Part C）

> 标签：#riscv #流水线 #架构决策 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/core_top.v`）随 Part C 契约 §16/D17 与四档入口同批提交；配套模块见 `2026-10-06-rtl-branch-predict.md`、`2026-10-06-rtl-id-ex-stage-branch-valid.md`

## 1. 任务与初始提示词

把 BHT 预测接入 `core_top`：**预测 taken 时提前取目标（正确则零冲刷）**；**误预测时恢复正确 PC 并冲刷错误路径年轻槽**（不得写 regfile/DMEM、不得启动 muldiv）；保持对外端口不变、`soc_top` 零改动可编译；四档用同一 RTL 只切参数。

## 2. 模型第一版方案

新增/改写控制方程：

```verilog
assign branch_resolve    = ex_accept && branch_valid;
assign branch_mispredict = branch_resolve && (bp_predict_taken != branch_taken);
assign jump_redirect     = ex_accept && jump_taken;
assign predicted_redirect= branch_resolve && bp_predict_taken && !branch_mispredict;
assign redirect          = jump_redirect || branch_mispredict;
assign recovery_target   = jump_redirect ? redirect_target :
                           (branch_taken ? redirect_target : (pc_id + 32'd4));
assign fetch_addr        = redirect ? recovery_target :
                           (predicted_redirect ? redirect_target : pc);
assign pc_sel            = (redirect || predicted_redirect) ? 2'b01 : 2'b00;
```

实例化 `branch_predict`：lookup on (`instr_valid && branch_valid`, `pc_id`)，update on (`branch_resolve`, `pc_id`, `branch_taken`)；暴露事件线 `bp_lookup_event / bp_hit_event / bp_miss_event` 供 tb 统计。`if_stage` 取指地址改接 `fetch_addr`。顶层参数 `BHT_MODE` 透传。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 功能全 PASS（四档 CoreMark CRC/retired 一致、`all` 64 PASS）；**未决**：核 OOC/SoC 的 Vivado WNS/资源、125 MHz 与实机仍由验证/上板线执行。
2. 新增 BHT lookup mux 会改变关键路径，必须复测核 OOC Fmax（预期小幅，待验证线）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 预测正确不能产生气泡/冲刷 | 正确预测 ≠ redirect | 分离 `predicted_redirect` 与 `redirect` | ✅ 四档结果一致 |
| 2 | 误预测需恢复正确 PC | 恢复地址按 taken/not-taken 区分 | `recovery_target = taken?target:pc_id+4` | ✅ `bht_flow` 0/1/2 档 PASS |
| 3 | 错误路径不得有副作用 | 复用 `valid=0` 门控 | 错误路径槽无效 | ✅ `wrong-path store/RF/muldiv suppressed`（0/1/2 档） |
| 4 | 关闭 BHT 必须等价 Part B | `BHT_MODE=0` 恒不跳 | 参数化 | ✅ `v1_fwd` 与 bht_off 一致 |

## 5. 最终结论

Part C 接入完成。四档 CoreMark（同 tb/hex/计数代码，只切 `ENABLE_FORWARDING`+`BHT_MODE`）：

| 档 | cycles | retired | CPI |
|:---|---:|---:|---:|
| v1_nofwd | 19,057,438 | 10,106,386 | 1.885683 |
| v1_fwd（BHT 关） | 17,114,141 | 10,106,386 | 1.693399 |
| v1_fwd + 1-bit BHT | 16,335,562 | 10,106,386 | 1.616374 |
| v1_fwd + 2-bit BHT | 16,232,079 | 10,106,386 | 1.606122 |

- `gain_fwd = 10.20%`；`gain_total(2-bit) = 14.83%`；BHT 净贡献（2-bit）= 0.0873 CPI。**25% 为组合尽力目标，未达，如实记录**。
- `run_iverilog.sh all` **64 PASS、0 unexpected FAIL**。

## 6. 经验沉淀

- **正确预测与 redirect 分离**：正确预测只改取指路径，不冲刷；只有 `jump_redirect || mispredict` 才 flush。
- 误预测恢复地址必须区分 taken（跳目标）/ not-taken（`pc_id+4`）；错误路径靠 `valid=0` 门控，杜绝副作用。
- **关闭档必须逐拍等价 Part B**，保证单变量对照。
- 统计用**事件线**（tb 层次化引用），不占片上资源、不污染 Fmax。
- #skill候选
