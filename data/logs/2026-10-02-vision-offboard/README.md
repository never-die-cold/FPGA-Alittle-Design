# 模块二离板冲刺证据（2026-10-02）

代码起点 dev/vision d5ccd7e，本目录与 `docs/vision-offboard-next.md` §3 的 12 步清单对应。
所有命令在仓库根目录执行；Vivado 2026.1，iverilog 13.0，XSim 随 Vivado。
`*-before/after` 成对日志为修缓冲所有权前后的定向复现；`hdmi*/route*` 为 Vivado 构建。

## 全量回归（可复现入口）

```bash
bash sim/scripts/run_iverilog.sh all          # 核 + 门禁自检 + 22 视觉 tb + Python
bash sim/scripts/run_vision_xsim.sh all       # XSim 同判据对拍
bash sim/scripts/run_vivado_vision_impl.sh    # OOC post-route
bash sim/scripts/run_vivado_hdmi.sh           # 物理 HDMI 工程
```

| 证据 | 日志 | 结果 |
|:---|:---|:---|
| 全量回归 | all-step1.log / all-final.log | 退出 0：16 核测试 + 门禁 8 例 + 22 视觉 tb + 3 Python |
| 全量复检（接手后） | riscv-recheck.log | 同口径退出 0；CoreMark CPI=2.105 |
| XSim | xsim-console.log / xsim-final-console.log / xsim-recheck.log | 同判据 PASS |
| cop_buf 修复前 | copbuf-before.log | 压力 tb 复现串帧，门禁拒绝（预期失败） |
| cop_buf 修复后 | copbuf-after-all.log / metadata.log | 争用/拥塞/复位全过 |
| 异步配置 | config-unit.log / config-top.log / top-async.log | 原子组、busy SLVERR、epoch |
| 彩色显示 | color.log / pipeline.log / real.log | RGB 直通 256/1843200 px 精确，快照 ID 精确 |
| sobel 打拍 | sobel-retime.log | gauss+sobel 49→50 拍，时序收敛 |
| OOC post-route | route-before/ route/ gate-recheck-console.log | WNS=+0.330/WHS=+0.027 与复检 WNS=+0.629/WHS=+0.009，无阻塞 DRC |
| 物理 HDMI | hdmi/（timing/drc/cdc/utilization + driver.log） | 布线完成、时序约束全满足、DRC 0 错误、bitgen 成功 |
| Python 协议 | python-config.log / python-final.log / localize.log | 提交/确认/超时/回绕 + 定位契约 |
| Windows EXE | client-build.log / client-http.log / client-render.log + preview-mock.png | 打包自检 + HTTP 联调 |

## 物理 HDMI 工程状态与边界

`hdmi/driver.log`：PS7 + dvi2rgb/rgb2dvi + vision_axi 全链布线完成、时序约束
全满足、DRC 0 错误，bitgen 成功。首次 `write_hw_platform` 报 Common 17-69：
`write_bitstream` 写了自定义路径，工程模式导出只认 impl_1 run 目录内的 bit。
`build_hdmi.tcl` 已改为 `launch_runs impl_1 -to_step write_bitstream`（bit 入
run 后复制到 $out）；对既有工程按同流程补导出（`hdmi/export_xsa.tcl` +
`xsa-export.log`）成功，`sim/build/hdmi-project/vision.xsa` 内含 `vision.bit`
+ `vision.hwh`（PYNQ `Overlay()` 所需）。bit/XSA 为 sim/build 构建产物不入库。
布线后工程不再打开 Hardware Manager；下载、锁定与实机验收另行安排。

内部并行边界 OOC 正余量不证明 TMDS 引脚/相机/采集卡闭环；下载、锁定、EDID、
延迟与采集卡显示留给上板验收（负责人另行安排）。

## 门禁说明

`vision_gate.sh` 判据 = 进程退出 0 + 存在 `^PASS:` + 无行首 FAIL/FATAL/ERROR。
`gate-selftest.log` 为 8 例故障注入自检；含 ERROR 文本的合法日志（如 hdmi/driver.log
的 XSA 失败）会被门禁拒绝，属预期行为，不推翻其中已列明的单项结果。
