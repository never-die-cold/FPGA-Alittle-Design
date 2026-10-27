# [2026-10-27] 协作记录：合并回归、A/B 变体分离与 A 首包门禁

> 标签：#coprocessor #Vivado #门禁 #交付包 #变体
> 平台：Codex + JL（Windows Vivado 2026.1）｜ 模型：GPT-5
> 相关 commit：`87cba27` `f2e32b7` `864e334` `ec44f4f` `f7fbe8a` `2fc2bdd` `6536775`

## 1. 任务与初始提示词

合并 `origin/dev/riscv` 后重跑协处理器回归，确认 AXI-Lite CDC 三级同步与多目标
`COMMIT_RESULT` 的影响；把“核+协处理器 A 变体”和“含视频 B 变体”彻底分开；
A 变体经 Windows 整机 40 MHz 门禁后才能打首包；旧包一律作废，不得混入 B 视频产物。

## 2. 模型第一版方案

- 合并冲突 `tools/cop_payload_loader.py`：同时保留 direct 精确 40 MHz/首 STATUS 守卫与
  HWH MMCM 输入时钟方案。
- `cop_axi_lite_cdc.v`：控制 toggle/ack 两级→三级，载荷仍两级；hold 显式复位。
- `cop_task_ctrl.v`：新增 `COMMIT_RESULT`，每个非末目标多一拍，N 目标整轮净增 N−1 拍。
- 构建变体：A 默认不装视频源；B 仅 `COP_WITH_VIDEO=1` 时加入 HDMI/视觉/VDMA/HP1。
- 旧包 `f856d5861db0`、`759744b99891`、`5653d5911b76` 作废但保留目录追溯。

## 3. 失败现象

1. 合并唯一冲突在 loader：direct 时钟守卫与 MMCM 方案必须并存，不能二选一。
2. 三目标夹具从 18 拍变为 20 拍：两个非末目标各多 1 拍 `COMMIT_RESULT`；
   旧断言需改成精确 20 拍，不能放宽为“≥18”。
3. 裸 `all` 首次退出 1：系统 `python3` 缺 NumPy，失败在网络向量生成，不是 RTL/TB 红项。
4. A 首包门禁 WNS 从上一版 +3.071 降到 +2.078（三级同步与 `COMMIT_RESULT` 增加逻辑），
   但仍为正；CDC 计数保持 73/12/7，未新增 allowlist。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | loader 冲突 | 两套时钟守卫都需保留 | 合并 direct + MMCM 分支 | 门禁解析 PASS |
| 2 | 三目标 18→20 拍 | 新增提交隔离拍 | TB 精确断言 20 拍 | `cop_multitarget_commit` PASS |
| 3 | 裸 all 退出 1 | 环境缺 NumPy | 显式仓库 venv 复跑 | `all` 退出 0 |
| 4 | A/B 产物可能混用 | 变体未隔离 | A 默认不装视频，B 仅开关启用 | FILES 不含 vision/HDMI |
| 5 | 旧包仍在 dist | 会误上传 | 明确作废清单 | 只上传 A 新包 |

## 5. 最终结论

A 变体 Windows 门禁 PASS：WNS **+2.078 ns**、DSP **136/220**、BRAM36 **69/140**、
LATCHES=0、DRC=0；`IMEM_FIRST_WORD=0x00008117`、`READMEM_WARNINGS=0`；
CDC-15=73、CDC-3=12、CDC-6=7，allowlist 仍 5 条。

- bit：`f325a0dc4c2cb143e24ef13df6608e206af5c58f0354b3deec6f039d5875f71f`
- hwh：`480d04a3d9abee59e81892378c2457dfe92ea0cf6fc0822d4467b2121dbab358`
- xsa：`9e0a56276e89e2a94e3155eea7e267c97b97014ed74c8874524d03eaa462534c`
- 包：`dist/cop-board-gate-2fc2bdd4a8f8/`；tar SHA256
  `e2eb5bd340f01c9cbfb2930a55d8ec36cbbdcdd6f0923636ed1e812b8b862127`
- `FILES.txt`/`SHA256SUMS` 各 116 行，`sha256sum -c` 116/116 OK；FILES 不含
  `attach_pynq_video`、`src/vision`、HDMI XDC。

`BOARD=UNVERIFIED_NEEDS_NC`、`BOARD_CLOCK=UNVERIFIED_NEEDS_40MHZ_READBACK`、
`LOADER=BLOCKERS_RESOLVED_PENDING_BOARD_VALIDATION`、`BUILD_VARIANT=A_core_plus_coprocessor_ONLY`。
只上传 A 的 tar.gz 与 .sha256，不上传裸 bit/hwh/xsa 或 B 视频变体。

## 6. 经验沉淀

- 触发条件：合并后新增握手级数/提交隔离拍，且要拆分交付变体。
- 排查步骤：冲突按“两套守卫都保留”合并；时序断言用精确拍数；裸命令失败先查解释器；
  A/B 变体从构建开关和文件清单两端隔离；旧包显式作废。
- 适用范围：所有多提交/多变体交付；换 Vivado 版本需重新门禁。
#skill候选
