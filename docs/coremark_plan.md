# CoreMark 跑分工作包分条计划（`dev/bench`）

> 状态：📋 执行计划（2026-09-23 起草）
> 主责：基准线 `dev/bench`｜窗口：9/25–10/1（与 Part B/C 并行，2026-09-21 压缩排期）
> 依据：`docs/core_comparison.md`（决策与指标定义）、`src/riscv/plan.md` §1–§3（剩余计划与遗留）、`sim/README.md`
> 配套契约：`docs/coremark_tb_contract.md`——接口/观测/判据的唯一执行口径（本地草稿已落盘 §1–§4，待复核入库）
> 冲突处理：接口以 `src/riscv/design_v0.md` 为唯一权威；本文只回答"做什么、谁做、怎么验收、卡在哪"

## 0. 现状快照（动手前先核对，禁止凭记忆）

**已就绪**

- 存储契约 8A 冻结：IMEM/DMEM `8192×32`、`addr[14:2]`、DMEM 异步读、`tohost 0x8000_3FF0`（随 PR #32 合入 main）
- RV32IM 核 + `muldiv` 整核冒烟 PASS；回归五档 `v0|fwd|muldiv|rv32im|all`
- 通用 tb `sim/riscv/tb_core_coremark.v` 已入库：plusarg 参数化、写事件判结束、cycles/instrs/bubbles/CPI 统计
- 契约草稿 `docs/coremark_tb_contract.md` §1–§4 落盘（未入库）

**未就绪（阻塞项）**

| # | 项 | 现状 | 责任线 |
|:--:|:---|:---|:---|
| 1 | 8B 存储模型（32KB 统一 RTL/固件/链接） | 未开始 | RTL 线 |
| 2 | SoC 计时计数器（提案 `0x8000_8000`） | 未开始，地址待确认 | RTL 线 |
| 3 | vendor CoreMark + 移植层 | 未开始 | bench |
| 4 | `coremark.hex` + golden（crcfinal） | 未开始 | bench 出、verify 复核 |
| 5 | `coremark` 回归模式（`run_iverilog.sh`） | 等 #1 | verify/bench |
| 6 | `data/metrics.csv` 两行数值 | 骨架在，数值空 | bench |

**依赖链**：#1/#2（RTL）→ #3（bench）→ #4/#5（bench/verify）→ metrics + 四档数据（bench）；阶段 A 契约可与 RTL 并行，不等 RTL 完成。

## 1. 阶段 A：契约收口（9/23–9/24）

- [ ] A1. `docs/coremark_tb_contract.md` 补 §5 判据、§6 运行与证据、§7 变更控制与未决项收口，复核后入库
- [ ] A2. 待确认项收口：计时器地址/读语义（提案 `0x8000_8000`，同拍组合读）、观测块 `0x8000_7F00` + 字段表、`tohost` 保持 `0x8000_3FF0`
- [ ] A3. 确认结果由 RTL 线回写 `design_v0.md` §3.3；bench 同步 `data/metrics.csv` 口径文字
- 验收：契约冻结 → 三线可并行；任何实现与契约冲突，先改契约再改码

## 2. 阶段 B：RTL 前置（9/24–9/25，RTL 线主责，bench 只消费）

- [ ] B1. 8B 存储模型：IMEM/DMEM `8192×32` 落地（tb 模型 / 链接脚本 / `soc_top` 统一 32KB）
- [ ] B2. SoC 计时计数器：32 位自由运行、每 clk +1、同拍可读、地址按 A2 冻结值
- [ ] B3. 五档回归复跑，证据入 `data/logs/`
- 验收：coremark 路径不被存储容量/计时读数卡死
- bench 配合：地址未定稿前 `TIMER_ADDR` 用宏占位 + tb `+timer_addr` plusarg，不阻塞移植层开发

## 3. 阶段 C：vendor 引入与构建（9/25，bench）

- [ ] C1. EEMBC coremark 按**固定 commit** 拉入 `src/riscv_fw/coremark/vendor/`；commit 哈希/日期/使用文件 SHA-256 入 `data/evidence/`；附官方 LICENSE
- [ ] C2. 守住官方规则：`core_list_join.c`/`core_matrix.c`/`core_state.c`/`core_util.c`/`coremark.h` 不改；允许改 `core_portme.c/h`；`core_main.c` 只加"结果导出钩子"（CRC/ticks 写观测块），diff 入证据
- [ ] C3. `Makefile` 增 coremark 目标、`link.ld` 按 32KB 布局；产出 `coremark.hex/.dis`；`size` 查容量 + `objdump` 查无 libgcc/浮点/压缩/原子指令
- [ ] C4. 容量兜底：2K profile（`TOTAL_DATA_SIZE=2000`、`ITERATIONS=32`、seeds `0/0/0x66`、`MEM_STATIC`）超限时按官方配置裁，裁剪即写入口径
- 验收：hex 字数 ≤ 8192、可被 tb 预载、`.text/.data/.bss+栈` 不越 32KB、不与观测块/`tohost` 重叠

