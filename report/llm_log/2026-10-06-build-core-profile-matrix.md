# [2026-10-06] 协作记录：build 脚本——SoC / Fmax 四档 profile 参数化

> 标签：#build #工具链 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`build/build_soc.tcl`、`build/build_fmax.tcl` 随板级档位同批提交

## 1. 任务与初始提示词

Part C 四档要做 Vivado 综合/时序/上板，构建脚本必须能**按档**综合且**证据互不覆盖**，同时**默认档保持与历史一致**。

## 2. 模型第一版方案

- **`build/build_soc.tcl`**：`-tclargs ?40|125? ?nofwd|fwd|bht1|bht2?`；档位映射到 `ENABLE_FORWARDING`/`BHT_MODE` generic，`synth_design -generic $core_generics`；profile 目录 `soc_40mhz`（fwd 保留历史名），其余加后缀（`soc_40mhz_bht2`）；位流 `pynq_z2_${profile}.bit`。
- **`build/build_fmax.tcl`**：新增 `-core_profile nofwd|fwd|bht1|bht2` 选项，按档设置综合 generic 以取该档 WNS/Fmax。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败。
2. **未决**：四档的实跑 Vivado 结果（WNS/DRC/资源/位流）由验证/上板线产出；本次只改脚本，**未在 WSL 运行 Vivado**。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 四档证据不能互相覆盖 | 分目录 + 分位流名 | profile 后缀命名 | ✅ 命令固定，历史 fwd 名不变 |
| 2 | 档位要真正进入综合 | `synth_design -generic` | `core_generics` 列表 | ✅ 与 `clock_cfg` 参数透传一致 |

## 5. 最终结论

`build_soc.tcl` 支持 `40/125 MHz × {nofwd,fwd,bht1,bht2}`，`build_fmax.tcl` 支持按档 OOC；默认档保留历史目录/位流命名，其余加后缀防覆盖。四档实跑与上板待验证线。

## 6. 经验沉淀

- 多档实验用**参数化 profile + 分目录/分文件名**，默认档保留历史命名以兼容既有证据。
- 构建脚本的档位开关要与 RTL 顶层参数、仿真 tb **同一命名**，形成“仿真-综合-上板”一条链。 #skill候选
