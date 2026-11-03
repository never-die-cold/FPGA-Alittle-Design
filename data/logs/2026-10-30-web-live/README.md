# 2026-10-30 网页端真实链路联调

时间：2026-10-30 晚至 10-31 凌晨（Asia/Shanghai）。源码基线 `ffe0769` 加本次未提交的网页/API 改动，无 RTL 修改；用户授权直接开始上板后网页调试，并授权本机页面使用 USB 采集卡。

## 入口与部署

PC：`python src/web_client/serve.py --endpoint http://192.168.50.99:8765`，浏览器打开 <http://127.0.0.1:8000>。选择 USB Video (345f:2109)，连接后为 1280×720、约 30 FPS。服务仅绑定本机。

板端使用 `/usr/local/share/pynq-venv/bin/python3`，r6 包 `/home/xilinx/cop-pkg-r6-multitarget-20261028-r1`；首次使用原应用 `/home/xilinx/cop-app-r6-20261028`。快照接口部署在独立副本 `/home/xilinx/cop-app-web-20261030`，仅替换为当前 `vision_live_service.py` 和配套 `vision_protocol.py`，原应用保留。

产品服务参数为 `--order 3,3,3 --background-mode local --color-threshold 25 --min-score .8`。最终运行根目录 `/home/xilinx/cop-live-web-20261030-r4`；其 `service.pid`、`service.log` 和会话子目录保存在板上。按原有 `cop_product_service.py --package ... --root <新目录>` 入口启动即可重载包，须先停止已有同一服务、确认端口空闲。未修改系统自启动。

## 实际结果

- 初始 SSH 可达，但 8765 没有服务。第一次启动因相机尚未给出帧而超时；用户确认视频就绪后启动成功。
- 本机 HTTP 返回真实 LIVE / C01 / COP_HW / prototype=false，会话和配置由板端确认。修复 Windows `.mjs` 的 text/plain MIME，浏览器模块得以执行。
- 第一轮报文 `packet.json` 与原帧 `capture.png` 原样取自 `/home/xilinx/cop-live-web-20261030-r1/a3481095/check-000001/`。PNG 用于核对本轮画面与框，不能由合成场景替代。图中视觉复核为 4 螺栓、1 螺母、1 垫圈；模型输出 4/2/0，均低分，工单为 3/3/3，结论 RECHECK/low_score，未调低阈值。
- 新应用首次启动发现旧协议模块缺少 parse_trigger_ref；补齐同版本协议模块后恢复。
- r3 会话 `4880f425-3c08-4ae3-b565-3a3fb2eb2b75` 前 4 轮成功返回，第 5 轮出现 TASK_ERROR（status=0x1069，error_code=1），随后第 6–8 轮 MM2S DMA 超时。`hardware-error.json` 原样取自该会话 `check-000005/cop_trace.json`。网页撤除旧判定，失败轮次不记批次。原因未定位，不能记为已修复。
- 重载包并启动 r4 后，会话为 `31f0ef12-6eed-4c12-92a7-a9f44b2a7bf0`。手动 check 1、自动 check 2/3、手动 check 4 均返回真实 RECHECK 和 6 个目标；ROUND=4、REC=2。CSV 实际解析为 2 行，check_id=1/4、同一会话、UTF-8 BOM=true；自动轮没有记录。最终自动检查暂停。
- UVC 预览与板端快照均可显示。结果在接收后 4.5 秒过期，撤除框和数量；快照按完整会话号及 check_id 读取，跨会话/缺失轮次返回 404。
- 视觉复核发现原视口 max-height 会压坏 16:9 比例并产生留边，已移除此上限；坐标映射按报文宽高计算。

## 仓库内验证

```powershell
python sim/vision/test_web_server.py
node --test sim/vision/test_web_protocol.mjs
python sim/vision/test_vision_live_service.py
```

HTTP 3 项、报文解析 4 项通过；现有 LIVE 服务测试验证本轮快照字节、跨会话拒绝与缺图 404。`bash sim/scripts/run_vision_python.sh` 现有 19 组全部通过，VISION_EXIT=0。原始输出和浏览器截图、导出的 CSV 位于本机忽略目录 `sim/build/web-debug-20261030/`。启动、视频与手动检查按网页端 README 复现。

最终视口比例修正后，浏览器拒绝继续操作授权，因此该 CSS 修正尚未刷新复核；已保存的实板叠框截图为修正前状态。未绕过该授权限制。

未完成：TASK_ERROR 与后续 DMA 超时的根因/恢复、连续稳定性、分类精度、网页工单下发、持久批次/异常截图、逐帧精确关联及工业整机验收。当前工作仅完成网页链路首轮联调，不能作为上述验收通过。
