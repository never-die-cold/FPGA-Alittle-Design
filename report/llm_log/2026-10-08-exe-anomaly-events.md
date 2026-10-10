# 2026-10-08 协作记录：异常事件日志（D11）——把状态机迁移变成可导出的证据

> 标签：#vision #架构决策
> 平台：ZCode ｜ 模型：GLM-5.3-Flash
> 相关 commit：dev/exe 本批（rounds events 队列 + records.AnomalyLog + preview 落盘）

## 1. 任务与初始提示词

用户按既定顺序推进第 ② 项：异常事件/异常截图日志（M3 验收："断联/过期结果均有测试记录"；
plan.md §1.3："异常截图和记录导出"）。决策单 D9 已预留"异常事件与异常截图独立于批次"。

## 2. 模型第一版方案

- 状态判定分解：`RemoteRounds._state(now)` 返回 no_result/outage/session/config/stale/offline/ok
  （D3 判定从"布尔组合"拆成"带原因的状态"，布尔语义保持等价）。
- 事件队列：overlay 每次调用检测状态迁移，迁移时向 `events` 队列 push
  （kind=overlay_*、prev、check_id、fails）；poll 的会话变化与 rehandshake 失败各 push 一条。
- 落盘：`records.AnomalyLog`（与 BatchRecords 同模式：注入截图回调、追加 jsonl、
  MOCK 前缀），preview 每帧 `drain_events()` 落盘并附当前帧截图。
- 迁移驱动 = 天然边沿触发（只在状态变化时记录），断联 10 秒只产生"进入 outage + 恢复 ok"
  两条，不会逐帧刷屏。

## 3. 失败现象

本批无运行期失败；设计上拦下一个隐患：handshake() 里若清空 events 队列，
会丢掉 poll 在重握手前刚 push 的 session_changed 事件——改为**只有 init 建空队列，
handshake 只重置状态基线（last_state），不动事件队列**。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 设计推演：重握手前 push 的 session_changed 会被 handshake 清掉 | 队列清理时机与 push 时机冲突 | handshake 不清 events，只重置 last_state | ✅ test_vision_rounds 断言事件集合包含 session_changed 与 rehandshake_failed |

## 5. 最终结论

D11 落地：anomalies.jsonl + anomaly_*.png（含恢复 ok 事件，形成完整时间线）；
打包 E2E 断言 anomalies.jsonl 存在。回归 7/7 + 重建三关 PASS。

## 6. 经验沉淀

- 触发条件：需要给"偶发异常"留验收证据（断联/超时/过期），且要求证据可导出。
- 排查步骤：状态机输出"带原因的状态码"而非布尔 → 在状态迁移沿上记事件（边沿触发，防刷屏）
  → 事件走队列由上层落盘（状态机保持不碰文件、离线可测）。
- 适用范围：换题换板成立（长跑系统的事件留痕通用分层）。
