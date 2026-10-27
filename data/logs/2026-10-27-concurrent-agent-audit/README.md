# 2026-10-27 并发会话审计与板端诊断

- 日期：2026-10-27，时间锚点为电脑 Asia/Shanghai；板端系统日期错误，不能据其墙钟排列事故。
- 基线：`dev/riscv` / `bc37c08ccc3c1293e35c8cc4bfc2809fb091ef4e`；仅一个 Git worktree，领先 origin 4 个提交。
- 开工已有 9 个跟踪文件改动，245 行新增 / 26 行删除；本轮保留全部源码改动，不提交、不合并。
- 范围：读取本机 DeepSeek Harness / ZCode 会话与现场状态；记录证据；停止明确识别的残留测试/旧服务；用已有视频程序诊断。
- 结论：发现真实的资源竞争和包版本混用；冷启动恢复网络，视频重载和 HDMI 重连后经板图像恢复；不能认定 SD 卡体已损坏。

## 会话在做什么

| 应用 / 会话名 | ID 前缀 | 实际工作与交付 | 冲突 / 边界 |
|---|---|---|---|
| DeepSeek「检查分支提交与未完成待办」 | 909c290b | 分支/PR 整合、板端环境与 IMEM 诊断、fast runner、停止旧原型服务 | 也在访问同一板卡；后续尝试绕开 PYNQ 解析直接配置 PL |
| DeepSeek「28号前冲刺完成赛题成品」 | 591aaf5b | 训练载荷导出、MODEL_ID 0x4A303251、PynqDmaPlane/驱动与测试、上板尝试 | 与其他会话共享源码和板端；结尾把故障过早归因于 SD 卡 |
| DeepSeek「成品待办计划清单」 | 3b1e94d5 | Agent A：DMA start 边沿 RTL/TB、构建门禁、edge 包、75fb2eb 等 4 个本地提交 | 22:51 有 Stop-Process 清理串口进程记录；其自述“打断 B 传输”不能单独证明全部故障原因 |
| ZCode「多Agent并行冲突处理说明」 | db9b5f1b | Agent B 上板；23:29 用户授权后接管本机构建，增加地址钉死、MMCM、门禁；重打包并改板端工具 | 包目录复用，旧文档/新位流/旧运行工具未统一；四例仍未跑通 |

原始消息/工具摘录：`deepseek-excerpts.json`、`zcode-excerpts.json`。只导出项目相关内容，不导出账户配置。
Git 分支、唯一 worktree 与 reflog 见 `git-state.txt`；三个 DeepSeek 会话共享工作目录，未隔离 Git index 或构建输出。
DeepSeek 原始来源为 `C:/Users/ASUS/.dsh/sessions/--E-Projects-FPGA-Alittle-Design--/` 下三个 zstd 会话；ZCode 为只读打开的 `C:/Users/ASUS/.zcode/cli/db/db.sqlite`。
ZCode 的 Selection side chat 只解释 JTAG 操作；「帮我打开向日葵远程软件」未参与 RTL/包修改。

## 已证实的问题

1. **开机程序争用 PL**：`/etc/cron.d/pynq-live` 自动加载 vision，`bootpy.service` 又执行 `/boot/boot.py` 的 BaseOverlay。
   本次 dmesg：96.280210 秒写 `vision.bin`，134.844721 秒写 `base.bin`；视频位流被覆盖。见 `board-load-order.txt`、`board-startup-config.txt`。
2. **原型服务会复活**：同一 cron 文件启动 `park_live_server_v7.py`（8765）。它收到检查请求时会切换 capture 位流并恢复 vision，不能与 cop 测试共用 PL。
   根用户 `crontab -l` 为空不代表 `/etc/cron.d/` 没有任务；昨晚“已停服务”只对当次开机有效。
3. **同名包已换内容**：旧文档的 edge bit 为 `9341f7fa…c4160`；现 `build/board-package-edge-fix{,-trained}` 是 MMCM bit `43ac4f446cd24e11b29453585d3e31a2722a574bcd7626423b2d4cbdff87ed1e`。
   现 HWH=`ec5de273…4475d`、XSA=`a76b4ed0…a7971`；完整哈希见 `package-inventory.json`。六个包各自 SHA256SUMS 均匹配，不等于版本相容。
4. **时钟契约冲突**：现硬件的 cop_mmcm 输入为 FCLK1 142.857132 MHz，倍频 7 / 分频 25；现 loader / fast runner 却仍写 `Clocks.fclk1_mhz = 40.0`。
   如果该写入实际生效，便破坏 MMCM 输入条件；不能把直连版本的“FCLK1=40”验收直接用于 MMCM 版。本轮只做静态核对，未重跑 cop。
5. **板端存在另外修改的混合包**：`cop-pkg-mmcm-oldtool` 的 loader/runner 与当前包不同；`remote-tools/` 包含未纳入普通打包入口的 wrapper/检查脚本。
   源码、差异及 SHA 已保存为 `board-package-drift.json`；不能靠当前 Git commit 单独复现这些板端修改。
6. **中断后仍有遗留测试**：电脑 SSH PID 46240 还等待执行混合包 zero，ZCode 对应 Bash 已标 cancelled。
   本轮核对完整命令后只终止该 PID；证据 `orphan-ssh-before.json` / `orphan-ssh-action.txt`。未向其他会话发消息。

## 本轮实机结果

