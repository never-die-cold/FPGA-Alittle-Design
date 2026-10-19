# M2 Windows 视频预览和结果接口原型

`preview.py` 显示 UVC 采集卡视频，或明确标为 `MOCK ONLY` 的模拟图。
已有 LIVE 类别/分数/工单判定展示、批次与 CSV、文件回放；分类/工单结果来自报文或文件，前端不执行硬件推理。
UVC-only 显示 `VIDEO ONLY | UNASSOCIATED`；配置 endpoint 后按轮次与年龄窗叠加结果，不代表逐帧精确关联。真实硬件 LIVE 和最终发布验收仍未完成。

## 离板构建与复验

Windows PowerShell，仓库根目录：

```powershell
# pwsh 7 未安装时用 Windows PowerShell 5.1（脚本兼容）；-ExecutionPolicy Bypass 仅对本次调用放行。
# python 命令若被微软商店占位 stub 占用（where python 指向 WindowsApps），用 py 启动器指向真实解释器。
powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1 -Python py
sim/build/vision-client/dist/vision_preview/vision_preview.exe --selftest
sim/build/vision-client/dist/vision_preview/vision_preview.exe --mock
```

脚本将固定依赖装在仓库内 `sim/build/vision-client-deps`，生成包含 `_internal` 的完整目录。
分发时复制整个 `dist/vision_preview/`，不能只复制 exe。构建自动执行 EXE 自测及本地 HTTP 联调。
不连接采集卡的可复现实验：

```powershell
python src/pynq_host/vision_mock_service.py
sim/build/vision-client/dist/vision_preview/vision_preview.exe --mock --endpoint http://127.0.0.1:8765
```

采集卡接入后的验收入口为 `vision_preview.exe --source 0`，按 q 或 Esc 退出。按 `c` 手动触发
一轮检查（0.3s 防抖）；配 `--records-dir` 时该轮**有效**结果落批次记录（D8–D10）。
设备索引需现场确认。10/03 与后续现场记录已有真实采集卡画面证据；完整目标电脑/设备兼容与发布复验仍待完成，不能推为所有 UVC 设备已验证。

批次记录（M3 起步，契约见决策单 D8–D10；**W07 起 schema v2**）：`--records-dir <目录>` 开启。
只有手动触发的有效轮次记录——自动间隔轮次永不记录，结构性满足"重复帧不增加批次计数"；
记录键 `(session_id, check_id)` 去重（**跨进程生效**：启动时从既有 records.jsonl 重建键与计数，
损坏行大声失败；异常事件截图序号同样续编）；产物为 `records.jsonl`（一行一条：mode/session/check/
config/frame/时间/结果年龄/目标数/boxes/**status**/**decision 原样**（当轮工单即
decision.expected）/**prototype**/protocol_version/截图名）+ `screenshots/` 逐条 PNG。
**截图前缀标来源（C04 §3.2/Q2）：MOCK=`mock_`、LIVE+prototype=`proto_`、真实 LIVE 无前缀——
三者不得互换使用**；MOCK/PROTOTYPE 不得用作板上识别证据。真实 LIVE 记录仍需对应原帧、硬件版本和实测证据，文件名前缀不能单独证明来源。
目录包含 `records.csv` 时即为完整导出件；**CSV 导出**：`py src/vision_client/export_records.py <记录目录>`
（UTF-8-BOM，Excel 直接打开不乱码；v2 增 status/missing/extra/prototype 列，v1 旧记录兼容；
targets 列保留 JSON）。离线测试：
`py sim/vision/test_vision_records.py`、`py sim/vision/test_vision_export.py`。

去重集合启动时从既有 records.jsonl 重建（**2026-10-13 起跨进程生效**，损坏行大声失败）。服务 HTTP 重试每次新建 check_id——重试语义草案见 [C04 §2.4](../../docs/contracts/vision-live-semantics.md)（待 NC/JL 确认）；记录键去重不用于证明请求重试幂等。
快照读取与哈希核对：`py src/pynq_host/round_artifacts.py <root> <session_id> <check_id>`（packet 绑定 + capture 字节哈希 + 引擎源哈希；不符大声失败；旧轮次无 `capture.sha256` 按缺件拒绝）。

异常事件日志（D11）：状态迁移（断联/超期/配置变化/恢复 ok）与会话变化、重握手失败写入
同目录 `anomalies.jsonl`（一行一事件，含 prev/check_id/fails）+ `screenshots/anomaly_*.png`。
`--trigger-frame N` 为联调自检入口：在第 N 帧模拟一次手动触发（等效按 `c`），
供打包测试覆盖"手动触发→落批次记录"全路径。

