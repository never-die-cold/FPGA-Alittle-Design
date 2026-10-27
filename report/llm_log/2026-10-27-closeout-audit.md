# 2026-10-27 全仓收尾审计（只读）

范围：全仓，排除 `.git/`、`sim/build/`、`dist/`、`build/run/` 产物。审计基线为
`dev/riscv@0430257e22331b73d91967eaaeaf652d3585e045`，开始时工作区干净、相对
`origin/dev/riscv` ahead 0。本文件是本轮唯一写入；未运行 Vivado，也不产生板级结论。

## 1. 结论摘要

- 当前权威状态应以 `src/coprocessor/plan.md:21-26` 为准：J04b/J07/J08 为部分完成，
  J05/J06/J09 未完成。A 变体只完成整机综合实现门禁，BOARD 仍未验证。
- A 变体的 WNS/资源/IMEM/CDC 数字和 bit/hwh/xsa 哈希只在当前文档与忽略目录中；Git
  没有原始 `gate_summary.txt`、报告、tar 或 sidecar，干净 checkout 不能独立复核该结论。
- 协处理器 runner 的 35 个模式均非空，26 个 `tb_*.v` 全部被 runner 覆盖；无孤儿 Verilog TB。
- J02 当前 BRAM 对拍仍为 pattern/zero 各 9,225 packed words、73,795 elements、472,594 cycles，
  `EXPECTED_OUTPUTS.tsv` 的结果 CRC/日志 CRC 与本轮实跑一致，不存在只比 argmax 的验收。
- 主要收尾遗漏是当前文档互相矛盾：现行交接单仍写“核清终态”、物理 bank 未实现、整机未实现，
  与冻结 A2、现 RTL/TB 和 A 门禁事实冲突。

## 2. J04b/J05/J06/J07/J08/J09 状态对齐

| 项 | 审计后的真实状态 | 当前计划 | 其它文档偏差 |
|:---|:---|:---|:---|
| J04b | 🟡。manifest→影子物理 bank、A 整机门禁已完成；结果 DMA、任意描述表和当前 A 包板验未完成 | `src/coprocessor/plan.md:21,40-46` 基本准确 | `src/coprocessor/README.md:15-17,24,61`、`docs/contracts/coprocessor-handoff-v0.md:9,12,17,48,54,59-60,78`、`docs/closeout-todo.md:15,44-56` 仍称物理 bank/SoC/综合/位流未完成 |
| J05 | ⬜。只有 ROI 结构审计工具和合成自测，没有真实审计 ROI、训练/评估 | `src/coprocessor/plan.md:22` 准确 | 未发现把合成数据审计写成真实数据验收；`docs/roi-dataset-handoff.md:26` 明示规划目标 |
| J06 | ⬜。没有 RELEASE 模型、正式参数/黄金/审批链 | `src/coprocessor/plan.md:23` 准确 | `kind=PROVISIONAL` 边界在 `docs/contracts/coprocessor-manifest-v1.md:5-9`；未发现冒充 RELEASE |
| J07 | 🟡。B 变体已有离板视频/VDMA/HP1 集成源码，但综合、实现、板上均未验证 | `src/coprocessor/plan.md:24` 准确 | `docs/closeout-todo.md:62` 仍把“首网硬件输出”错误归到 J07；实际 J07 交付定义见 `docs/project-closeout-three-person-checklist.md:89` |
| J08 | 🟡。A PROVISIONAL 首包存在且门禁通过，待 NC；正式首网/视频整机包未交 | `src/coprocessor/plan.md:25` 准确 | `docs/contracts/coprocessor-handoff-v0.md:17,60` 仍称没有位流/可交包、三包均未发布 |
| J09 | ⬜。当前 A 包尚无 NC 回传，不能开始针对它的离板复现修复 | `src/coprocessor/plan.md:26` 准确 | 无提前完成表述 |

