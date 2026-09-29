# [2026-09-27] 协作记录：Part B 启动——v1 三级流水 + 转发契约（design_v1.md）分章冻结

> 标签：#riscv #架构决策 #流水线 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：基线 `962a4f5`（Part A 收口）；本记录与 `src/riscv/design_v1.md`（新增草案）同批提交

## 1. 任务与初始提示词

Part A 收口后启动 Part B（三级流水 + 数据转发）。按古法编程 + `AGENTS.md` 开工，要求**先冻结 v1 契约文档，再落 RTL**：

> 把 v0 的两级 `IF / ID+EX+MEM+WB` 重构为三级 `IF / ID+EX / MEM+WB`；加入可配置的数据转发与冒险处理，保持 RV32IM 语义不变；形成 `v1+转发` 与 `v1无转发` 两档同核对照；记录 CPI、Fmax、WNS 与资源，作为 Part C 分支预测的起点。

`design_v1.md` 头部约定：定稿后为 Part B/C 的流水、转发、冒险与模块接口唯一权威；v0 仍以 `design_v0.md` 为准。

## 2. 模型第一版方案

新增 `src/riscv/design_v1.md` 草案，按小节逐段冻结：

- §1 目标/边界/优先级：功能正确 > 转发完整 + CPI 对比 > 提频；125 MHz 为加分项，L3 保底。
- §2 版本基线：v0 用 commit/tag 固定；v1 无转发/有转发**同一份 RTL + 顶层参数 `ENABLE_FORWARDING`** 切换，禁止复制第二份 `core_top`。
- §3 三级术语 + §4 总体原则（load-use 定 1 拍、转发覆盖 ALU/branch/JALR/store/muldiv、decode 出 `uses_rs1/uses_rs2`、taken 冲刷 1 年轻槽、M 在 ID+EX 等待）。
- §5 稳态拍序与两边界（IF/ID、ID+EX/MEM+WB）。
- §6 流水字段与裁剪（IF/ID 字段、`mem_*` 字段、ID+EX 后裁剪、WB 提交记录不构成第四级）。
- §7 边界动作与复位（stall 让旧 MEM+WB 提交一次后**排空**，禁止冻结重复提交）。
- §8 转发契约（三类来源 EX→EX/MEM→EX/WB→EX、统一命中式、mux 优先级 `EX>MEM>WB>RF`、load-use 例外、转发值覆盖范围、开关与复现入口）。
- §9 冒险/停顿/冲刷（RAW 比较、开/关转发停顿方程、1 拍 load-use 拍序、redirect 与边界控制优先级）。
- §10 RV32M 多拍流控（`pending` 属 `core_top` ID+EX、`start/wait/done` 方程、三级暂停范围、done 结果经 MEM+WB 统一写回）。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **Codex 常规文件写入工具被 WSL 挂载阻止**：`apply_patch` 报 `fs sandbox helper failed ... unsupported host mount at /mnt/wslg/distro`；改用已授权的**仓库内 `python3` 写入**应用同一段内容。
2. **契约“边写边审”多小节**：早期只有 §1–§4 且状态清单全未勾；随 1B-2/1B-5 等小步逐节补齐并同步勾选。
3. **定稿候选已补齐**：§11–§15 已覆盖存储器/regfile、模块接口、指标门禁和 D1–D15；等待用户最终确认。
4. 本轮为**纯文档**，未运行 RTL 回归（无代码可跑）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `apply_patch` 报 sandbox 错误 | WSL 嵌套挂载阻止常规写入工具 | 改用仓库内 `python3` 写入同一内容 | ✅ 文档落盘，`git status` 只见 `design_v1.md` |
| 2 | 契约缺 §5 及以后 | 需按古法拆步逐节补 | 追加 §5–§10 并同步状态清单 | ✅ 各节自检锚点匹配 |
| 3 | RV32M 流控归属歧义 | `pending` 应属 `core_top` 的 ID+EX，不入 MEM+WB | §10 冻结归属与 `start/wait/done` 方程 | ✅ 文档一致 |
| 4 | 对照档如何产生 | 禁止手改源码造档 | 顶层参数 `ENABLE_FORWARDING` + 脚本入口 | ✅ 写入 §8.5 |

## 5. 最终结论

