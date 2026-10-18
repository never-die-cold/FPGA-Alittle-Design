# 2026-10-18 夜间自主执行日志

> 分支：`codex/night-2026-10-18`  
> 起点：`cb352f8be3883a0048e89d38d756fbf87529d5b7`  
> 原则：只做仓库内可复现的离板工作；不 push，不代替 JL 冻结新契约。

## 1. 第零阶段：需求、契约与现状复述

已完整阅读：`AGENTS.md`、`docs/workflow.md`、根 `plan.md`、
`src/riscv/plan.md`、`src/riscv/design_v0.md`、`src/riscv/design_v1.md`、
`src/coprocessor/design_v0.md`、`docs/coprocessor-integration-v0.md`、
`src/coprocessor/README.md`、模块 3 的训练与原型参考、检查 V0 与视觉同步协议、
两份 runner、`data/metrics.csv`，以及 `src/coprocessor/`、`sim/coprocessor/`
现存的全部 RTL/TB。另读了三人收口清单和现行 DDR 离线交接索引。

指定的 `src/coprocessor/plan.md` 与 `docs/coprocessor-handoff-v0.md` 在起点 HEAD
不存在；前者列为本夜 J03 收口待建文件，后者以现行
`docs/cnn-ddr-offline-handoff-2026-10-13.md` 辅助核对，但不冒充缺失文件。

### ✅ 已实现并有仓库内验证入口

- J02 诊断整数参考、量化/打包/解析和逐层黄金生成；它是诊断包，不是正式模型包。
- J03 的 INT8 MAC、128 lane 流水阵列、卷积、ReLU/requant、GAP、FC 与整网 sequencer。
- `mac_array_pipeline` → `conv_engine` → `cnn_sequencer` 现役计算链及对应 TB。
- `mac_lane`、`dot8` 独立诊断 TB；起点提交已把两者接入独立模式和 `all`。
- RISC-V 核既有回归、视觉链既有回归均有仓库 runner；本夜将重新执行而不沿用历史 PASS。

### 🟡 已实现但未完成系统级验证

- 协处理器模块级仿真与 OOC 历史报告已有证据；完整 SoC 综合、实现、100 MHz
  时序和板端行为均未验证。
- C02/C03 已冻结，但 C03 的本地 MMIO/CDC 行为尚未回写核契约并经 JL 确认。
- 诊断参数包能推进 J03/J04 管路验证，但没有真实 PTQ/QAT 权重、阈值和正式黄金身份。

### ⬜ 未实现 / 未接入核

- 物理 BRAM/cache wrapper、`cop_top`、MMIO 寄存器块、CDC mailbox、DMA/payload 装载。
- RISC-V/SoC 接入、工业固件、目标级结果表联动与系统超时闭环。
- 真实数据训练/PTQ（必要时 QAT）、J06 正式模型包、整机位流、上板验证。

### 本夜可安全推进的范围

- J03-R1：只复核起点提交的 runner 接入，跑两个独立模式、协处理器 `all`、全仓 `all`。
- J03 收口：建立模块计划/验收记录，明确诊断模块与现役链，不改 RTL。
- J04 前置：只形成 C03 MMIO 地址和 SoC 行为的核契约草案，标成“待 JL 确认”。
- 余量仅用于独立、低风险的 TB/文档/golden 校验；不展开未经评审的新架构。

禁止碰：冻结 C02/C03 的语义、RISC-V 核既有访存语义、vision/SoC 已验收行为、
J04 RTL、综合/实现/位流和上板。需要新决策时只记问题并跳过。

### 现役数据通路与诊断模块

- 现役：`mac_array_pipeline.v` 内含自己的 128 路乘法/加法树，被
  `conv_engine.v` 实例化，再由 `cnn_sequencer.v` 调度。
- 诊断：`mac_lane.v` 与 `dot8.v` 是独立自测模块，未被现役
  `mac_array_pipeline.v` 实例化；其 PASS 不能替代现役流水线对拍。

### 执行约束

- 冻结契约不得静默修改；核接口仍是无 ready/valid 的同拍异步读、上升沿写本地口，
  不能称作 AXI4-Lite master，也不得暗加等待语义。
- 进入综合的 RTL 必须通过 Verilog-2001，禁止 `.*`、`logic`、`always_ff` 等 SV-only 语法。
- 每个实现小步先设计、改动不超过 100 行，使用仓库内 TB 与 runner，保留原始退出码。
- 仿真 PASS 不等于综合、时序或上板 PASS；历史失败数据不改写。
- 夜间模式替代白天理解门槛：每步闭环后写日志并本地 commit，绝不 push。

