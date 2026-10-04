# Part B 未来三日可执行计划

> ⚠️ 推送前待办：本地 `dev/rtl` 与 `origin/dev/rtl` 已分叉；恢复推送前必须先执行 `git pull --rebase origin dev/rtl`，禁止强推。
> 编制日期：2026-10-04；工作分支：`dev/rtl`。
> 依据：`design_v1.md` 冻结契约、`src/riscv/plan.md §4.2/§4.3`、`docs/partB-verify-plan.md`。
> 纪律：每个 RTL 小步净改动不超过 100 行；先写/改仓库内 tb，再改 RTL；每步跑单项、`all` 和 `git diff --check`。

## 1. 现状与可复现证据

### ✅ 已实现并验证

- Part A v0 已由 tag `partA-v0` 固定；RV32IM、CoreMark、SoC 基线证据见
  `data/logs/2026-09-28-partA-closure/`。复现：`bash sim/scripts/run_iverilog.sh all`。
- R1 `uses_rs1/uses_rs2` 已验证 11 例，见 `data/logs/2026-09-29-r1-verify/`；
  复现：`bash sim/scripts/run_iverilog.sh decode`。
- R2–R5 四个积木已有独立复验：forwarding 25 例、hazard 16020 组合、
  MEM+WB 3 例、ID+EX 6 例，见 `data/logs/2026-09-30-r2r5-verify/`；复现命令分别为
  `run_iverilog.sh forwarding|hazard|mem_wb|id_ex`。
- `id_ex_stage` 的 `decode (.*)` 已展开为显式端口；RTL-only
  `iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v` 零输出、退出码 0，定向 tb 6/6 PASS；
  本次原始证据见 `data/logs/2026-10-04-fix-implicit-ports/`。

### 🟡 已实现但未完成目标级验证

- `forwarding.v`、`hazard.v`、`id_ex_stage.v`、`mem_wb_stage.v` 仅模块级通过，尚未接入
  `core_top`，因此不能据此宣称三级核通过。
- `sim/scripts/synth_id_ex_ooc.tcl` 已提供默认 Verilog-2001 OOC 入口；当前 WSL 中 Windows
  Vivado 壳缺少 `lnx64` 文件，尚无真实 `synth_design` PASS。Windows 复现：
  `D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source sim/scripts/synth_id_ex_ooc.tcl`。
- v0 有 Icarus、XSim、Vivado、上板证据；这些证据不能替代 v1 的同类验证。

### ⬜ 未实现 / 未接入核

- v1 `core_top` 三级集成、`ENABLE_FORWARDING=1/0` 两档整核入口与整核 hazard/RV32M 专项。
- 两档 arch-test、CoreMark/benchmark CPI、公平降幅、XSim 对拍、Vivado WNS/资源、v1 上板。
- Part C BHT 与四档报告尚未实现；独立“Part C 验收计划”文件不存在，验收条款目前只在
  `src/riscv/plan.md §4.3` 和 `design_v1.md`。
- PicoRV32 实测证据不存在：`docs/core_comparison.md` 仍是计划，`data/metrics.csv` 对应行为空。

## 2. D1：三级核功能集成

### D1.1 先建立整核红灯用例（✅ 红灯已建立，2026-10-04）

- 改：新增 `sim/riscv/tb_core_v1_flow.v`；给 `run_iverilog.sh` 增 `v1_flow` 模式。
- 覆盖：复位空槽、连续 ALU RAW、load-use、taken/not-taken、store 恰好一次提交。
- 验证：先记录旧 `core_top` 不满足三级断言的预期 FAIL；不得把红灯写成已验证。
- 交付：最小失败日志落 `data/logs/<date>-partB-v1/`。
- 理解题：为何气泡必须用 `valid=0`？为何 stall 不能 hold MEM+WB？

### D1.2 接入提交边界与唯一副作用点（✅ D1.2a/b 已验证并通过理解门槛）

- 改：`core_top.v` 增默认开启的 `ENABLE_FORWARDING`；例化 `mem_wb_stage`；把 regfile/DMEM
  写使能收敛到 `mem_valid`；load 扩展和 store lane 使用寄存后的地址/数据。
