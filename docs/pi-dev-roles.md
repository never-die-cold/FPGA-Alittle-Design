# 树莓派 4B：开发期角色与红线（pi-dev-roles）

> 生效：2026-10-03 方案批准（纪要随 llm_log 归档）。本文只管 Pi 的**开发/联调期**角色。
> 硬边界依据：[plan.md](../plan.md) §1.3 / M3 验收行、[采集规程](fastener-data-collection-protocol.md) §1、[hardware.md](../board/hardware.md) §3.7。

## §1 红线（先读这个）

1. **Pi 不进产品分析路径**：预处理/定位/CNN 推理/工单检查全部在 PYNQ（PL+PS+RISC-V）。Pi 算出的任何结果不得进入验收证据或交付叙事。
2. **Pi 不产生数据集像素**：数据集帧一律经 PYNQ `hdmi_in.readframe()` 采集（数据集像素=部署像素），Pi 侧存图禁止。
3. **供电与上电顺序**：Pi 用专用 5V/3A USB-C 电源；**禁止从 PYNQ USB host 口取电**；上电顺序 PYNQ 先（PL EDID 就绪）→ Pi 后（hardware.md §3.7）。
4. **mock/回放结果标注「非板上识别」**：仅供界面联调与链路验收动作，不替代真实识别验收（plan.md §3.4）。
5. **系统配置只落在项目专用 microSD**（另配，Raspberry Pi OS Lite 32-bit，SSH 开启）；HDMI 输出锁 720p60（`config.txt` 设 `hdmi_group=1`/`hdmi_mode=4`）。

## §2 角色清单

| 角色 | 内容 | 前置 | 产出 |
|:---|:---|:---|:---|
| R1 交叉基准 | arm_localize 便携包在 Pi（Cortex-A72）跑分，与 Zynq A9 / PC 三方对照 | Pi 可 SSH（现在即可） | 三方耗时表入档，支撑 10/5「定位必须 PL 加速」拍板 |
| R2 mock 服务宿主 | `vision_mock_service.py --host 0.0.0.0` 挂 Pi，EXE 远程联调 | Pi 可 SSH | EXE 联调不占 PC/板卡；联调日志存证 |
| R3 回放源 | 循环播放合成场景 → HDMI → PYNQ IN：换源/EDID/断连测试 + M3 重复帧/缺件/多余件验收动作 | **micro-HDMI→HDMI-A 线到货** | 素材生成器 `sim/scripts/make_replay_scene.py` + 实测记录 |
| R4 正式演示源 | CM3 相机 → Pi → PYNQ（原定角色，hardware.md §1 链路） | 线 + CM3 到货 | 验线（hardware.md §4）→ 采集规程 §2 机位定标 |

## §3 R1 交叉基准 runbook

```bash
# PC 组包（SHA256 对照 data/evidence/2026-10-03-arm-localize-baseline/final-package-manifest.json）
python sim/scripts/make_arm_localize_pkg.py
# 上 Pi（<pi> 为 IP；包内含 manifest 自检）
scp sim/build/arm-localize-package.tar.gz <user>@<pi>:~/
ssh <user>@<pi> "tar -xzf arm-localize-package.tar.gz && cd arm_localize \
  && python3 -I -B arm_localize_selftest.py \
  && python3 -I -B arm_localize_bench.py --out benchmark --warmup 1 --repeats 5"
# 结果拉回并对照（platform=armv7l 与 A9 同口径；bbox/像素/PGM/hex 字节级一致才算 PASS）
scp -r <user>@<pi>:~/arm_localize/benchmark data/logs/<date>-pi-a72-bench/pi-benchmark
python sim/vision/compare_arm_localize_bench.py \
  data/evidence/2026-10-03-arm-localize-baseline/pc-benchmark data/logs/<date>-pi-a72-bench/pi-benchmark
```

归档：`data/logs/<date>-pi-a72-bench/`（README 写明命令、Python/OS 版本、原始输出链接）+ `docs/arm-localize-results.md` 附三方表。注意：armv7l 32 位系统下 Python 版本可能与 A9（3.10）不同，差异在 README 注明口径。

## §4 R2 mock 宿主 runbook

```bash
# Pi 上（src/pynq_host 同目录需有 vision_protocol.py）
python3 vision_mock_service.py --host 0.0.0.0 --port 8765
# EXE 侧
vision_preview.exe --mock --endpoint http://<pi_ip>:8765
```

默认绑定 127.0.0.1 不变（本机联调零影响）；`--host 0.0.0.0` 仅为远程联调开。联调记录标注 MOCK ONLY。

## §5 R3 回放源 runbook（线到货后）

```bash
python sim/scripts/make_replay_scene.py            # 生成 PGM 场景 + concat 清单
# 素材拷到 Pi，组装并循环播放（Pi 需 ffmpeg）
ffmpeg -f concat -safe 0 -i concat.txt -vf fps=60 -pix_fmt yuv420p replay.mp4
ffplay -loop 0 -vf "setpts=N/FRAME_RATE/TB" replay.mp4   # 或 vlc 循环
```

场景序列 `normal×2(重复帧段) → extra → normal → missing → empty` 直接映射 M3 验收用例；合成灰底场景不用于识别精度评价。

## §6 R4 CM3 演示源（到货后）

1. 项目卡上 `raspi-config` 使能相机 + `config.txt` 锁 `hdmi_group=1`/`hdmi_mode=4`
2. 按 hardware.md §4 验线（base overlay 直通先行）
3. 采集规程 §2 机位定标（40–80cm）后进入数据采集

## 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-10-03 | 首版：R1–R4 角色定案（方案经批准），红线五条；mock 服务加 `--host`；回放素材生成器入库 |
