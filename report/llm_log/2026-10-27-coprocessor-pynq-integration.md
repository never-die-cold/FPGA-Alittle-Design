# [2026-10-27] 协作记录：PYNQ 原始采集/硬件推理接入 LIVE API

> 标签：#coprocessor #PYNQ #vision #LIVE #CDC
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`7962b60` `2eab8f1` `3f48055` `e894515` `7a3603f` `3404c33` `cfbded8`

## 1. 任务与初始提示词

把原始 HDMI 采集与硬件推理接入 LIVE API；板端加载/payload 包必须绑定 HWH 拓扑；
视觉启动要排在 stock PL 初始化之后；快速模式、阻塞自行解决，最后分多个 commit、push、
开 PR 合并后同步各分支。理解门槛题留到最后，不得代答或虚勾。

## 2. 模型第一版方案

- AXI-Lite CDC：payload 两级采样，请求/ACK 三级，给并行数据一拍稳定余量；
  held bus 与 Gray 指针加明确延迟/偏斜约束。
- 多目标结果：消费者在下一时钟沿看到寄存的 `result_write`；`COMMIT_RESULT` 保持旧槽号到
  该沿再推进 ROI，避免第 0 槽漏写和后续错位。
- 固件：按新的 `CFG_APPLIED` 连续接单，等待上一单 PS CONSUME；同配置不重复执行。
- 时钟/打包：从 HWH 判定直连或 MMCM，保持 142.857 MHz 输入并核对；包目录拒绝覆盖。
- PS 驱动：配置提交后重新装载模型，恢复被硬件清除的有效标志；等当前序号固件判定再读计数。
- 启动：systemd 依赖 bootpy，不再用两个固定 sleep 的并发脚本抢 PL。

## 3. 失败现象

1. 请求/ACK 与并行 payload 同拍到达时，可能读到上一个地址的数据，需要一拍稳定余量。
2. 在拉高 `result_write` 的同拍切换 `result_index`，会导致第 0 槽漏写/后续槽错位。
3. 固件缓存“权重上次已装载”，每次 `CFG_COMMIT` 后下一单不启动。
4. 两个固定 sleep 的并发启动脚本会抢 PL，视觉在 stock PL 初始化前启动。
5. 新包构建失败，不能改写为 PASS；手动按钮核验与 CSV 导出未完成。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | payload 同拍采样可能读旧值 | 缺稳定余量 | payload 两级、req/ack 三级 | CDC 回归 PASS |
| 2 | 第 0 槽漏写 | 同拍切换索引 | `COMMIT_RESULT` 保持旧槽号一拍 | 三目标 20 拍 PASS |
| 3 | 下一单不启动 | 配置缓存误判 | 每次 CFG_COMMIT 重新装载 | 双作业 E2E PASS |
| 4 | 视觉抢 PL | 启动顺序竞态 | systemd 依赖 bootpy | 启动顺序修正 |
| 5 | 新包构建失败 | 不能造假 PASS | 保留失败，标 UNVERIFIED | 边界诚实 |

## 5. 最终结论

合并 PR #89 后，PYNQ 集成包含：原始 HDMI 采集 + 硬件推理接入 LIVE API、HWH 绑定加载、
启动顺序修正、CDC/多目标修复。验证入口见 `data/logs/2026-10-27-git-integration/README.md`，
实板边界见 `docs/runbooks/pynq-coexist-handoff-2026-10-27.md`。
新包构建失败未被改写成 PASS；板上连续作业、手动按钮与 CSV 仍未验收，BOARD 保持 UNVERIFIED。
理解门槛 3 题未作答，不记“已通过”。

## 6. 经验沉淀

- 触发条件：把采集、推理、服务接入同一块 PYNQ，且 PS/PL 跨域并发启动。
- 排查步骤：先固定 CDC 的稳定余量与索引提交时序，再修固件配置缓存；启动用依赖而不是 sleep；
  包必须绑定 HWH 拓扑，构建失败保持失败。
- 适用范围：所有 PYNQ LIVE 集成；换视频源/PL 拓扑需重定时钟与包绑定。
#skill候选