- tb：扩 D1.1，断言气泡/复位不写、store 只写一次、load byte/half/word 正确。
- 验证：`run_iverilog.sh mem_wb`、`v1_flow`、`all`；预期既有 RV32IM/tohost 不回归。
- 理解题：为何 MEM+WB 无 hold？为何 `dmem_we` 必须包含 `mem_valid`？

### D1.3 接入 ID+EX、转发与 hazard（✅ D1.3a/b 已验证并通过理解门槛）

- 改：`core_top.v` 先接 regfile→forwarding→`id_ex_stage` 数据面，再接 `hazard` 的
  `front_stall/ex_accept/redirect/mem_in_valid` 控制面；对外存储器端口保持不变。
- tb：加入 ALU→ALU/branch/JALR/store，检查转发开时零 RAW 气泡、load-use 恰 1 拍。
- 验证：`forwarding`、`hazard`、`v1_flow`、`all`；检查 `redirect && front_stall==0`。
- 理解题：为什么 redirect 必须由 `ex_accept` 门控？EX/MEM/WB 三来源为何不是三级之外的新级？

### D1.4 接入 muldiv 等待与统一写回（预计 60–85 行）

- 改：`core_top.v` 实现单拍 start、粘滞 pending、start 拍立即 front stall、done 进 MEM+WB。
- tb：扩 `tb_core_v1_flow.v`，统计 start=1 次、等待期 0 次提交、结果写回 1 次、紧随消费者正确。
- 验证：`run_iverilog.sh muldiv`、`rv32im`、`v1_flow`、`all`，预期 `tohost=142879`。
- 理解题：为何不能等 busy 才 stall？为何 pending 要到 MEM+WB 接受结果才清？

### D1 出口

- `v1_flow` 及既有 `all` 全绿；`core_top` 外部端口不变；所有副作用受 valid 门控。
- 若任一小步超过 100 行，则继续按数据面/控制面拆，不把两个目的塞进同一提交。

## 3. D2：双档转发、专项覆盖与架构回归

### D2.1 固化同 RTL 双档入口（预计 30–60 行）

- 改：tb 顶层透传参数；`run_iverilog.sh` 新增冻结名称 `v1_fwd`、`v1_nofwd`，`all` 纳入两档。
- 验证：两条命令使用同一文件列表与 tb，只以 elaboration parameter 取 1/0；禁止复制 RTL。
- 预期：功能终值一致；无转发档 RAW 气泡更多。
- 理解题：关转发后 hazard 为何必须停所有真实 RAW？怎样证明对比只变一个变量？

### D2.2 完成整核 hazard / RV32M 断言（每个 tb 补丁 60–95 行）

- 改：扩 `tb_core_v1_flow.v` 或新增 `tb_core_v1_hazard.v`；接入单独模式和 `all`。
- 覆盖：x0/伪 RAW、双源、branch 先停后跳、taken 1 气泡、stall 时旧提交不重复、M 后继相关。
- 验证：`v1_fwd`、`v1_nofwd`、`rv32im`、`all`；保留两档原始日志。
- 理解题：load-use 那拍四个边界各做什么？M done 为何只送下游而不直接写 regfile？

### D2.3 跑同集合 arch-test（脚本适配每步不超过 80 行）

- 改：仅在现有 `run_arch_test.sh` 增参数化确有必要时修改；不得改变参考签名语义。
- 验证：两档各跑 v0 已有 `add-01/addi-01/and-01`，签名相同；套件不存在时运行
  `fetch_arch_test.sh` 并记录实际 commit，不把缺套件写成 PASS。
- 交付：日志和工具版本入 `data/logs/<date>-partB-v1/README.md`。

### D2 出口

- `all` 包含 v1 两档并全绿；R-type 零气泡、load-use 1 气泡、taken 1 气泡均由断言证明。

## 4. D3：CPI、跨工具、时序与交付证据

### D3.1 冻结 retire/CPI 口径（预计 50–90 行）

- 改：`tb_core_coremark.v` 改按 `dut.wb_valid` 计 retired；同一 tb/hex/终止条件跑两档；
  `cpi_harness.py` 只在输出格式确需适配时修改。
- 验证：`run_iverilog.sh v1_fwd|v1_nofwd` 与 benchmark/CoreMark；计算
  `(CPI_nofwd-CPI_fwd)/CPI_nofwd`，主门禁为 ≥25%。
