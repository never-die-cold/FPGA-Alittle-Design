# 2026-10-08 协作记录：EXE 轮次叠加的两处状态机缺口与一个被弱测试放过的真 bug

> 标签：#vision #bug修复 #skill候选
> 平台：ZCode ｜ 模型：GLM-5.3-Flash
> 相关 commit：dev/exe c037273（bbox 对齐）；本批（rounds.py + test_vision_rounds）

## 1. 任务与初始提示词

用户指示"继续工作、继续写"——前端线下一步：把轮次状态机从 preview.py 抽离为可离线测试的
rounds.py（不依赖 cv2），并写覆盖 D3/D5 语义的测试（触发节流/超龄/配置变化/断联/会话恢复），
作为 M3"撤框/断联/过期用例测试记录"的离板地基；同时按用户指示先把 bbox 端点语义对齐
半开区间（对齐 docs/outsource/localization-requirements.md L2）。

## 2. 模型第一版方案

按既有 D2/D3/D5 语义直接抽离 RemoteRounds + 写 6 场景测试；bbox 校验从 `0<=x0<=x1<w`
改为 `0<=x0<x1<=w`（半开区间），画框右下取 x1-1/y1-1。

## 3. 失败现象（三轮）

- 轮 1：rounds 测试首跑即炸——`TypeError: 'NoneType' object is not subscriptable`；
  前一行 WARN：`check failed (1/3): HTTP Error 404: Not Found`。
- 轮 2（设计审查）：连续失败达限触发 `handshake()` 时若服务仍不可用，异常外泄 → EXE 崩溃
  （板卡重载/服务重启窗口期必现）。
- 轮 3（设计审查）：服务重启=新会话，但恢复后的成功请求会把 `fails` 清零，重握手永不触发
  → EXE 永久 WAITING（违反 D5"检测到 session 变化即清空本地状态并重握手"）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 404 + NoneType | `http_json` 以"有无 body"区分 GET/POST，`poll` 调 `/v1/check` 未传 body → 实发 GET → mock 仅注册 POST → 404；**端点模式叠框从未生效**（步骤 B 的打包测试只验"跑通+出图"未验画面内容，放过此 bug） | `poll` 改传空 JSON 对象 `{}`；`test_vision_client.py` 补"绿色目标框像素>500"内容断言 | ✅ 测试通过；重建 EXE 内容断言通过 |
| 2 | （设计推演）重握手无异常保护 | 恢复动作自身失败会成为崩溃点 | 新增 `rehandshake()` 收口 `(URLError,OSError,KeyError,ValueError)`，失败仅告警保持 WAITING | ✅ 断联段测试通过（WARN: re-handshake failed 后继续运行） |
| 3 | （设计推演）重启后永久 WAITING | 成功请求清零 fails → 不再重握手 → session 永不更新 | `poll` 检测 `packet.session_id != self.session` 立即 `rehandshake()`，本轮不采纳报文 | ✅ 恢复段测试通过（WARN: session changed → 下轮 ROUND 恢复叠加） |

## 5. 最终结论

`src/vision_client/rounds.py`（纯 stdlib 状态机：D2 触发节流 / D3 撤框六条件 / D5 会话重连）
+ `sim/vision/test_vision_rounds.py`（6 场景，接入 `run_vision_python.sh`）+ 打包内容断言。
Python 回归 6/6、EXE 重建三关全 PASS；证据 `data/logs/2026-10-08-exe-rounds/`。

## 6. 经验沉淀

#skill候选
- 触发条件：① "跑通即通过"的弱测试放过功能完全失效的 bug（测试要断言输出的**可观测特征**——如画面像素统计——而非仅退出码/产物存在）；② 网络客户端把 GET/POST 决定藏在"有无 body"里，空 body 动作会静默退化为 GET；③ 失败恢复路径（重握手）自身也要有失败处理，否则恢复逻辑成为新的崩溃点；④ 状态机在"远端换了身份"（新会话）时的自愈条件必须显式编码，不能依赖计数器（fails）间接推断。
- 排查步骤：联调测试加内容断言 → 对每个恢复路径问"如果恢复动作自己也失败呢" → 对每个会话/身份标识问"它变化时谁负责触发重建"。
- 适用范围：换题换板成立（上位机/联调脚本通用范式）。
