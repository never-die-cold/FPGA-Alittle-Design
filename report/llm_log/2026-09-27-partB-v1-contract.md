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
3. **尚未定稿**：存储器与 regfile 三级语义、新增模块端口与位宽、CPI/回归/Vivado/板级验收、待拍板决策 + v0/plan 交叉引用仍为未勾项。
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