## 4. 阶段 D：裸机移植层（9/25–9/27，bench）

- [ ] D1. `core_portme.h`：配置项全部显式定义（`MEM_STATIC`、`HAS_FLOAT=0`、`HAS_TIME_H=0`、`MAIN_HAS_NOARGC`、`ITERATIONS=32`、seeds 通道）
- [ ] D2. `core_portme.c`：`get_time` 读 `TIMER_ADDR`（打点用 `t_end - t_start`）；`time_in_secs`/`EE_TICKS_PER_SEC` 整数口径（不引浮点）；`ee_printf` 输出（按需，写入 dmem 缓冲）
- [ ] D3. 观测块写入（契约 §4.3 字段表：MAGIC/iterations/seedcrc/三算法 CRC/crcfinal/t_start/t_end/errors_raw/DONE），每字段恰好一次、先于 `tohost_exit`
- [ ] D4. 结束协议：`tohost = crcfinal` → `tohost_exit = 0` → 死循环自旋（tb 按写事件判结束）
- [ ] D5. 自检通过：`seedcrc=0xe9f5`、CRC 与 golden 一致；`errors_raw` 携带的仿真 <10s 错误只作证据不作判据
- 验收：`+exp_tohost=<golden>` PASS；golden `crcfinal` 由 bench 出、verify 复核

## 5. 阶段 E：回归接入与证据（9/27–9/29，verify 主责、bench 配合）

- [ ] E1. `coremark.hex` 入库后给 `run_iverilog.sh` 加 `coremark` 模式（等 8B 合入，避免同文件分叉）
- [ ] E2. 固化 `+max_cycles`（首轮实测最坏周期 ×2）与 `+timer_addr` 默认参数
- [ ] E3. 证据归档 `data/logs/2026-09-xx-coremark-<cfg>/`（原始日志 + 判据 + 测试条件）；`data/scripts/` 放评分解析脚本（日志 → score/CPI/表格）
- 验收：一条命令可复现（仓库内 tb + 脚本，禁临时文件）、PASS/FAIL 明确、日志可追溯到数值

## 6. 阶段 F：数据入档（9/29–10/1，bench）

- [ ] F1. `data/metrics.csv` 填两行：CoreMark/MHz（注明"仿真短迭代外推"口径 + 工具/配置条件）、CoreMark/LUT（写明推导公式与 post-route LUT 来源）
- [ ] F2. `docs/core_comparison.md` §5 勾选、§2 表更新为实测行（M1 后）
- [ ] F3. README「为什么自研核」占位数字刷新（**实测后再写，禁止先写目标后凑数**）

## 7. 阶段 G：四档对比（9/29–10/1，配合 Part B/C）

- [ ] G1. 同一份 `coremark.hex` 只换 RTL 配置，跑四档：v0 / v1 无转发 / v1+转发 / v1+BHT
- [ ] G2. 每档出 cycles/instrs/bubbles/CPI + CoreMark/MHz + CoreMark/LUT 表；原始日志入档
- [ ] G3. 结论入 `report/`（四档表 + 测试条件 + 原始日志索引）

## 8. 纪律与风险

- 纪律：非纯文档 commit 走理解门槛（讲解 + 3 题）；单步 ≤100 行；每步汇报四件套
- 风险 1｜8B/计数器延期：宏占位 + plusarg 先行，只延迟出分，不阻塞移植层写码
- 风险 2｜移植卡住：退自写 benchmark 的 CPI 对比，CoreMark 列留空注明原因（`plan.md` §4.3 预案）
- 风险 3｜数据段超 32KB：官方配置项裁剪并注明口径，不用 DDR（触碰"零 DDR"卖点）
- 风险 4｜四档 RTL 未就绪：先出 v0 单档，其余档随 RTL 逐档补，M1 收口不受阻

## 9. 排期一览

| 阶段 | 日期 | 主责 | 出口 |
|:---|:---|:---|:---|
| A 契约收口 | 9/23–9/24 | bench（RTL/verify 复核） | 契约入库 |
| B RTL 前置 | 9/24–9/25 | RTL 线 | 8B + 计数器可用 |
| C vendor + 构建 | 9/25 | bench | `coremark.hex/.dis` |
| D 移植层 | 9/25–9/27 | bench | CRC 正确、观测块可读 |
| E 回归接入 | 9/27–9/29 | verify/bench | 一键跑分 + 证据 |
| F 数据入档 | 9/29–10/1 | bench | metrics 两行 + 日志 |
| G 四档对比 | 9/29–10/1 | bench（RTL 配合） | 四档数据表 |