三层状态没有在当前权威计划中混写；`docs/coprocessor-nc-handoff.md:48-52` 正确分列仿真 PASS、
综合实现 PASS、板上 UNVERIFIED。混写/漂移发生在旧的当前入口：
`src/coprocessor/README.md:61` 把“整机时序未验证”继续写成当前事实，
`docs/contracts/coprocessor-handoff-v0.md:59` 把综合、实现、位流、板上四者一起写为未验证；前两项实际上已过 A 门禁。

## 3. 审计问题表

| 编号 | 类别 | 严重度 | 事实 | 证据（路径:行／命令输出） | 建议动作 | 谁能做 |
|:---|:---|:---|:---|:---|:---|:---|
| A01 | 冻结语义 | 阻断 | 当前 J04 交接单仍称由核写三个旧 CLEAR 位清终态，直接违反 A2 的 PS 独占 CONSUME | 错句 `docs/runbooks/coprocessor-j04-handoff.md:74`；现行契约 `docs/contracts/coprocessor-integration-v0.md:377-383`；实现摘录 `docs/coprocessor-wc-interface.md:32-43` | 将旧交接单标历史或改成 A2 现行语义，禁止 WC/NC 按旧清灯流程接入 | JL/WC |
| A02 | 状态真实性 | 高 | 当前交接索引自相矛盾：先写整机/位流未验证，又写旧整机 PASS，最后仍称没有整机/位流/交付包 | `docs/contracts/coprocessor-handoff-v0.md:12-17,59-60`；当前事实 `src/coprocessor/plan.md:21,40-46` | 当前状态只保留 A 门禁 PASS、BOARD 未验、B 未验；旧门禁移到历史小节 | JL |
| A03 | 状态真实性 | 高 | 模块 README 仍称物理 bank、SoC/视频集成未实现，实际 payload 影子 bank 和 A 板顶已落地 | `src/coprocessor/README.md:15-17,24,61`；`src/coprocessor/cop_payload_adapter.v:1-18`；`src/riscv/pynq_cop_top.v:1-18`；本轮 `payload_network` PASS | 对齐模块计划，保留结果 DMA/BT-4/板验缺口 | JL |
| A04 | 状态真实性 | 高 | 根计划仍把 payload 物理 bank 列为未实现/下一交付物 | `plan.md:134,143`；当前计划 `src/coprocessor/plan.md:40-46` | 从“未实现”移出，改列结果 DMA、描述表、板验和正式模型 | JL |
| A05 | 状态真实性 | 高 | 无日期收尾表仍锚定旧提交/无板/本机有 Vivado，并把已完成 bank/固件 E2E/整机门禁列未完成 | `docs/closeout-todo.md:14-19,44-56`；当前 HEAD/环境命令输出为 `0430257`、WSL 无 Vivado；当前计划 `src/coprocessor/plan.md:21` | 重新基线化该“当前表”，否则停止作为入口 | JL |
| A06 | 门禁文档 | 中 | Vivado checklist 页首说当前门禁 PASS，正文又说 A 的数字/bit 均 UNVERIFIED，且命令复用已存在、会 fail-closed 的 build name | `docs/coprocessor-vivado-checklist.md:3-4,14,22-31,76-85`；`build/build_pynq_cop_gate.tcl:134-140` | 保留历史表，新增 20261027_r1 最终行；示例 build name 改成占位的新名字 | JL |
| A07 | 时钟文档 | 中 | 时钟 runbook 仍称 IMEM 门禁后的源码尚待重跑，已被 A 门禁事实否定 | `docs/coprocessor-board-clock-runbook.md:3-7`；A 门禁 `docs/coprocessor-build-variants.md:18-23` | 指向当前 A 包，同时继续保留 BOARD/BOARD_CLOCK 未验证 | JL/NC |
| A08 | 证据链 | 阻断 | A 门禁 2.078 ns 的原始报告未跟踪；干净 checkout 只有二手摘要 | `git ls-files 'build/reports/**'` 无输出；`.gitignore:79` 忽略 `/build/reports/pynq_*/`，`:64` 忽略 `/dist/`；摘要 `report/llm_log/2026-10-27-coprocessor-variant-a-gate.md:41-53` | 将 gate_summary、关键 timing/util/CDC/DRC 原始报告归档到 `data/logs` 并写 commit/命令/退出码 | JL |
| A09 | 证据链 | 阻断 | 当前唯一有效 tar/sidecar 未跟踪，也没有 Release URL/上传回执；NC 无仓库内可取得的交付物 | `docs/coprocessor-nc-handoff.md:78-93`；`git ls-files 'dist/**'` 无输出；包摘要 `report/llm_log/2026-10-27-cop-a-gate-package.md:29-59` | 只上传 tar.gz+sidecar 到 Release，并在交接页记录 URL、哈希和上传回执 | JL |
| A10 | 证据链 | 高 | J04 交接单的“交付文件指纹”已过期，会把当前正确源码判错 | 文档 `docs/runbooks/coprocessor-j04-handoff.md:28-61`；现值：`cop_task_ctrl.v` 64 行/`1253cac…`、`cop_top.v` 200 行/`7d52a50…`、runner 193 行/`663b8d2…` | 不再维护手抄全表，或重算并绑定当前 commit | JL |
| A11 | OPEN 台账 | 高 | OPEN-1 仍挂“物理 bank 未实现”，但 manifest→影子 bank→原子切换已有 RTL 和逐元素整网证据 | 旧项 `docs/runbooks/coprocessor-j04-handoff.md:104,114-115,126-127`、`docs/contracts/coprocessor-ps-driver-v0.md:150`；实现 `sim/coprocessor/tb_cnn_sequencer.v:73-87,144-175`；PASS 输出 `payload_network ... shadow BRAM ...` | OPEN-1 标已关闭；不要连带关闭结果 DMA/描述表/板验 | JL/WC |
| A12 | OPEN 台账 | 高 | OPEN-K2-1 一处已关闭、一处仍明确未确认 | 已关 `docs/coprocessor-nc-handoff.md:128-129`；仍开 `docs/coprocessor-storage-plan.md:54-55` | 存储计划保留 PLAN，但把 K2-1 标“综合资源已关、生产模型/板验另列” | JL |
| A13 | OPEN 台账 | 阻断 | 当前 A 包 BOARD/BOARD_CLOCK/LOADER 仍待 NC，不能从门禁 PASS 推导板级可用 | `docs/coprocessor-nc-handoff.md:48-52,90`；`src/coprocessor/plan.md:21,25` | NC 按新包跑时钟、首读、固件活性、pattern/zero、连续轮次并回传 | NC |
| A14 | 产品证据 | 阻断 | J05/J06 没有真实 ROI、正式模型、阈值、RELEASE manifest，PROVISIONAL 不能收产品 | `src/coprocessor/plan.md:22-23,57`；`docs/contracts/coprocessor-manifest-v1.md:5-9` | 完成真实数据审计、训练/量化、正式黄金和审批链 | JL/WC/NC |
| A15 | 实现缺口 | 高 | 完整 C03 仍缺 RESULT_ADDR 结果 DMA 和任意 TARGET_DESC_ADDR；非恒等 target/ROI 不能验收 | `docs/runbooks/coprocessor-j04-handoff.md:128-129`；`docs/contracts/coprocessor-ps-driver-v0.md:141,149`；`src/coprocessor/plan.md:41,46` | 维持 OPEN-2/BT-4；完整整机包前实现并补非恒等对拍 | JL |
| A16 | 回归入口 | 高 | 文档指定的相对 venv 在全仓 wrapper 中失效：wrapper 先 `cd sim`，子 runner 找不到该相对路径并退到不存在的 `python` | `sim/scripts/run_iverilog.sh:102,157-160`；实跑 `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python ... all` 最终 `run_coprocessor_iverilog.sh: line 32: python: command not found`，exit 1 | wrapper 在改 cwd 前规范化 Python 为绝对路径，或文档使用绝对路径/由 runner 相对 ROOT 解析 | JL |
| A17 | 环境依赖 | 中 | 裸协处理器 all 今天仍因系统 Python 缺 NumPy退出 1，OPEN-ENV-1 未关闭 | 实跑 `bash sim/scripts/run_coprocessor_iverilog.sh all`：`ModuleNotFoundError: No module named 'numpy'`，exit 1；台账 `docs/coprocessor-nc-handoff.md:131` | 给入口稳定建 venv/依赖预检；在干净环境复跑后再关 | JL |
| A18 | 仿真日志 | 中 | 固件 E2E/PYNQ top 直接载 4094-word `cop_job.hex`，Icarus 对 8192 深度发 readmemh 不足警告；Vivado 用派生补齐镜像，两路径口径不同 | `src/riscv/imem.v:15-19`、`src/riscv/dmem.v:17-21`；本轮 all 原始输出两条 `Not enough words ... [0:8191]`；综合策略 `docs/coprocessor-imem-init-gate.md:42-51` | 仿真也载门禁生成的 8192-word镜像，或明确该 warning 仅仿真源 hex 且不得进入综合日志 | JL |
| A19 | RTL 卫生 | 低 | 17 个 `src/riscv/*.v` 缺 `timescale`，全量仿真持续打印继承 timescale；不影响本轮功能结论 | `iverilog -g2001 -Wall -s pynq_cop_top ...` 输出从 `alu.v:3` 到 `soc_top.v:3` 的缺失列表，exit 0 | 若团队要求日志零噪声，统一补；不得把它当功能 FAIL | JL |
| A20 | RTL 卫生 | 低 | 未发现当前综合路径的 `.*`/`logic`/`always_ff`、`$display`、绝对 `/tmp`；`initial` 仅 IMEM/DMEM 初始化且有门禁 | grep 无命中；`src/riscv/imem.v:15-19`、`dmem.v:17-21`；A 门禁摘要 `docs/coprocessor-build-variants.md:18-23` | 无动作；B 变体综合后仍需重复同一检查 | JL |
| A21 | RTL 卫生 | 中 | 未发现 A 变体锁存器或已知多驱动；但 Verilator 全顶 lint 被实例名 `mailbox`（SV 关键字）提前阻断，当前“无问题”主要依赖 Icarus/Vivado | `src/coprocessor/cop_top.v:88`；Verilator `unexpected TYPE-IDENTIFIER` exit 1；Icarus `-g2001` 顶层编译 exit 0；门禁 LATCHES=0 见 `docs/coprocessor-build-variants.md:18-20` | 若要把 lint 作为证据，固定 Verilog-2001 lint 工具/模式；不据失败推断 RTL 功能错 | JL |
| A22 | 文档索引 | 中 | docs/README 与子 README 未覆盖 20 个现存 Markdown；路径死链为 0 | 本轮索引脚本输出 `TEXTUAL_ORPHAN_COUNT 20`、URL decode 后 `DEAD_COUNT 0`；清单见 §8 | 将当前文档挂索引；模板/外包副本可明确标排除 | JL/WC |
| A23 | 旧包台账 | 低 | 七个作废包的命中大多是日期证据，但多份历史文件仍使用“当前有效包”措辞，离开日期上下文会误用 | 命中示例 `data/logs/2026-10-25-dma16-merge-gates/README.md:23-27`、`report/llm_log/2026-10-26-coprocessor-j07-board-tools.md:48-51`；当前表 `docs/coprocessor-nc-handoff.md:90-93` | 历史记录不改事实，只加“历史/已作废”醒目标记；当前入口只指 2fc2bdd4a8f8 | JL |
| A24 | 机器依赖 | 中 | Vivado 默认路径仍分裂：现文档实际路径为 `D:\vivado\...`，两个脚本默认 `D:\Vivado_downloads\...` | `docs/coprocessor-vivado-checklist.md:23-35`；`build/run_pynq_cop_gate.ps1:1`；`board/scripts/program_soc.bat:3-7` | 默认值取消或统一为参数/环境变量；文档列 COP_PYTHON、COP_BUILD_NAME、COP_WITH_VIDEO | JL |

