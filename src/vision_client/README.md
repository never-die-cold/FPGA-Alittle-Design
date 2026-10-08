# M2 Windows 视频预览和结果接口原型

`preview.py` 显示 UVC 采集卡视频，或明确标为 `MOCK ONLY` 的模拟图。
原型没有 CNN 分类、工单判定、批次数量或真实板卡结果。实际视频显示 `VIDEO ONLY | UNASSOCIATED`；
不能凭两台设备的帧率相同就把网口框叠到采集卡画面上。

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

采集卡接入后的验收入口为 `vision_preview.exe --source 0`，按 q 或 Esc 退出，按 c 立即触发一轮检查。
设备索引需现场确认。当前没有验证实际 UVC 格式、驱动与目标电脑兼容性。

轮次叠加模式（契约见 [docs/vision-sync-protocol-decisions.md](../../docs/vision-sync-protocol-decisions.md)）：
`--source 0 --endpoint http://<host>:8765` —— 采集卡视频 + 结果服务轮次叠加。启动握手失败立即
退出；每 `--interval`（默认 0.5s，启动校验必须小于 `--max-age`，否则每轮结果在下轮触发前过期、
画面周期性空窗）触发一轮 `POST /v1/check`；结果按 D3 判据（会话 + 配置号 + 年龄窗 `--max-age`
默认 1.0s）有效才叠框，过期/断联撤框显示 WAITING；连续 3 次 HTTP 失败自动重新握手（D5）。
横幅常显 `MOCK ONLY | ROUND n | age | targets`。

状态机（`rounds.py`，纯 stdlib）与取帧渲染解耦：preview.py 只负责取帧与画框。
离线测试 `py sim/vision/test_vision_rounds.py` 覆盖触发节流、超龄/配置变化/断联撤框、
服务重启（新会话）自动恢复，已接入 `sim/scripts/run_vision_python.sh` 全量。

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
设备服务尚未实现，这里的立即确认只模拟 API 形态，真实 PS 配置仍必须用 `VisionRegs.commit()`
等待 R12 生效（NC 负责，见决策单 D7）。
