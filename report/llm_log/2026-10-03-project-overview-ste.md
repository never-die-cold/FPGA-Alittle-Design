# 2026-10-03 项目总览文档 + 7 幅数据流图：理解门槛问答（3/3 过）

> 任务：用户要求用 ASD-STE100 口径写全项目讲解，并配 RTL 组成与数据传输逻辑图。
> 产出：`docs/project-overview.md` + `docs/img/make_project_diagrams.py`（7 幅 PNG 可一键重生成）。
> AI 产出 prompt 要点：ASD-STE100 中文对应口径（短句/主动语态/一句一事/术语唯一/技术名保留原名）；
> 图须与 2026-10-03 RTL 现状一致且脚本可复现；先读 design_v0/v1 与 vision design_v0 再画。
> 视觉验收：visual-judge 子代理因账号连接不可用，按协议降级本人目检，两轮修复后 7/7 过。

## 理解门槛（用户作答，agent 对码核验）

### Q1 v0 为何无需转发？v1 哪类相关仍须停顿？

用户答：v0 靠拍序留出的时间，不靠转发：普通指令在执行拍末写回，下一条指令到下拍才读
寄存器，所以读到新值；lw 因数据 RAM 异步读而能同拍取数并写回。v1 仍需停 1 拍的是紧邻
load-use：数据到达时点晚于消费者 EX 级需要它的时点；把 DMEM 读值直接旁路到 ALU 会形成
过长组合路径，故用 interlock 等一拍。

核验：✅ design_v0.md §2.2（拍 k+1 末写回 / k+2 读到新值；lw 异步读同拍写回）；
regfile.v 组合读+时钟沿写；dmem.v `assign rdata = mem[addr]` 异步读；
design_v1.md §8.3「load-use 的 1 拍 interlock 优先于 mux……禁止建立 DMEM→ALU 零拍路径」。

### Q2 写 R0 后画面为何不变？软件如何确认生效？

用户答：R0–R10 是暂存配置，不直接驱动画面。顺序：确认 R11 busy=0 → 读 R12 算期望
下一编号 → R11 bit0 写 1 发起 commit → 轮询 R12 直到等于期望编号；硬件帧首原子应用后才
更新确认编号；无视频帧时等到超时。

核验：✅ pynq_host/vision_regs.py `commit()`：读 44 查 busy → 读 48 算 expected=+1 →
写 44=1 → `wait_applied(expected, timeout)` 轮询 48，超时 TimeoutError；
vision_top.v：config_bridge dst 侧 `if(dst_frame && req_sync!=acknowledge)` 帧首整组落地。

### Q3 写 Bank0 时 Bank1「恰好此刻写完」，回放选哪个？

用户答：若 Bank1 已完整有效且 wr_sel 指向 Bank0，回放选 Bank1：choose_rd 优先非写银行的
有效帧，start_replay 阻止读正在写的 wr_sel。时序细节：按当前 RTL，同一写侧不可能一边写
Bank0 一边让 Bank1 同拍完成——完成事件提交的是 wr_sel 指向的银行；Bank1 若在该拍完成，
须先置 buf_valid，回放最早下一拍才能选到它。

核验：✅ cop_buf.v `choose_rd = buf_valid[~wr_sel] ? ~wr_sel : wr_sel`；
`start_replay = ... && !((writing || in_vs) && choose_rd == wr_sel)`；
完成事件在 `in_hs && wr_row==DH-1` 分支且只置 `buf_valid[wr_sel]`，同拍置位对组合
start_replay 不可见。用户指出题面场景「同拍完成」在 RTL 中不成立，补充正确。

## 结论

3/3 过，准予入库。本步提交：docs/project-overview.md、docs/img/（脚本+7 PNG）、本日志。
不包含同工作区待另一道理解门槛的 pi-dev-roles 相关改动。