严重度统计：阻断 5，高 9，中 7，低 3。

## 4. 文档与事实不一致清单（错误原句）

1. `docs/runbooks/coprocessor-j04-handoff.md:74`：
   “`核写 CLEAR_DONE/CLEAR_ERROR/CLEAR_RESULT_VALID 执行 W1C`”。现行 A2 是 PS 独占
   `CTRL[6]=CONSUME`，旧 bit3/4 清除命令停用且零副作用。
2. `docs/contracts/coprocessor-handoff-v0.md:12`：
   “`Vivado 40 MHz 门禁、bitstream、.hwh 与板上仍 UNVERIFIED`”。A 门禁、bit/hwh/xsa 已有，
   只有板上仍 UNVERIFIED。
3. 同文件 `:17`：“`J07/J08 未完成：没有整机实现、位流或可交 NC 上板...`”。已有 A 整机实现和
   PROVISIONAL 首包；正确缺口是 B/正式模型/当前 A 的 NC 验收。
4. `src/coprocessor/README.md:15`：“`DataMover payload 到各物理 bank 的生产地址适配...`”仍列 OPEN；
   当前 payload adapter、双 bank 和逐元素 payload_network 已通过。
5. 同文件 `:61`：“`实体 BRAM生产地址适配、SoC/视频与板端集成...未实现`”。物理 bank/A SoC 已实现；
   B 视频仅离板接入、未综合/板验。