产出 `src/riscv/design_v1.md` 草案：三级流水拍序、两边界与字段、转发真值表与 mux 优先级、load-use/flush/stall 拍序、RV32M 多拍流控均已冻结为文本契约；对照档统一用顶层参数 `ENABLE_FORWARDING` 产出 `v1_fwd` / `v1_nofwd` 两档，验收入口预留 `bash sim/scripts/run_iverilog.sh v1_fwd|v1_nofwd`。仍待定稿：存储器/regfile 三级语义、模块端口位宽、CPI/回归/Vivado/板级验收、待拍板决策。**本轮仅文档，未运行回归。**

## 6. 经验沉淀

- 触发条件：流水线重构前先冻结微架构契约。
- 排查步骤：
  1. 用**显式 `valid`** 作为副作用门控，NOP 只做波形可读，不能代替门控；
  2. 性能对照档用**同一 RTL + 顶层参数**，禁止复制源码或手改生成；
  3. 转发优先级固定 `EX>MEM>WB>RF`，load-use 的 1 拍 interlock **优先于** mux；
  4. stall 必须让旧 MEM+WB **提交一次后排空**，禁止冻结旧槽重复提交；
  5. 多拍单元的 `pending` 属前端流控，结果经统一写回级提交，保证 retire 口径一致。
- 适用范围：换流水级数 / 换转发策略均成立；“先契约后 RTL + 单参数对照档”可复用。 #skill候选

## 7. 2026-09-28：契约定稿候选

本轮继续完成 §11–§15：存储器/regfile 三级语义、四个新增/改造模块接口、
`core_top` 参数与连接、CPI/验证门禁，以及已确认的 D1–D15。当前没有未决
微架构选项；全文等待用户最终确认后冻结，之后才进入 RTL 实现。

### 7.1 相对 v0 的关键差异

| 项目 | v0 | v1 契约 |
|:---|:---|:---|
| 物理流水 | IF / ID+EX+MEM+WB | IF / ID+EX / MEM+WB |
| RAW | 无数据停顿 | 转发；load-use 固定停 1 拍 |
| 对照档 | 单一 v0 | 同 RTL 参数切 v1 开/关转发 |
| 提交 | 执行级同拍写回 | MEM+WB 唯一提交级 |
| RV32M | done 同拍直接写回 | done 结果先进入 MEM+WB，再统一写回 |
| 主 CPI 比较 | 参考锚点 | v1+转发相对 v1无转发降 ≥25% |
| 提频 | v0 板级 40 MHz | 125 MHz 非阻塞；记录实际最高通过频率 |

### 7.2 决策与证据状态

- D1–D15 的选项、被否方案与理由完整列在 `design_v1.md` §15；
- D3 固定同 RTL + `ENABLE_FORWARDING`，脚本入口为 `v1_fwd/v1_nofwd`；
- D4 创建 `partA-v0` 标签并固定指向 `962a4f5`；
- D15 到时间盒仍未通过 125 MHz 时，保留最高通过频率并启用“两级+完整转发”L3；
- 本阶段只有文档锚点与格式检查，没有 v1 RTL、仿真、Vivado 或新上板证据。

### 7.3 进入阶段 2 前状态

契约正文已齐全，但 `forwarding.v`、`hazard.v`、`id_ex_stage.v`、
`mem_wb_stage.v` 和 v1 `core_top` 均未实现。用户最终确认契约后，才按古法编程
进入 RTL 单步实现；任何实现偏差必须先回写契约。

### 7.4 契约总复核

1. **load→branch**：用户说明 load 在拍 t 末写回，branch 在拍 t 因
   `ex_accept=0` 保持，拍 t+1 用新值裁决并拉高 redirect；经补充确认，
   flush 在拍 t+1 发出，被杀死的年轻槽在拍 t+2 表现为控制气泡。判定：通过。
2. **RV32M**：用户完整复述“转发操作数就绪→单拍 start/置 pending/立即 wait
   →busy 时前端保持且旧 MEM+WB 排空→单拍 done 送入 MEM+WB→下一拍统一
   写回→后继转发”，并说明 pending 与唯一提交点如何防重复。判定：通过。
3. **指标与板级**：用户确认两档固定程序、初始状态、终止条件、计数代码和流程；
   125 MHz 未过而 80 MHz 通过时记录 80 MHz 并启用两级+完整转发 L3；
   bitstream 必须实际下载且观察 LED=`1101` 才能称为已上板。判定：通过。

总复核通过；契约保持“定稿候选”，等待用户明确确认冻结后进入阶段 2。
> 2026-09-28 用户最终确认：冻结 `design_v1.md`，进入阶段 2 拆步规划；首个 RTL 小步仍需用户确认框架后启动。
