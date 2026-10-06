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

采集卡接入后的验收入口为 `vision_preview.exe --source 0`，按 q 或 Esc 退出。
设备索引需现场确认。当前没有验证实际 UVC 格式、驱动与目标电脑兼容性。

## 模拟接口 v1

- GET `/v1/status`：mode=MOCK、session_id、hardware_connected=false。
- GET `/v1/latest`：版本、session_id、frame_id、config_id、原图宽高、UTC Unix 时间戳、
  status=LOCATION_ONLY、目标序号和原图闭区间 bbox `[x0,y0,x1,y1]`；最多16目标。
- POST `/v1/config`：JSON `{"control":3}`，只允许低四位；返回模拟 applied_config_id。
- 不认识的路径404；错误 JSON/参数400。服务默认仅绑定127.0.0.1，且不访问 MMIO。

`vision_protocol.py` 验证类型、坐标、编号和状态。帧关联必须同时匹配会话、帧号、配置号，
并检查过期时间；复位/重连需要新会话。设备服务尚未实现，这里的立即确认只模拟 API 形态，
真实 PS 配置仍必须用 `VisionRegs.commit()` 等待 R12 生效。