6. `plan.md:134,143`：“`payload 物理 bank...未实现/下一交付物`”。与现 RTL/TB 不符。
7. `docs/closeout-todo.md:48-49`：“`B04 ... 是目前唯一没被行为验证过的固件路径`”。
   `firmware_e2e` 已真实执行 CPU/固件/MMIO 两轮并 PASS。
8. `docs/coprocessor-vivado-checklist.md:30-31`：“`A 的新 WNS...和 bit/hwh 均为 UNVERIFIED`”。
   同文件 `:3-4` 已称整机 PASS，且当前 A 数字/哈希见 build-variants。
9. `docs/coprocessor-board-clock-runbook.md:6-7`：“`加入 IMEM 初始化门禁后的新源码尚待重跑`”。
   当前 A 已给出 IMEM 首字/非零/零 warning 门禁。
10. `docs/coprocessor-storage-plan.md:54-55` 仍说 OPEN-K2-1 等 Vivado 确认；
    `docs/coprocessor-nc-handoff.md:128-129` 已按 BRAM36=69 将其关闭。

没有发现把当前 A 的“综合实现 PASS”直接写成“板级 PASS”；当前交接页正确保持 BOARD 未验证。

## 5. 无证据结论清单

1. **A 变体整机门禁 PASS 的 Git 内原始证据缺失**：有 commit 摘要、命令、产物哈希，但
   `build/reports/pynq_cop_a_20261027_r1/` 被忽略；缺可提交的原始 timing/util/CDC/DRC/summary 与退出码。
