# [2026-09-23] 协作记录：CoreMark 回归入口接入（coremark 模式）+ 过期状态清理 + 复跑归档

> 标签：#riscv #benchmark #工具链 #回归
> 平台：OpenCode ｜ 模型：deepseek-flash（opencode-go/glm-5.3-flash）
> 相关 commit：待提交（哈希回填）；基线 commit `ac6dcee`

## 1. 任务与初始提示词

> 为 run_iverilog.sh 增加 coremark 模式，删掉旧描述之后重新执行 test

背景：8B（32KB 存储统一）与 CoreMark 移植已随 PR #33/#34 合入 main；此前约定"等 8B 改完
`run_iverilog.sh` 后再加 coremark 模式，避免同文件冲突"的阻塞已解除。

## 2. 方案要点

- `sim/scripts/run_iverilog.sh`：新增 `coremark` 单档模式并纳入 `all`；入口集中定义
  `COREMARK_ARGS`（hex/exit/timer_addr/50M 看门狗/golden 判据），仅对 `tb_core_coremark` 传入
- 活动文档清理（8 处）：`docs/coremark_plan.md`、`docs/coremark_tb_contract.md`、`sim/README.md`、
  `src/riscv/plan.md`、`src/riscv/done/m1-first-phase-completed.md`、`src/riscv_fw/coremark/README.md`
  ——8B/8C/9A/9B、"模式待接入"、"构建待写"等过期描述全部刷新；未决项 #1/#6 关闭，
  #2/#7 明确为 SoC 板上路径剩余项
- `sim/scripts/run_arch_test.sh`：iverilog 加 `-s tb_arch_test` 显式顶层，消除未例化 `imem`
  的 `$readmemh hello.hex` ERROR 噪音
- 证据归档 `data/logs/2026-09-23-coremark-script-regression/`（5 份原始日志 + SHA-256）

## 3. 失败现象（真实偏差，如实记录）

1. **arch-test 日志噪音**：首次复跑出现 `ERROR: imem.v: $readmemh hello.hex Unable to open`
   ——通配编译把未例化的 `imem.v` 当根模块执行其初始化；签名比对本身 PASS，属噪音非功能故障
2. **metrics.csv 字段破坏**：填数时在字段内使用 ASCII 千分位逗号（21,275,738），7 列变 9/11 列
3. **coremark_score.py 无参数路径**：`sys.stderr.write(__doc__)` 因模块无 docstring 抛 traceback

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | arch-test 日志含 ERROR 行 | 未指定顶层导致 `imem.v` 被当根模块 | `run_arch_test.sh` 加 `-s tb_arch_test` | ✅ ERROR 消失，3 用例签名 PASS |
| 2 | csv.reader 字段数 9/11/8 | 字段内 ASCII 逗号 | 千分位去逗号、LUT 行尾逗号改 2 个 | ✅ 12 行全 7 字段 |
| 3 | 无参数 traceback | `__doc__` 为空 | 改 `USAGE` 常量 | ✅ 用法提示 + rc=2 |
| 4 | 脚本改动后日志为旧版产物 | 归档须对应最终代码状态 | 用最终脚本重跑 coremark/all 并刷新日志与 SHA-256 | ✅ 结果一致（1.506） |

## 5. 最终结论

- `bash sim/scripts/run_iverilog.sh coremark`：PASS（32 迭代、tohost=0x8799、exit=0、
  CRC/golden 全对；21,275,738 cycles、CPI=2.105、CoreMark/MHz=1.506）
- `bash sim/scripts/run_iverilog.sh all`：8/8 PASS（含 CoreMark 长测）
- arch-test `add-01/addi-01/and-01`：签名 588/564/584 字全对
- 评分解析：`python data/scripts/coremark_score.py <log>` → 1.506 / CPI 2.105，两份日志一致
- `data/metrics.csv`：CoreMark/MHz=1.506、CPI=2.105 已填（口径/条件/证据齐全）；
  CoreMark/LUT 待 8B 后重综合
- 理解门槛：脚本参数语义 2 题（计时读 0/看门狗默认太短；参数仅属 CoreMark）已答通过；
  commit 前 3 题见下方 §6

## 6. 理解门槛（脚本参数语义 2 题，2026-09-23 已答）

| 题 | 用户答案 | 判定 |
|:---|:---|:---|
| 不传 `+timer_addr=80008000` 会怎样？为何 `+max_cycles=50000000` 也要显式设？ | 计时读 0；默认看门狗太短 | ✅ 通过 |
| 为何脚本只对 tb_core_coremark 传参数？ | 参数只属于 CoreMark | ✅ 通过 |

commit 前 3 题（2026-09-23 已答，全部通过）：

| 题 | 用户答案 | 判定 |
|:---|:---|:---|
| 为何加 `-s tb_arch_test` 后 `$readmemh hello.hex` ERROR 消失？ | iverilog 默认根模块选择在多候选中选错对象，`-s` 强制正确顶层 | ✅ 通过（补精：默认是把**所有未例化模块都当根**执行 initial，非"选错一个"） |
| `all` 中 CoreMark 失败会怎样？ | 前 7 个已跑完不受回溯影响；脚本"决定是否继续或中止" | ⚠️ 首答不通过——后半不确定；补讲 `|| exit 1` 短路语义（失败即停，无继续分支） |
| 补题：删掉全部 `|| exit 1` 会怎样？ | 失败被忽略、脚本可能返回 0、CI 误判通过、门禁失效；正确做法是状态变量汇总失败 | ✅ 通过（超额答出替代方案） |

## 7. 经验沉淀

- 触发条件：给一键回归接入长跑用例；或清理跨分支合并后的过期状态描述。
- 排查步骤：
  1. 长测接入脚本时把专属参数集中在入口一处（`COREMARK_ARGS`），按 tb 名分派，避免散落；
  2. 通配 `*.v` 编译时必须用 `-s <top>` 显式顶层，否则未例化模块的 `initial` 会当根模块执行；
  3. CSV 填数先跑 `csv.reader` 校验字段数，千分位逗号是常见破坏源；
  4. 改完脚本后归档日志必须用**最终代码状态**重跑，哈希才可追溯。
- 适用范围：换 tb、换 benchmark、换脚本入口均成立。 #skill候选
