# EXE 环接通：PC↔PYNQ 网络上 LIVE 服务全链（2026-10-17）

> 板子重启后（boot_id 更新、sudo 失效、PL 空），owner 授权代工全链。今天把 **PS→EXE 环**
> 在真实网络上接通：板端 park 采集后端 + numpy CNN 引擎装进 EXE 分支的 W05 LIVE 服务骨架，
> PC 经 192.168.50.0/24 直连消费 v1.2 LIVE 包。

## 网络层（先决条件）

- 板子重启后 eth0 = UP/LOWER_UP，@reboot cron 配好 169.254.87.99/16 + 192.168.2.99/24，
  但与 PC（"以太网"=192.168.50.1/24，原树莓派段）不同网段；PC 上 4 个 link-local 接口
  干扰路由，tun0（sing-tun）由用户关闭。
- 解法：板端 `ip addr add 192.168.50.99/24 dev eth0`（sudo，owner 已重认证）→
  PC ping 192.168.50.99 **0% 丢包 / 0ms**。SSH 通道未再用（file 全走 UART 传）。

## 服务部署（板上零 torch）

- 复用 10-15 EXE 快照的 `vision_live_service.py`（W05 骨架，/v1/status /v1/check /v1/config
  /v1/latest 端点不变）+ `vision_mock_service.py` + `vision_protocol.py`，UART 上传至
  试验目录 `c01-8b702ebb0b284fa3a408491e13e644e3/`（昨天 park 链全部文件已在此）。
- 新增 `inputs/park_live_server.py`（v1→v7 七版迭代，全部原始日志留档）：
  - `ParkCaptures` 后端（backend=PARK，prototype=True）：每轮 flock 采集锁→确保候选位流
    （已载则跳过下载）→等一个真实帧 tick→park 保护复制→capture.png+sha256 落盘→
    有界恢复原 vision（用户显示器在轮次间保持正常画面）。
  - numpy 引擎：golden locate → crop_resize 64×64 → 折叠 FP32 NumPy CNN →
    inspection_rules 语义 judge；C04 §2.2 超限映射（>16 目标截断+counts=None+
    reasons 保持 RECHECK）；v1.2 目标字段严格四元组（touches_border 只进 reasons）。
  - pynq 在 HTTP 线程需要 `asyncio.set_event_loop(new)`（v3 踩坑）；`allocate` 导入
    （v4）；faulthandler 周期线程栈转储（v6 起）。
- 启动：`sudo nohup python3 -u park_live_server_v7.py --host 0.0.0.0 --port 8765
  --root ~/vision_m2/live-artifacts --order 2 2 2 --min-score 0.8`。
  运维注意：`pkill -f` 会自匹配远端 shell（两次 SIGTERM 教训），用字符类 `serve[r]_vN`。

## 联调结果（PC PowerShell 直连）

| 端点 | 结果 |
|---|---|
| GET /v1/status | `{"mode":"LIVE","backend":"PARK","prototype":true,"hardware_connected":true}` |
| POST /v1/check | **121.6 s 全轮**，合法 v1.2 包：16 目标带 class/score（threshold 边缘场景，14 bolt/2 nut），decision RECHECK（reasons=[target_limit, touches_border]，actual/delta/missing/extra 完整），prototype=true，frame_id=1 |
| 第二轮 | 后台复跑中（check-round2.txt） |

轮次耗时构成：候选下载+锁定 ~20-40 s + 保护复制 ~0.2 s + 恢复 vision ~15 s +
locate ~12 s + 16 目标 numpy CNN ~60-90 s。**EXE 的 REQUEST_TIMEOUT 原为 2 s
（FILE 后端即时引擎口径），已改为 300 s 并注明 owner 授权的过渡语义**
（`src/vision_client/rounds.py`，C03 硬件 CNN 替代后回收）。

## EXE 代工验收入口（owner 执行）

```powershell
# GUI 从源码跑（免重打包；--source 1 = USB 采集卡）
C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe src/vision_client/preview.py --source 1 --endpoint http://192.168.50.99:8765
```

预期：UVC 实时画面 + 每轮（~2 min）叠加 LIVE 包的框/标签/判定；判定 RECHECK 属实
（场景未构图 + 目标触边 + 超限），诚实链路证据。

## 边界

- prototype=true：park 采集链未走正式 N03 盖章（owner 授权代评审已做，正式验收另计）。
- 轮次 2 分钟级：板上 numpy CNN 是过渡路径，C03 硬件 CNN（J02）才是正路。
- 场景未构图（全触边/超限）——RECHECK 是 golden 定位器的诚实输出。