2. **“当前唯一有效包 116/116 OK”缺可取得产物**：tar、sidecar、FILES、SHA256SUMS 都在忽略的
   `dist/`，仓库没有 Release URL/上传回执。文档哈希不能替代附件本身。
3. **OPEN-K2-1 已关闭的引用路径不稳定**：`docs/coprocessor-nc-handoff.md:128` 指向旧固定目录
   `build/reports/pynq_cop_40mhz/utilization_impl.rpt`，当前门禁使用 build name
   `pynq_cop_a_20261027_r1`，且两者都未入 Git。

J05/J06/J09、B 变体、BOARD 均明确写成未验证/未完成，不属于“无证据却宣称通过”。

## 6. OPEN 全量核对

| OPEN | 审计状态 | 依据 |
|:---|:---|:---|
| OPEN-K2-1 | 资源综合已关，但存储计划台账未同步 | `docs/coprocessor-nc-handoff.md:128-129` vs `docs/coprocessor-storage-plan.md:54-55` |
| OPEN-FW-1 | 待外验；综合/bit 已含固件，板上当前 A 固件活性未验 | `docs/coprocessor-nc-handoff.md:130` |
| OPEN-ENV-1 | 未解；裸 all 本轮 exit 1 | `docs/coprocessor-nc-handoff.md:131` + 本轮命令输出 |
| OPEN-DOC-1 | 已修复，留痕正确 | `docs/coprocessor-nc-handoff.md:132`，runner `firmware_e2e` 明确加载 hex |
| OPEN-BT-4 | 未解；非恒等 target/ROI 不可验收 | `docs/coprocessor-nc-handoff.md:133-136` |
| OPEN-BOARD-CLK-1 | 根因/顺序已解，当前 A 仍待 40 MHz 回读外验 | `docs/coprocessor-nc-handoff.md:139-140` |
| OPEN-IMEM-1 | 综合侧已关、板上当前 A 待验 | `docs/coprocessor-nc-handoff.md:141-142` |
| OPEN-LOADER-1/2 | 离板已修、板上待验 | `docs/coprocessor-nc-handoff.md:143-146` |
| OPEN-1 | **实现已解决但旧台账仍挂未解** | A11 证据 |
| OPEN-2 | 未解：RESULT_ADDR DMA | `docs/runbooks/coprocessor-j04-handoff.md:128-129` |
| OPEN-3 | 实现采用保守规则；旧交接仍要求再冻结 | `docs/runbooks/coprocessor-j04-handoff.md:130-134` |
| OPEN-4/7 | 原“单相位”描述已过期；AXI CDC/异步 FIFO已有随机比率和门禁，返回多位语义仍需按实际边界拆项 | 旧述 `docs/runbooks/coprocessor-j04-handoff.md:135-144`；runner `axis_fifo_random`/`axi_lite_cdc` PASS |
| OPEN-5 | 未解：IRQ 链未签收，轮询可用 | `docs/runbooks/coprocessor-j04-handoff.md:138-139` |
| OPEN-6 | 未解：FW_DECISION 对外布局仍标暂定 | `docs/runbooks/coprocessor-j04-handoff.md:140-141` |
| OPEN-8 | Icarus数组敏感列表 warning 仍在；实体 bank 问题应从本项拆除 | `docs/runbooks/coprocessor-j04-handoff.md:145-147` + 本轮 warning |
| OPEN-9 | 未解：VERSION/CAPABILITY 固定 0 | `src/coprocessor/cop_top.v:127-129` |
| OPEN-10 | 未解且属于已登记契约偏离：空闲 ABORT 行为不同 | `docs/runbooks/coprocessor-j04-handoff.md:151-153` |
| OPEN-11 | 未解：有效空场景无法表达 | `docs/runbooks/coprocessor-j04-handoff.md:160-163` |
| OPEN-12 | 已关闭（OOC 历史）；整机 A 门禁另有当前数字 | `docs/runbooks/coprocessor-j04-handoff.md:154-159` |
| OPEN-BOARD-1 | 生产顶层已实现，应标历史已关；旧命中只在 dated llm_log | `report/llm_log/2026-10-22-board-gate-vivado.md:64`；现顶 `src/riscv/pynq_cop_top.v` |