- 交付：原始日志、`data/metrics.csv` 两行及命令；气泡不算指令，M 只 retire 一次。
- 理解题：为何 busy 拍不能增加 retired？为什么 v0 不能作为 25% 降幅分母？

### D3.2 XSim 与 Vivado 门禁（脚本小步各不超过 100 行）

- 改：复用/新增仓库内 Tcl，默认 Verilog-2001 读取；两档用同器件、版本、约束与报告口径。
- 验证：XSim 终值/cycles 与 Icarus 一致；实现报告必须 WNS≥0、无未约束内部端点、无
  Error/Critical Warning DRC。125 MHz 是非阻塞加分项；到时间盒未过则保留最高通过频率并启动 L3。
- 交付：七件套报告、Vivado 版本、commit、原始日志。只生成 bitstream 时状态写“待上板”。

### D3.3 板级与交接

- 只有实际下载 PYNQ-Z2 并观察到约定 LED/tohost 才记 v1 已上板；否则保留“待上板”。
- 汇总四件套：改动文件、原始命令/结果、`git diff --check`、未实现/未接入清单。
- Part B 通过后才建立 Part C BHT 三档实现步骤；PicoRV32 实测排在 M1 收口后。

## 5. 依赖、风险与停止条件

- 当前最大技术风险是 `core_top` 切换时的 valid/hold/redirect/muldiv 优先级；以逐拍断言定位，
  不用固定延时猜测。任何问题超过 30 分钟，记录最小复现后转独立项。
- arch-test 套件目录被 gitignore，依赖网络和工具链；缺失时只能标阻塞，不得伪造签名结果。
- WSL 无可用 Vivado/XSim；需 Windows 执行仓库 Tcl。工具没跑就明确写“未验证”。
- 用户任务写了“D15 WNS≤0”，冻结契约和正常时序门禁均为 **WNS≥0**；计划按契约执行。
- timescale 继承警告为既有技术债；本次 `-g2001` 综合代理采用 RTL-only 编译零 warning，
  不把清理全部 timescale 混入核心集成小步。

## 6. 理解门槛（回答通过后才进入下一步）

- D1.1：为什么气泡必须用 `valid=0`，不能只把指令改成 NOP？
- D1.1：为什么 stall 时不能 hold MEM+WB，而要让旧指令提交一次后排空？
- D1.2a（已通过）：为什么 regfile/DMEM 写使能都必须包含 `mem_valid`？
- D1.3a（已通过）：为什么 redirect 必须经过 `ex_accept` 门控？
- D1.3a（已通过）：为什么 load-use 要停 1 拍，而普通 ALU RAW 可以通过转发零停顿？
- D1.3b（已通过）：为什么组合 `id_ex_stage` 不会增加第四级？
- D1.3b（已通过）：为什么 `branch_taken/jump_taken` 仍必须经过 hazard 的 `ex_accept`？
- D1.3b（已通过）：为什么 store data 必须用转发后的 rs2 并捕获进 MEM+WB？
- D1.2b（已通过）：`sb` 的 byte enable 如何选择 offset 0/2/3 对应字节车道？
- D1.2b（已通过）：`lb` 与 `lbu` 为什么分别执行符号扩展和零扩展？
- D1.2b（已通过）：复位期零写与全程恰好 11 次写如何抓漏提交和重复提交？

## 7. 用户回来后必须拍板 / 回答

1. 确认任务中的 `WNS≤0` 是笔误，继续以冻结的 `WNS≥0` 为门禁。
2. Part C 是否另建独立验收计划，还是继续以 `plan.md §4.3 + design_v1.md` 为唯一执行入口。
3. Windows XSim/Vivado 和 PYNQ-Z2 实机由谁、在哪个时间窗执行；无人执行前均标未验证/待上板。
4. `.*` 修复理解题：为什么显式端口比全局 `read_verilog -sv` 更稳？为什么 Icarus `-g2012`
   PASS 不能证明 Vivado 默认解析通过？为什么测试平台也同步展开端口？
5. 三日实现理解题集中采用各小步所列问题；逐题通过后才允许本地 commit；当前禁止 push。