## 2. 完成记录

### J03-R1 runner 接入复验：设计说明

- 起点提交 `cb352f8` 已完成脚本接入；本夜不重复改 RTL/runner，只验证其可复现性。
- 目标：证明 `mac_lane`、`dot8` 均有独立入口，且进入协处理器 `all` 和全仓 `all`。
- 本步预估改动：夜间日志约 15 行；RTL/脚本 0 行。
- 验证命令：`run_iverilog.sh cop_mac_lane`、`cop_dot8`、
  `run_coprocessor_iverilog.sh all`、`run_iverilog.sh all`、`git diff --check`。

复验结果（原始退出码）：

- `run_iverilog.sh cop_mac_lane`：0；`PASS: mac_lane signed INT8 products (7 vectors)`。
- `run_iverilog.sh cop_dot8`：0；`PASS: dot8 balanced signed reduction (5 vectors)`。
- `run_coprocessor_iverilog.sh all`：0；算术、流水线、Conv1–4、FC、两组
  sequencer 逐元素黄金全 PASS；两组整网均为 472,593 cycles。
- 首次 `run_iverilog.sh all`：1；默认 Python 缺 `cv2`，最小复现为
  `python3 -c "import cv2"`，实际 `ModuleNotFoundError`。
- 第二次全仓：1；`--target` 依赖能通过 OpenCV 用例，但 ordering 负例会替换
  `PYTHONPATH`，子进程因缺 NumPy 提前退出，因而找不到预期板端失败签名。
- 仓库内 `virtualenv==20.35.3` 创建 `sim/build/vision-venv-full`，安装冻结的
  OpenCV 4.12.0.88、NumPy 2.2.6、Pillow 12.3.0；构建目录不纳入提交。
- 单独复现 `test_c01_capture_ordering.py`：0；预期 0x4810 失败签名出现。
- 第三次 `run_iverilog.sh all`：0；使用上述 venv；四档真实 CoreMark 分别
  19,057,438 / 17,114,141 / 16,335,562 / 16,232,079 cycles，协处理器、
  核、视觉 RTL 与 Python 收尾全部 PASS。
- 本步源码/RTL/runner 改动：0 行；仅补充本日志。起点 runner 实现提交仍为
  `cb352f8`，夜间复验不制造重复功能提交。

### J03 收口：设计说明

- 新建缺失的 `src/coprocessor/plan.md`，只记录权威链接、J01–J10 状态和进入 J04 的门槛。
- 新建本轮 J03 验收索引，引用既有原始证据与本夜退出码，不复制大日志。
- 在模块 README 明示 `mac_lane/dot8` 为诊断模块、现役链使用 `mac_array_pipeline`。
- 预计三文件合计不超过 100 行；不改 RTL、契约语义或测试。
- 验证：路径存在性/关键字静态核对、`git diff --check`；本步为纯文档，不重跑已完成全量。

结果：新增模块计划 39 行、验收索引 21 行，README 增 4 行，本段日志 10 行；
关键路径和诊断/现役描述均由 `rg` 命中，`git diff --check` 退出 0。J03 仅按离板
算术/调度范围收口，J04 与正式模型相关项目继续明确标为未实现。

### J04 前置核契约回写：设计说明

- 目标文件：`src/riscv/design_v1.md`；只追加明确标记“待 JL 确认/非规范”的草案附录。
- 内容只映射 C03 已冻结事实：4 KiB `0x8001_0000` 窗口、DMEM 屏蔽/读 mux、
  单周期本地镜像、上升沿命令邮箱、CDC 原子快照、权限/非法地址行为和验收点。
- 不复制完整寄存器表，以 C03 为唯一来源；不新增核端口、wait state、IRQ、自定义指令或 RTL。
- 预计契约与日志合计不超过 80 行；验证交叉引用/关键字段和 `git diff --check`。

结果：`design_v1.md` 新增 46 行非规范草案，本日志新增 12 行；仅两份 Markdown 变化。
`rg` 已命中地址、无等待边界和待确认标题，`git diff --check` 退出 0。未运行 RTL
回归，因为本步没有实现变更且草案明确禁止据此开工。

### 低风险整理：J03 指标入表设计说明

- `data/metrics.csv` 现有“CNN 推理单帧耗时/能效”只是空占位，没有 J03 数据。
- 只追加两行已有证据：诊断整网控制周期、控制器 OOC 资源/100 MHz 时序。
- 条件栏明确诊断参数、CE 停顿、无实体 BRAM/DMA/SoC，不换算板端延迟或宣称整机达标。
- 证据引用 2026-10-15 已归档原始日志；验证 CSV 每行 7 列、`git diff --check`。