未发现未登记的新实现偏离；当前已知的结果 DMA、描述表、IRQ、只读常量、空闲 ABORT、空场景均已有 OPEN。

## 7. 回归、golden 与 RTL 卫生

### 7.1 本轮实跑

| 命令 | 结果 |
|:---|:---|
| `bash sim/scripts/run_coprocessor_iverilog.sh all` | exit 1；系统 Python 缺 NumPy，最后错误 `ModuleNotFoundError` |
| `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh all` | exit 0；pattern/zero 行为级各 73,795 元素、472,593 cycles |
| 同环境 `... bram_network` | exit 0；读延迟边界 PASS；pattern/zero 各 73,795 元素、472,594 cycles |
| 同环境 `run_coprocessor_python.sh all` | exit 0；10 组全部 PASS |
| `bash sim/scripts/run_coprocessor_python.sh manifests` | exit 0 |
| `bash sim/scripts/run_iverilog.sh cop_mac_lane` / `cop_dot8` | 两者 exit 0 |
| 相对 venv 环境运行 `bash sim/scripts/run_iverilog.sh all` | exit 1；进入嵌套 cop runner 后 `python: command not found` |
| 四个 shell 脚本 `bash -n` | exit 0 |

runner 静态双向映射命令输出：`TB_COUNT 26 MAPPED_COUNT 26`、`ORPHAN_TB NONE`、
`MODE_COUNT 35`、`EMPTY_MODES NONE`。Python `test_int8_*.py` 由独立
`run_coprocessor_python.sh` 的 10 个模式覆盖，不是 Verilog runner 的孤儿 TB。

