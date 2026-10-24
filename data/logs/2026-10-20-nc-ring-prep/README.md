# NC ring / EXE 离板交接卡

- 日期/执行人：2026-10-20，nc_ring_exe agent；仅离板静态核查。
- 版本：dev/riscv@5f8abe25906d918f15809c888a7d3c1182aa3e08；开工 git status 干净。
- 命令：读取 workflow、计划/契约、客户端 README/rounds/preview、历史 ring 脚本；Get-FileHash；ZIP 只读目录检查。
- 结果：找到源码启动、协议字段和历史板端服务入口；本 agent 未启动服务、未运行 GUI/HTTP、未访问板卡；本轮 ring/EXE 均未验收。
- 产物：本操作卡；引用原文件，不复制源码快照。
- 边界：历史为 PARK 采集+PS NumPy CNN，prototype=true；不是 CNN 硬件输出。实际板端状态由主控独占核查。

## 先看两个缺口

1. `sim/build/` 本地静态扫描没有找到 `vision_preview.exe`（21:14 快照）。历史 `data/logs/2026-10-15-onboard-n02-n03/exe-ffb7ab2.zip` 是源码快照，ZIP 内没有 `.exe`，不能作为可运行 EXE 交付。
2. 历史安装过 `/etc/cron.d/pynq-live`，冷启动可能自动启动 PARK 服务。主控已另行实测 PID669 的 v7 服务监听8765；本卡不复核该结果。N02/恢复 vision 前须由主控协调服务与 overlay，其他 agent 不可另启采集。

## 三处易误判

1. EXE 启动即再握手（`/v1/config` 令 `config_id+1`，`vision_live_service.py:222`）并自触发轮次：画面是更晚的 `check_id`，与 `check.json` 不同轮，非异常。
2. EXE 自动轮询独占单通道（`rounds.py:244`）：手动 `c` 排在下一次请求后，REC+1 可能等两轮，勿连按。
3. 三处 `Invoke-WebRequest` 先接 `$r` 再写 `$r.Content`，并把 `$r.StatusCode` 与 UTC 起止记入 `http-log.tsv`。

## NC 实网执行顺序（仅主控执行）

先完成 N01/N02，确认服务无在途任务、板端恢复安全、网络及 UVC 索引已实查。
历史地址是 `http://192.168.50.99:8765`；当前主控也已确认该板端地址。
禁止同时运行 EXE 自动检查与另一个手动 POST，避免两轮争用板卡。

仓库根目录 PowerShell；先创建本轮独立证据目录。以下是待执行命令，不是本 agent 测试结果：

```powershell
$ringOut='data/logs/2026-10-20-nc-board/ring'
New-Item -ItemType Directory -Force $ringOut | Out-Null
$ringBase='http://192.168.50.99:8765'
(Invoke-WebRequest -UseBasicParsing "$ringBase/v1/status" -TimeoutSec 10).Content | Set-Content -Encoding UTF8 "$ringOut/status.json"
$ringWatch=[Diagnostics.Stopwatch]::StartNew()
(Invoke-WebRequest -UseBasicParsing "$ringBase/v1/check" -Method Post -Body '{}' -ContentType 'application/json' -TimeoutSec 600).Content | Set-Content -Encoding UTF8 "$ringOut/check.json"
$ringWatch.Stop()
$ringWatch.Elapsed.TotalSeconds | Set-Content "$ringOut/check-seconds.txt"
(Invoke-WebRequest -UseBasicParsing "$ringBase/v1/latest" -TimeoutSec 10).Content | Set-Content -Encoding UTF8 "$ringOut/latest.json"
```

HTTP 非成功响应须另留状态码/原始错误；超时不能当任务已结束，不可立即发第二次 check 或重载 overlay。
这里保存响应正文原文，不能用 ConvertTo-Json 后的内容冒充原样报文；另记 HTTP 状态码及开始/结束时间。
既有历史脚本位置为 `data/logs/2026-10-17-exe-ring/inputs/test_park_live.ps1`，其注释里的 `sim/scripts/test_park_live.ps1` 路径已经不适用；脚本本身会重新序列化 JSON，且没有 latest 步骤。

HTTP 轮次完成后再启动客户端。现场确认采集卡索引，下面 `1` 只是历史值：

```powershell
python src/vision_client/preview.py --source 1 --endpoint http://192.168.50.99:8765 --records-dir data/logs/2026-10-20-nc-board/ring/records
```

点击 RUN INSPECTION 或按 c，等待有效手动轮次使 REC 加一；q/Esc 退出。源码界面截图只能记源码验收，不能称为打包 EXE 验收。
真正 EXE 构建入口为 `powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1 -Python py`；该入口会安装固定依赖、写共享 sim/build、执行打包自测/HTTP联调，因此由主控另行排他执行，本 agent 未运行。
生成后完整分发 `sim/build/vision-client/dist/vision_preview/`（含 `_internal`）；将上面 python+脚本替换为该目录的 vision_preview.exe，其余参数相同。

## 对账与截图

- status 的 mode/session_id/backend/prototype/hardware_connected；check 的 session_id/check_id/config_id/frame_id、trigger_ref（手动轮）、targets 与 decision 原文；latest 应对同轮核查。服务若推进了轮次要明确记差异。
- EXE 会握手并 POST config(control=0)，expected_config 取 applied_config_id；按会话+配置号+接收后年龄判有效，不保证采集卡逐帧精确关联。
- 保存框、标签、判定、PROTOTYPE、轮次与 REC 可见截图；记录所用 exe/源码 SHA、UVC模式、网络地址及版本。
- `records.jsonl` 与 `screenshots/proto_*.png` 对应手动有效轮次；只自动轮询不会增加批次。导出：`python src/vision_client/export_records.py data/logs/2026-10-20-nc-board/ring/records`。
- 原始 capture/结果产物在板端 live-artifacts；按 session/check 找对应目录并核对像素哈希及 capture 关联。保存服务日志与HTTP/EXE分段耗时。RECHECK 如实保留。
- 当前源码 HTTP 超时300s，历史板端单轮约94–122s；结果默认1s超龄即撤框，两分钟轮次间显示WAITING属当前语义。不要修改年龄窗来掩盖旧结果。

## 停止、恢复与 WC 无网口的分工

主控先退出客户端，确认服务没有在途采集；记录确切 PID 后再停止指定服务，禁止复制历史宽泛 pkill/rm 命令。历史服务会切换位流，恢复期间不能再触发请求。
随后按现有 vision runbook 恢复 `/home/xilinx/vision_m2/m2_onboard.py load` 与 `smoke`（需正确 PYNQ 环境和 sudo），再检查 UVC。若 UNSAFE-STOP 或串口超时，先按对应恢复规程处置，不能直接杀进程/重载。
WC 不需要网口即可检查界面、批次、CSV、离线回放及 localhost 模拟服务：一个终端 `python src/pynq_host/vision_mock_service.py --live`，另一个终端 `python src/vision_client/preview.py --mock --endpoint http://127.0.0.1:8765 --records-dir data/logs/2026-10-20-wc-local/records`。
WC 的这些结果必须标合成/PROTOTYPE，不证明 UVC兼容、板端网络、PARK采集或硬件推理；这些由 NC 的唯一实机链验证。

## 后续第一动作

主控先完成 N02 的独占板窗口并确认服务处理状态，再决定构建 EXE 或先用源码做实网一轮；真正 EXE 截图与本轮 ring 原始证据仍未完成。