结果：CSV 增 2 行；stdlib `csv.reader` 检查 63 行均为 7 列，关键字核对通过，
`git diff --check` 退出 0。没有生成新测量值，也没有改写历史失败或占位行。

### 低风险整理：协处理器交接薄索引设计说明

- 新建此前缺失的 `docs/coprocessor-handoff-v0.md`，面向 WC/NC/JL，只做权威入口和状态导航。
- 不复制 C02 payload offset、C03 寄存器表或旧 DDR 文档正文，避免多份真源漂移。
- 更新 `docs/README.md` 与模块 README 的入口；明确 J03 可交付、J04/J06/J08 未交付。
- 预计三文件与日志合计不超过 100 行；只做链接存在性、禁重复字段检查和 `git diff --check`。

结果：薄索引 64 行，8 个本地链接全部存在；导航增 3 行、模块 README 增 1 行。
静态检查确认未出现寄存器 offset 表/`RESULT_META` 复制，`git diff --check` 退出 0。

### 低风险补测：dot8 原始负边界设计说明

- 只读审计确认现有 5 个向量已覆盖零、合法正/负界、原始最大正界和混合符号树；
  尚未覆盖原始总线 `-128` 在负方向穿过完整 8 路加法树。
- 只在 `tb_dot8.v` 增加 8 路 `-128 * 127 = -130048` 向量，预计 3 行；不改 RTL。
- 该用例仍只验证诊断 `dot8`，不能替代现役 `mac_array_pipeline` 的逐元素对拍。
- 验证：`cop_dot8`、协处理器 `all`、全仓 `all` 与 `git diff --check`。

结果：TB 增 3 行，独立模式退出 0，报告 6 个向量。协处理器 `all` 首跑因默认
Python 缺 NumPy 退出 1；保留失败后，用仓库内既有冻结依赖 venv 重跑退出 0，
两组整网仍为 472,593 cycles 且逐元素匹配。全仓 `all` 退出 0，四档真实 CoreMark
为 19,057,438 / 17,114,141 / 16,335,562 / 16,232,079 cycles，核、协处理器、
视觉 RTL 与 Python 收尾均 PASS。`git diff --check` 退出 0；未改 RTL。

### 低风险整理：全仓 runner 帮助文字

- 只读核对发现全仓 runner 的 `coprocessor` 用法注释仅列 4 个子模式，而实际 case/子 runner
  还支持 8 个算子/诊断模式和 `watchdog`；该注释会误导复现者。
- 只改 1 行注释，使其与子 runner 的 usage 一致；不改控制流、RTL 或测试判据。
- 验证：两份 shell 脚本 `bash -n`、模式关键字静态核对和 `git diff --check`。

结果：runner 注释改 1 行；两份脚本 `bash -n` 均退出 0，静态核对命中完整模式列表，
`git diff --check` 退出 0。纯注释变更未重跑已完成的全仓回归。

### 低风险补测：诊断 golden manifest 完整性设计说明

- 三个 golden 生成器会记录 SHA256，但现有测试没有重新读取 manifest 校验落盘字节。
- 新增一个 Python 测试，在 `sim/build/coprocessor` 内生成算术、算子和整网诊断数据，
  核对固定 kind/case/必需文件集合，并独立重算所有文件与来源 SHA256。
- 对一个生成文件临时追加字节，断言哈希不再匹配后立即恢复，证明负例具备检错能力。
- 预计测试、runner 与日志合计不超过 100 行；不改算法、RTL、冻结契约或正式模型状态。
- 验证：独立 `manifests`、Python `all`、全仓 `all`、`git diff --check`。

结果：新增测试 69 行，runner 改 5 行，日志增 15 行；共新增 87、删除 2，
总改动 89 行，满足单步上限。独立 `manifests` 和 Python `all` 均退出 0；全仓 `all`
退出 0，并实际打印 manifest 完整性 PASS。四档真实 CoreMark 为 19,057,438 /
17,114,141 / 16,335,562 / 16,232,079 cycles，核、协处理器、视觉 RTL 与 Python
收尾均 PASS。`git diff --check` 退出 0；生成物只在被忽略的 `sim/build` 内。

### 低风险整理：J02 README 回归入口去陈旧计数