### 7.2 强度与数值

- `tb_cnn_sequencer.v:114-129` 对每次写出的 layer/address/data 与 golden 精确比较，并禁止重复位置；
  `:184-190` 再核写数、读事务、参数读、logits/class/margin/score/low_conf。
- `tb_cop_bram_latency.v:15-23` 明确要求早/晚一拍错误可见。
- 本轮 BRAM 日志重算：pattern `result_crc32=b47dd829`、`sim_log_crc32=734b84a1`；
  zero `cdc9b738`、`2d1239b4`，与包表逐项相同。打包脚本来源见
  `sim/scripts/package_coprocessor_nc.sh:78-97`。
- 行为数组模式 472,593 与同步 BRAM 模式 472,594 相差一拍是模式差异；包的
  `EXPECTED_OUTPUTS.tsv` 明确取 BRAM 日志，不是过期期望。
- 未发现“只比 argmax/只比大小”作为整网验收；最终分类检查不能替代上述逐元素断言。

### 7.3 RTL 静态检查

- `iverilog -g2001 -Wall -s pynq_cop_top ...` exit 0；综合源未命中 `.*`、`logic`、
  `always_ff/always_comb`，未命中 `$display` 或绝对 `/tmp`。
- `$readmemh` 只在 `src/riscv/imem.v:19`、`dmem.v:21`；`initial` 仅用于可综合内存初始化，
  已有 pre/post synth IMEM 门禁。
- 当前 A 门禁报告摘要为 LATCHES=0、DRC=0；静态审计未确认多驱动。B 未综合，不能借 A 结论。
- 17 个 RISC-V 综合文件缺 timescale并在 Icarus 中继承 TB timescale；这是日志确定性问题，
  不是本轮发现的功能错误。

## 8. 孤儿／死链清单

### 8.1 测试

- 孤儿 Verilog TB：0。
- 空 runner 模式：0。

### 8.2 文档索引

路径死链：0（检查 492 个本地 Markdown 链接，先 URL decode；生成模板不按仓库当前位置解析）。

未被 `docs/README.md` 或最近子目录 README 文本覆盖的 Markdown：20 个：

1. `docs/branch-layout.md`
2. `docs/contracts/coprocessor-ps-driver-v0.md`
3. `docs/enclosure/acrylic-three-tier-concept-v1.md`
4. `docs/enclosure/enclosure-v1-measure-and-material-sheet.md`
5. `docs/file-guide/tools/README-template.md`
6. `docs/localization-dataset-audit.md`
7. `docs/localization-experiment-results.md`
8. `docs/localization-exploration-audit.md`
9. `docs/non-algorithm-plan.md`
10. `docs/outsource/cop-cnn-requirements.md`
11. `docs/outsource/fastener-vision-2026-10-07/localization-dataset-audit.md`
12. `docs/outsource/fastener-vision-2026-10-07/localization-experiment-results.md`
13. `docs/outsource/fastener-vision-2026-10-07/localization-exploration-audit.md`
14. `docs/outsource/localization-requirements.md`
15. `docs/project-overview.md`
16. `docs/runbooks/concurrent-agent-audit-2026-10-27.md`
17. `docs/runbooks/pynq-coexist-handoff-2026-10-27.md`
18. `docs/修订方案-受控流水线.md`
19. `docs/工作进展汇报.md`
20. `docs/方案探索报告.md`

