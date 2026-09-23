# [2026-09-23] 协作记录：CoreMark 移植层落地——哈佛加载器缺口实跑定位 + v0 跑分/golden

> 标签：#riscv #benchmark #工具链 #架构决策
> 平台：OpenCode ｜ 模型：deepseek-v4.1-flash（opencode-go/deepseek-v4.1-flash）
> 相关 commit：`8100975`（契约）+ 本批次同一 commit（哈希回填）

## 1. 任务与初始提示词

> 开工！（承接契约交付后的 Phase C/D：vendor 源码、移植层、构建、跑分、golden）

计划依据：`docs/coremark_plan.md` 阶段 C/D；接口依据：`docs/coremark_tb_contract.md`。过程约定：代码步骤免理解题（用户拍板"免题版"），保留四件套汇报。

## 2. 模型第一版方案

- C1 vendor：官方 coremark 固定 commit `1f483d5b`（2025-05-01）入库 `src/riscv_fw/coremark/vendor/`，逐文件 SHA-256 入 `data/evidence/2026-09-23-coremark-source.md`
- D1/D2 移植层：`core_portme.c/h`（无 libc、`ee_printf` 置空、`get_time` 读 `0x8000_8000`、2K profile）
- D3 钩子：`core_main.c` 派生副本，仅在 `portable_fini` 前加 `port_results_export(...)` 写观测块；diff 入 `data/evidence/2026-09-23-coremark-main-hook.patch`
- C3 构建：`link_coremark.ld`（32KB；`.text/.data/.bss` 低区、tohost 固定 `0x3FF0`、栈顶 `0x7F00`）+ Makefile `coremark` 目标
- D6 golden：host 移植层（`coremark/host/`）同源复算

## 3. 失败现象（真实偏差，如实记录）

1. **程序跑飞**：首跑 PC 随机漂到 `0x807c8024` 一路爬出代码区；log 为空（vvp 缓冲，kill 后丢失）
2. **自动标定陷阱**：DMEM 不预载时 `seed4_volatile`（.data 初值）读到 0 → `ITERATIONS=0` 触发官方"跑够 10 秒"自动标定循环（~1e9 周期）
3. **indirect jump 飞出**：trace 定位 `0x22B4: jalr x0, 0(a5)` —— 编译器生成的 switch **跳转表在 `.rodata`**，被链接进 IMEM 侧，`lw` 读 DMEM 得 0 → 目标地址 = 表基址（数据区）→ 跳进 `.data`
4. **host 指针截断**：golden 宿主层 `ee_ptr_int` 先用 32 位，64 位 PC 上 `align_mem` 截断指针（-Wpointer-to-int-cast）

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | PC=0x807c8024、2M 周期不结束 | 疑似无限循环/跑飞 | 小看门狗 + cmd 重定向取输出；建临时 trace tb（`sim/build/`） | 定位到失控点 |
| 2 | trace 显示跳转表读 0 | 哈佛分离下 `.data`/`.rodata` 需数据口可见 | tb 增加 `$readmemh(hex, dmem)`（双口加载器语义）；契约 §3.2/§4.2 修订；新增未决项 #7（soc_top 预载） | 1 迭代 debug 跑通 |
| 3 | 1 迭代 `crcfinal==crclist` 合理但 `iterations` 疑云 | seeds `.data` 初值不可用 | seeds/`default_num_contexts` 改 `portable_init` 运行时赋值（`core_portme.c`） | 32 迭代全判据 PASS |
| 4 | host 编译告警 | 宿主指针宽度 | `ee_ptr_int` 改 `uintptr_t` | O2/O0 输出一致 |

## 5. 最终结论

- **v0 32 迭代仿真 PASS**：`seedcrc=0xe9f5`、`crclist=0xe714`、`crcmatrix=0x1fd7`、`crcstate=0x8e3a`、`crcfinal=0x8799`、`tohost=0x8799`、`exit=0`；CPI=2.105、**CoreMark/MHz=1.506**（仿真外推口径）；`errors=1` 为官方 <10s 计数（契约 §5.4 不作判据）
- **golden 三方一致**：host `-O2`、host `-O0`、RTL 仿真 → `crcfinal=0x8799`（验证线独立复核待办）
- 证据：`data/logs/2026-09-23-coremark/`、`data/golden/coremark_2k_32iter/`；hex 4094 字（≤8192）、体检无 libgcc/浮点/压缩/原子指令
- 理解门槛：用户选择"免题版"（代码步骤豁免出题），本记录留痕；commit 待用户确认

## 6. 经验沉淀

- 触发条件：把带初始化数据/跳转表的 C 程序移植到**哈佛分离**的裸机核；或官方 benchmark 首次上核。
- 排查步骤：
  1. 先跑小迭代 + 小看门狗拿退出输出；`vvp` 输出被 kill 会丢缓冲，重定向 + 让进程正常退出（`$fatal`/`$finish`）才可靠；
  2. 用全量 PC 轨迹（临时 tb 写文件）定位"第一条越界"，再回看 30-50 拍找飞出的跳转；
  3. `.data` 初值、`.rodata`（含 switch 跳转表）都必须经数据口可读——哈佛核要"镜像双口预载"或等效加载器；
  4. 官方 benchmark 的自动迭代标定（ITERATIONS=0）依赖 ≥1s 真实计时，仿真必须显式给迭代数；
  5. 跨位宽移植（host 64 位）时指针整型必须用 `uintptr_t`。
- 适用范围：换题目/换板卡仍成立；与 2026-09-15 `muldiv` 契约教训同属"接口缺口的代价"。 #skill候选