- README 仍称 Python 回归为“3 组/四组”，与 runner 的 10 个现行模式不一致。
- 只把两段改为权威 `all`/`manifests` 命令与覆盖范围，不复制易漂移的测试数量。
- 改动仅为文档 5 行；独立、Python all、全仓 all 已在上一小步退出 0，本步不重复运行。
- 前两次静态核对命令分别因 Markdown 反引号被 shell 展开、错误要求 `.sh` 具备可执行位而
  退出非零；未改文件。改用 `bash -n`、文件存在性和普通 `rg` 后退出 0，`git diff --check` 退出 0。

### 低风险整理：J02 Python 环境复现说明

- `requirements.txt` 已固定 NumPy 2.2.6，但 README 缺从空 venv 到 runner 的连续命令；
  项目总览同时残留“3组 INT8 参考”的陈旧计数。
- README 增加仓库 `sim/build` 内 venv、按冻结依赖安装、指定解释器运行三条命令；
  总览改为按语义描述完整参考/manifest 回归，不写易漂移数量。
- 仅文档增 8、改 1 行；路径/版本/命令静态核对和 `git diff --check` 退出 0。

### 低风险整理：J03 dot8 向量数演进说明

- 收口索引记录的 5 vectors 是 `21f8a9c` 当时真实结果，不改写历史；当前 TB 已在
  `4cb5b1d` 增加原始负边界，复现会报告 6 vectors。
- 只在当前索引结果格追加“当时 5 / 当前 6”与提交引用；历史原始日志保持不变。
- 文档改 1 行、日志增 5 行；静态核对与 `git diff --check` 退出 0。

### 低风险整理：交接索引补 J02 软件复现入口

- WC/NC 薄索引原来只列 RTL/全仓命令，遗漏整数参考 Python `all` 和 manifest 独立门禁。
- 只在复现代码块增加两条现有 runner 命令，不复制参数格式、不改变 J06/J08 未交付状态。
- 索引增 2 行、日志增 5 行；runner 模式存在性、命令文字与 `git diff --check` 核对通过。

### 本夜完成的本地提交

- `7553803`：第零阶段全量阅读、三类清单、范围与约束落盘；
- `21f8a9c`：J03-R1 独立/协处理器/全仓入口复验及环境失败留痕；
- `37aa106`：J03 离板收口计划、验收索引和诊断/现役边界；
- `02b15bb`：J04 本地 MMIO/SoC 非规范草案，明确待确认项；
- `e9af88c`：将已有 J03 诊断周期与控制器 OOC 指标纳入 metrics；
- `0d0f1db`：补齐只引用权威来源的协处理器 V0 交接薄索引；
- `4cb5b1d`：补齐 `dot8` 原始 `-128 * 127` 八路负边界并完成三级回归；
- `acdbd35`：使全仓 runner 的协处理器模式帮助文字与实际入口一致。

建议早上优先 review：`02b15bb`（契约草案）→ `4cb5b1d`（边界补测）→
`37aa106`（J03 收口边界）。所有提交均为本地提交，未 push。

## 3. 失败、跳过与待确认问题

- 全仓前两次失败均已保留在上节；根因是解释器依赖可见性，不是通过删测试或
  注释断言处理。最终使用仓库内完整 venv 原入口退出 0。
- `dot8` 补测的协处理器 `all` 首跑同样因默认 Python 缺 NumPy退出 1；冻结依赖
  venv 重跑原入口退出 0，未据此修改代码或判据。
- 待 JL 确认 §17 草案，以及三项细化：核侧子字写策略、无等待连续写邮箱策略、
  未对齐/越权访问的精确读回与错误码。确认前 J04 RTL 保持未实现。
- 按护栏跳过：J04 RTL、综合/实现、位流和上板；未触碰 RISC-V 核既有语义或 vision 行为。
- 指定的 `docs/coprocessor-handoff-v0.md` 在起点 HEAD 不存在；续工后已补成只引用权威来源的
  薄索引，10/13 CNN/DDR 文档继续保留为历史证据，不形成第二份契约表。

## 4. 续工点

- 分支：`codex/night-2026-10-18`；功能/测试收口点 `acdbd35`；本节日志提交后以
  `git log -1` 为最终 HEAD，工作树应干净，`git diff --check` 应退出 0。
- 下一步先由 JL review `src/riscv/design_v1.md` §17 并确认三项细化；确认前不要写 J04 RTL。
- 确认后从本地 MMIO 寄存器/地址译码 TB 的设计说明开始，保持单步不超过 100 行，
  独立模式与全仓 `all` 均通过后再进入 CDC/存储/`cop_top`。
- J03 已完成的是离板诊断计算链；正式模型、系统综合时序与上板继续保持“未完成/未验证”。