## 9. 作废包命中分类

| token | 应如何处理 |
|:---|:---|
| `f856d5861db0` | `data/logs/2026-10-22-board-top-sync/README.md:20` 和 dated llm_log 是历史；当前入口须标作废并指向 2fc2bdd4a8f8，现 `docs/coprocessor-nc-handoff.md:7-8,91` 已正确 |
| `759744b99891` | 10/25 DMA16 日志/llm_log 保持历史但标作废；当前入口指 2fc2bdd4a8f8 |
| `5653d5911b76` | 10/26 IMEM/J07 日志保持历史但标作废；其中“唯一有效包”只对当日快照成立 |
| `d66916c49b80` | 10/24 runtime/10/25 rework 记录保持历史并标作废 |
| `21c4e751bbe8` | 10/23 首次上板原始记录保持历史并标作废，不应改写为新包实测 |
| `b821aa1d0c1f` / `c4839f39be2d` | 10/22 中间包记录保持历史；当前交接 `docs/coprocessor-nc-handoff.md:93` 已明确作废 |

需要改指当前包的是“当前状态/下载入口”，不是历史原始日志。历史日志不得把旧实测冒认到新包。

## 10. 硬编码与环境依赖

| 依赖 | 当前情况 | 处置判断 |
|:---|:---|:---|
| `COP_PYTHON` | Windows Tcl 必须显式设置，避免 WindowsApps 占位符；已写 `docs/coprocessor-vivado-checklist.md:18-35` | 文档已覆盖；脚本 fail-closed，保留参数 |
| `COP_BUILD_NAME` | 必须全新；当前示例固定已使用的 `pynq_cop_a_20261027_r1` | 示例应改占位符/新名字，不能照抄旧名 |
| `COP_WITH_VIDEO` | A 未设、B 精确为 1 | `docs/coprocessor-build-variants.md:53-59` 已覆盖 |
| `COPROCESSOR_PYTHON` / `VISION_PYTHON` | 相对路径跨 wrapper 的 `cd sim` 失效；裸 Python 又缺 NumPy | 应由 runner 基于仓库 ROOT 规范化，文档不能依赖忽略目录恰好存在 |
| Vivado 路径 | 文档为 `D:\vivado\2026.1\...`；脚本默认另一路径 | 应改成参数/环境变量，默认不写特定机器盘符 |
| PYNQ Python | `/usr/local/share/pynq-venv/bin/python3` 是目标镜像依赖 | 已写板端 runbook；保留为目标环境要求，并提供 `python3` 备选命令 |
| 历史 `/home/xilinx/...`、Windows盘符 | 多数位于 `data/evidence`/archive 的原始证据 | 不参数化历史证据；当前可执行脚本不得依赖这些路径 |

## 11. P0 阻断项（5 条）

1. 修正当前 J04 交接单的旧 CLEAR/W1C 语义；不修会让 WC/NC 清错寄存器并破坏终态证据。
2. 把 A 门禁原始报告与退出码纳入可追溯证据；不修则 2.078 ns/资源/CDC 只能信二手摘要。
3. 上传唯一 A tar.gz+sidecar并登记 Release URL；不修则 NC 无法取得与哈希对应的当前包。
4. NC 对当前 A 包完成 40 MHz、固件活性、pattern/zero 与连续轮次验收；不修则 J04b/J08 不能收口。
5. 完成 J05/J06 真实 ROI→RELEASE 模型/黄金链；不修则只能演示诊断网络，不能形成产品模型交付。