- 初始：网口 1 Gbps、COM12 / USB Video 均枚举；ping 0/3，串口无回复，源地址绑定后的 TCP 均超时。
- 用户断电再上电；COM12 115200/8N1 捕获 U-Boot、FIT hash OK、Linux、登录提示。见 `serial-cold-boot.txt`。
- 冷启动 boot_id=`94516e98-212e-4831-b11c-c3a49021c929`；网络恢复 ping 3/3，<1 ms；SSH 可执行命令。
- 停止本次运行的旧 park 服务 PID 659/661；启动配置、SD 启动文件保持原样，下次开机仍会触发旧任务。
- 等启动程序退出后运行板端现有 `m2_onboard.py load`、`smoke`：`PASS: load`、配置编号 1、`PASS: smoke`、退出码 0。
- 两个板端 Python 文件 SHA 与仓库 `src/pynq_host/{m2_onboard,vision_regs}.py` 一致；vision bit=`4f0c491a…d5be5`，HWH=`c0adfd36…b5a5`。
- **恢复过程中的黑帧**：USB Video index=1，1280×720，首次重载前后仍是恒定黑图，PNG SHA 均为 `08f1c9de…b0fe`；标准差 0.943。
  `PASS: smoke` 只证明配置提交获得帧首确认，不证明像素内容或 HDMI OUT 正常。图和 metadata 位于 `uvc-initial/`、`uvc-after-vision/`。
- `board-idle-health.txt`：约 5 分钟 uptime，本次未见 mmc timeout / ADMA / I/O error；无旧服务/测试进程。
- **直连对照成功**：用户将树莓派直接接采集卡后，24 帧成功，`uvc-pi-direct/raw.png` 显示真实螺丝盒；标准差 35.785，PNG SHA=`515bd252…9e16b`。
- **经板视频已恢复**：用户恢复“树莓派 → PYNQ HDMI IN → HDMI OUT → 采集卡”后，24 帧成功，`uvc-through-pynq-replug/raw.png` 显示真实螺丝盒；标准差 35.441，PNG SHA=`fea8f8fc…4a856`。
- `vision-after-replug.txt`：配置编号 1→2，smoke PASS / exit 0，uptime 13 分钟，仍无新增 mmc/ADMA/I/O error。此恢复包含重载与热插拔，不能单独证明最初黑屏只由某一个动作导致。

## SD 与事故归因的证据边界

- 历史 `../2026-10-26-board/serial-zero-oldtool.txt` 确有 mmc 超时、ADMA Err=1、WRITE I/O error，必须保留为真实故障。
- 本次见 ext4 journal recovery、FAT 未正常卸载、journal unclean 提示；这些说明存在异常断电/未卸载，不能单凭它们判定卡磨损。
- 早前读卡器只读到了 FAT 启动分区，chkdsk `/scan` 返回快照错误；没有完成 ext4 或全卡健康检查。文件大小/时间戳/单次哈希不能证明镜像整体完好。
- 当前不能排除 SD/接触/供电、配置 PL 或 DMA 干扰等原因；未完成对照实验前，不宣称“换卡即可根治”或“DMA 没问题”。
- `pulse_cop_reset()` 读回 0 后写 2 再写 0，其 bit0 没有变化；旧记录“因此必然连带复位 FCLK0”的解释缺乏直接证据。已有挂死现象仍需独立分析。

## 可复现入口与后续顺序

```powershell
python -X utf8 data/logs/2026-10-26-build/verify_packages.py
ping.exe -n 3 -w 1000 192.168.50.99
python -X utf8 sim/scripts/capture_uvc_raw.py --output-dir data/logs/<新的运行目录>/uvc --frames 12
```

串口采集用仓库 `sim/scripts/serial_read.ps1 -Port COM12 -Seconds 30 -OutFile <仓库内新日志>`；本次冷启动采集额外等待 USB COM12 随板卡供电重新枚举。
视频复现使用 `docs/runbooks/pi-camera-preview-runbook.md` 的现有 load/smoke 入口，先等待 boot.py 结束并确保没有旧服务争用；不要在 cop 位流上访问 vision 基址。
本轮无 RTL 修改，未运行 Vivado/RTL 回归；历史 RTL PASS 不升级为当前硬件验收。

1. 已完成直连 / 经板对照并恢复原接线；保持当前视频基线，后续做连续性和冷启动复验。
2. 持久修复开机顺序与 PL 单一所有者：备份后串行化 bootpy / vision / 原型服务；本轮未改配置。
3. 独立整理 MMCM 与直连两种 bit/时钟/loader 契约，固定新包名、完整源码锚点和测试入口，再做单例 DMA。
4. 若再次出现 mmc 错误，先正常停机（若可响应）、取卡只读备份并检查；重刷/格式化尚未执行。
5. **未实现/未验收**：连续作业、真实相机到硬件 CNN 到 EXE 全链、正式模型精度、M2/M3/M4 收口。

产物清单与 SHA：`manifest.json`；当前源码脏文件 SHA：`source-state.json`；检查原始输出：`diff-check.txt`。
`git diff --check` 退出码 0；原有 9 个脏文件 SHA 全部保持一致。已刷新 `data/logs/README.md` 运行索引。
全仓库卫生检查未通过：根目录遗留 Vivado/缓存生成物、历史报告链接错误；原始检查还记录了刷新前的索引过期项（`repo-hygiene.json`）。本轮未清理这些既有文件。