轮次叠加模式（契约见 [docs/vision-sync-protocol-decisions.md](../../docs/contracts/vision-sync-protocol-decisions.md)）：
`--source 0 --endpoint http://<host>:8765` —— 采集卡视频 + 结果服务轮次叠加。启动握手失败立即
退出；每 `--interval`（默认 0.5s，启动校验必须小于 `--max-age`，否则每轮结果在下轮触发前过期、
画面周期性空窗）触发一轮 `POST /v1/check`；结果按 D3 判据（会话 + 配置号 + 年龄窗 `--max-age`
默认 1.0s，**年龄按 EXE 接收时刻计量、与服务端时钟无关**）有效才叠框，过期/断联撤框显示
WAITING；连续 3 次 HTTP 失败自动重新握手（D5）。界面为 **HUD v4「EdgeSight 应用外壳」**
（定稿与说明 [data/logs/2026-10-09-exe-hud-v4/](../../data/logs/2026-10-09-exe-hud-v4/README.md)）：
1600×900 画布 = 顶栏（运行状态徽标 / 状态 / 分辨率·FPS·session / 时钟）+ 视频圆角视口
（比例 0.9875）+ 右上三格指标面板（ROUND / TARGETS / REC + `FRESHNESS` 内嵌条）+ 右列
`DETECTED OBJECTS` 列表（缩略图 / T 序号 / XYWH 坐标）+ `RUN INSPECTION` 按钮
（**鼠标可点击**，与 `c` 键等效触发）。**UVC-only 模式隐藏面板与按钮**；REC 常驻计数
（`--records-dir`，手动触发成功记录一条即 +1 并保持）。文本由 Pillow 真实字体（Inter，OFL）
渲染，随 EXE 打包（含中文：Noto Sans SC 子集，GB2312 全集，OFL——类别名/判定文案可直接用）；
启动时声明 DPI 感知并按屏幕工作区等比缩放（200% 缩放屏实测 1.8×），
高分屏下不被系统拉伸切割。

**LIVE 显示（W06，C04 §3.2）**：`mode=LIVE` 轮次显示判定横幅（CHECK_PASS 绿 / CHECK_FAIL 红 /
RECHECK 琥珀，附 `-washerx1` 式缺多摘要）、TARGETS 格显示「实际/工单」、对象列表逐行显示
类别与分数（`class=null` → unclassified）；报文带 `prototype=true` 时顶栏恒显红色
`PROTOTYPE` 徽标（离线产物代实时结果，不可关闭）。判定横幅文本与差额由 `rounds.live_view`
纯函数生成（离板可测）。LIVE 联调替身：`python src/pynq_host/vision_mock_service.py --live`
（v1.2 LIVE 报文、prototype 恒 true、场景循环 PASS/FAIL/RECHECK；合成数据，不代表板上识别）。

状态机（`rounds.py`，纯 stdlib）与取帧渲染解耦：preview.py 只负责取帧与画框。
10/15 起 HTTP 轮询及自动重握手在单个后台线程中执行，GUI 逐帧采纳结果快照；
网络等待期间可继续预览，结果按原接收时间规则过期撤框。手动轮次携独立 `trigger_ref`，
FILE 原型服务据此保留该轮完整产物；实际 UVC 帧率与板端联调仍待实测。
离线测试 `py sim/vision/test_vision_rounds.py` 覆盖触发节流、超龄/配置变化/断联撤框、
服务重启（新会话）自动恢复，已接入 `sim/scripts/run_vision_python.sh` 全量。

## 离线文件回放（2026-10-10）

新增 `--replay <result.json>`，读取经过哈希检查的 FILE_REPLAY 快照，显示目标框、
原型类别/分数和三类“实际 / 工单”数量；状态为 OFFLINE FILE，不访问相机或网络。
它与 `--mock`、`--endpoint`、`--records-dir`、`--selftest`、`--trigger-frame` 互斥，
不生成新的联网批次。Python 与打包 EXE 都已通过离板回放测试。

```powershell
python src/vision_client/preview.py --replay data/evidence/2026-10-10-offline-inspection/runs/synthetic-001/result.json
# 打包后也可使用 --replay；--headless --save <PNG> 可导出检查画面。
```

完整生成步骤和限制见[离板检查说明](../../docs/runbooks/offline-inspection.md)。

## 模拟接口 v1

- GET `/v1/status`：mode=MOCK、session_id、hardware_connected=false。
- GET `/v1/latest`：版本、session_id、frame_id、config_id、原图宽高、UTC Unix 时间戳、
  status=LOCATION_ONLY、目标序号和原图 bbox `[x0,y0,x1,y1]`——半开区间语义 `[x0,x1)×[y0,y1)`，
  宽=x1-x0、右下端点可恰为 w/h（对齐定位外包需求 L2）；最多16目标。
- POST `/v1/config`：JSON `{"control":3}`，只允许低四位；返回模拟 applied_config_id。
- POST `/v1/check`（v1.1 新增）：触发一轮检查；body 可选 `{"trigger_ref":"..."}`（未知字段 400，
  空 body 合法），返回带自增 check_id 的定位报文并回显 trigger_ref（D2）。`/v1/latest` 保留为
  调试拉取口（帧号随轮询推进，携带当前 check_id）。
- 不认识的路径404；错误 JSON/参数400。服务默认仅绑定127.0.0.1，且不访问 MMIO。

`vision_protocol.py` 验证类型、坐标、编号和状态。结果有效性按 D3 = 会话 + 配置号 + 年龄窗
（frame_id 只透传展示、不参与匹配——EXE 无法把结果帧号对应到采集卡画面）；复位/重连需要新会话。
FILE/LIVE 服务骨架已实现；这里的立即确认仍只模拟 API 形态，真实 PS 配置必须用 `VisionRegs.commit()`
等待 R12 生效（NC 负责，见决策单 D7）。
