# [2026-09-11] 协作记录：v0 接口冻结——RV32I 两级流水设计决策与不依赖 Vivado 的仿真通路

> 标签：#riscv #架构决策 #仿真 #工具链
> 平台：OpenCode ｜ 模型：deepseek-flash (deepseek/deepseek-flash)
> 相关 commit：`cf78db6`（设计文档）、`6cc7d57`（仿真骨架）、`0373ada`（文档修正）+ 本条记录本身

## 1. 任务与初始提示词

issue #1/#2 均为硬件项、暂时无法推进，用户问"还有什么可以做"，多选后确定：

> "1. Part A 接口设计文档, 2. iverilog + 冒烟 tb, 5. 只做文档杂项"
> "开始细分commit执行"

设计决策采用问答确认：指令/数据存储、M 扩展排期、tohost 观测、核与存储边界四问。

## 2. 模型第一版方案

- 把 plan.md 中 9/21 的「模块划分定接口」提前，产出 `src/riscv/design_v0.md`（模块表 + 端口信号表 + 控制真值表 + 决策记录）；
- 用 MSYS2 的 iverilog 13.0 做 Vivado 未到货前的过渡仿真，先写 `tb_core_smoke.v` 骨架 + 一键脚本；
- 模型对 M 扩展的建议是"一次到位 RV32IM"（选项标注推荐）。

## 3. 失败现象（真实偏差）

1. **仿真工具环境不可用**：`iverilog` 编译时以 `0xC0000139 (ENTRYPOINT_NOT_FOUND)` 退出——本机 PATH 中 `C:\mingw64\bin` 排在 `ucrt64\bin` 前，抢加载了不匹配的 MinGW DLL（`iverilog -V` 不触发，真正编译才暴露）。
2. **tb 真实语法 bug**：`imem_rdata` 声明为 `wire` 却被存储器模型过程赋值，iverilog 报 `not a valid l-value for a procedural assignment`（编译期即失败）。
3. **脚本空 glob 失败模式不友好**：`src/riscv/*.v` 尚未存在时，未开 `nullglob` 会把字面量 `*.v` 传给 iverilog，报错信息误导。
4. **设计决策与 AI 推荐不同**：模型推荐 M 扩展一次到位，用户选择"先 RV32I 后补 M"（沿用 plan.md 原风险预案）——按用户决策执行，接口预留。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 用户选择"先 RV32I 后补 M" | 与 plan.md 风险预案一致，风险更低；提前补 M 反而拖慢基线锚点 | 设计文档将 M 列为"接口预留、Part A 收尾补"；译码预留 `muldiv_op`、PC 预留 `stall` | ✅ 决策记录入 §9 |
| 2 | iverilog 退出码 `0xC0000139` | Windows 下多套 MinGW 共存，DLL 搜索顺序被其他工具目录抢占 | 脚本内将 `dirname(iverilog)` 提到 PATH 最前（写进 `run_iverilog.sh`） | ✅ 编译通过 |
| 3 | `imem_rdata` l-value 报错 | 指令存储器模型输出必须由 reg 驱动 | `wire imem_rdata` → `reg imem_rdata`（注释说明由模型驱动） | ✅ 临时 stub 编译+运行通过 |
| 4 | 空 glob 报错误导 | `*.v` 无匹配时 bash 不展开 | 脚本 `shopt -s nullglob` + 明确错误提示"Part A 未开工" | ✅ 错误路径提示清晰 |
| 5 | 用写 tohost 的假核完整跑一遍 | 需要验证 tb 的 PASS 分支与脚本全链路 | 临时仓库布局 + stub 核（固定写 `tohost=142879`） | ✅ 输出 `PASS`、exit 0 |

## 5. 最终结论

**v0 接口冻结（4 项决策）**：

| # | 决策 |
|:---:|:---|
| 1 | 指令 BRAM 同步读 + 数据 RAM 异步读（`lw` 单拍，CPI 锚点干净） |
| 2 | v0 先 RV32I，M 扩展 Part A 收尾补（接口预留） |
| 3 | `tohost` 用数据 RAM 高端地址 `0x8000_3FF0` 观测，tb 直接读 |
| 4 | `core_top` 外置哈佛存储接口，地址译码留在 SoC 外壳 |

**v0 关键性质已推导留档**：两级流水天然无 RAW/load-use 停顿，`CPI ≈ 1 + 发生跳转的指令占比`（taken 分支各 1 拍气泡）；跳转 1 拍气泡——这是 v1 三级 + 转发 + BHT 的对照锚点。

**交付物**：

- `src/riscv/design_v0.md`：模块表、各模块端口信号表、`alu_op`/立即数/分支编码、RV32I 控制真值表、mermaid 框图
- `sim/riscv/tb_core_smoke.v`：加载 `hello.hex`、检查 `tohost==142879`，PASS/FAIL 自检
- `sim/scripts/run_iverilog.sh`：一键编译+运行；stub 全链路演练通过（PASS）
- `sim/README.md`：过渡期 iverilog 约定（Vivado 到货后 XSim 同 tb 复核）

**验证方式**：临时目录搭仓库布局 + stub 核，`bash sim/scripts/run_iverilog.sh` 输出 `PASS: tohost = 142879`、exit 0；RTL 落盘后同一命令即为正式冒烟。

## 6. 经验沉淀

- 触发条件：EDA 主工具（Vivado）不可用，但需要提前开发/验证 RTL；或 Windows 多工具链环境命令异常退出 #skill候选
- 排查步骤：
  1. 先盘点可替代的仿真工具（iverilog/Verilator），别让"等安装"阻塞设计推进
  2. Windows 下工具以奇怪退出码（如 `0xC0000139`）挂掉时，优先怀疑 PATH 中多套 MinGW DLL 冲突——把目标工具自身目录提到 PATH 最前
  3. tb 骨架写完后，先用 stub 模块做"编译 + 自检逻辑"演练（甚至构造 PASS 场景），别等 RTL 全写完才发现 tb 语法/路径错误
  4. 脚本对"依赖文件尚未产生"要做空集处理（`nullglob` + 明确提示），这是团队协作脚本的基本素养
- 适用范围：换工具链、换开发机、换赛题均成立
