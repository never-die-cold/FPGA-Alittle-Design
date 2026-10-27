# B1 板卡预检（edge 包阶段，Agent B 本会话）

> 本文件只记录事实与原始命令，不做任何构建/仿真。板线范围红线遵守。

## 时间线（本机本地时间 2026-10-26）

| 时刻 | 事件 |
|:---|:---|
| ~21:47 | SSH 192.168.50.99 通（board_ssh.py，paramiko）；hostname=pynq，uptime≈1:08 |
| ~21:47 | 板上无 cop/vision/pynq 相关服务运行；cron 仅 @reboot（旧原型服务已停，符合交接文档口径） |
| ~21:47 | 两套包在板：`/home/xilinx/cop-pkg`（10/25 旧包）与 `/home/xilinx/cop-pkg-imem-20261026`（IMEM 修复 bit 59c2c918…）|
| ~21:47 | `C:\Users\ASUS\cop-pkg-edge-20261026` 暂存目录已建 |
| ~21:48 | 192.168.50.99 SSH 超时；169.254.87.99 No route to host |
| ~21:48 | COM12 打开被拒（Access denied，端口被其他进程持有——按用户说明，多 agent 并行属正常冲突，不抢不杀）|
| ~21:49–21:52 | 前台 6 轮 + 后台 20 轮（30s 间隔）轮询：两通道均不通 |
| ~21:57 | COM12 重新可开（持有者释放，未杀进程）；COM 口实探确认 |
| ~21:59 | 串口探针读到**内核启动日志**（zynq-pinctrl/pl330/macb）→ 板卡刚被断电重启 |
| ~22:01 | 串口 shell 恢复（xilinx@pynq，exit 0）：up 2 min；eth0 = 169.254.87.99/16 + 192.168.50.99/24 + eth0:1 192.168.2.99/24；连通守护也报 UP |
| ~22:02 | 本机有线网卡（Realtek ifIndex10，192.168.50.1/24）确认 Up——掉线根因是板卡重启，非本机链路 |
| 结论 | 板卡曾被断电重启（PL 位流已清、FCLK1 回 FSBL 默认）；两套包与工具仍在板上；等待 A 包中 |

## B1 补录（22:03 板上实测）

- `/home/xilinx/cop-pkg/payload/pynq_cop_40mhz.bit`（10/25 旧包）sha256 =
  `d14a4bd037b1809c74fe511f1c7667edbc6bd6ecac8a8712a423946f5f1e2a1a`
- `/home/xilinx/cop-pkg-imem-20261026/payload/pynq_cop_40mhz.bit` sha256 =
  `59c2c9185e6dcdf88f6971076a459bdf403511746a9e7b15a6ebbc6110f6d659`
- `/home/xilinx/cop-pkg-imem-20261026/payload/pynq_cop_40mhz.hwh` sha256 =
  `ec3308361eaceda2eaf7a2e745c4d43bb1509c64f0da35fa4310c47f30a8f1e8`
- 三者与交接文档申报完全一致 ✅（旧包保留完好）
- imem 包 `payload/tools/` 只有 `cop_board_fast_run.py` + `cop_payload_loader.py`，
  **没有 cop_fclk.py** → B3 传输集必须含 cop_fclk.py（板上现无）
- 重启后无 cop 服务运行；PL 当前无位流（新会话需重新烧写，属 B4 正常流程）
- 串口 shell 现成（xilinx 自动登录）；串口工具对单行命令有 ≤3000 字节与单行限制，
  复合命令优先走 SSH

## 22:0X 并行冲突观测（重要，B 线不改写他人证据）

- `dmesg` 显示**当前这次启动内已有 5 次 PL 烧写**：517s `cop_old.bin`，618/648/745/861s
  `pynq_cop_40mhz.bin`——即**另一个并行会话此刻正在板上跑 fast-run 循环**（每个 case
  重载一次 Overlay 的特征节奏）。
- 本会话的 pynq 探针（venv 真 pynq + XILINX_XRT=/usr + 非 /home/xilinx cwd）在并行会话
  活动期间 `Device.devices=[]`（疑为多进程锁/状态竞争），`Clocks` 写入与 `Overlay` 均
  "No Devices Found"。
- 板上工具事实：`cop_fclk.py` 已传至 `/home/xilinx/cop-pkg-edge-20261026/remote-tools/`；
  系统 `python3` 被残缺本地 checkout `/home/xilinx/pynq` 劫持（缺 pydantic），
  板上脚本一律用 `/usr/local/share/pynq-venv/bin/python3` 且**勿以 /home/xilinx 为 cwd**。
- loader 实现已核实：`clock`/`run` 都自带 `Overlay(bit, download=True)` 整片重载，
  **JTAG 手工烧写不是必需路径**（B4 可全程 PS 侧完成；用户 JTAG 仅作可选备份）。
- B 线策略调整：等待「A 包到达 + 板卡静默」双条件，静默判据 =
  最近 ≥90s 无 fpga_manager 烧写 且 板上无 cop/fast_run python 进程；
  绝不与并行会话同帧抢板，避免寄存器竞态污染证据。

## 本机侧已核实

- 本机适配器 192.168.50.1/24 在位（直连链路本机侧正常，故障在板卡侧或线缆）。
- COM 口枚举：COM3, COM4, COM6, COM7, COM8, COM10, COM12（COM12 在位）。
- `data/logs/2026-10-26-board/` 早前会话已有 zero/pattern fast-run 证据（6/6 matches_expected=true），
  本阶段在其后追加，不覆盖既有证据文件。

## 待通道恢复后的 B1 补录项

1. `sha256sum /home/xilinx/cop-pkg/payload/pynq_cop_40mhz.bit` 与 imem 包同路径（旧包保留证据）。
2. `sha256sum /home/xilinx/cop-pkg-imem-20261026/payload/pynq_cop_40mhz.{bit,hwh}`。
3. 当前 PL 是否仍加载 IMEM bit（重启后 PL 清空；影响 B4 烧写流程判断，仅记录，不自行决定）。

## B2 收包校验（A 包到达后执行，逐项一致才继续）

1. `Get-FileHash` tar 与 A 申报 `.sha256` 对拍 → 不一致即停、写 failure。
2. 解包到 `~/cop-pkg-edge-20261026/`，核对包内 `SHA256SUMS` 逐文件。
3. 核对 VERSION、gate 日志 5 条 IMEM/readmem 行 + WNS/DRC/CDC、A 申报的 bit/hwh/xsa SHA。
4. A 申报已知问题清单与包实际内容一致性（仅记录，不放行未申报项）。

## B3–B6 执行手册（板上命令，root + pynq venv；文件一律取自校验通过的 A 包）

约定：`PY=/usr/local/share/pynq-venv/bin/python3`，板上包目录 `/home/xilinx/cop-pkg-edge-20261026`。

- B4 时钟（先于 JTAG 烧写设置）：
  `echo xilinx | sudo -S $PY payload/tools/cop_fclk.py set --clk 1 --mhz 40`
  期望 `after_mhz=40.0, in_spec=true`（FSBL 会把 FCLK1 留在 142.857，烧写不会改 PS 时钟）
- B4 烧写：**由用户/队友做 JTAG**（本机不启动 Vivado）；板线只等"烧完"信号
- B4 活性：`echo xilinx | sudo -S $PY payload/tools/cop_payload_loader.py clock --reads 20 --package . --smoke-timeout 2`
  期望 20/20 首读 STATUS=0x00000001（READY）
- B5 两例：`sudo -E $PY payload/tools/cop_payload_loader.py run --package . --case zero --measurement zero.json --timeout 10`（pattern 同式）
  期望 matches_expected=true（对 EXPECTED_OUTPUTS.tsv）
- B6 训练：`run --case roi_001 --measurement roi_001.json --timeout 10`
  期望 class=2, margin=53, score=6837, logits=41,-30,-12（即 29e2f4 三字），MODEL_ID=0x4A303250
- 失败快照（寄存器原始口径，MMIO base+偏移）：
  COP@0x40000000: STATUS=0x010, ERROR_CODE=0x014, CFG_SEQ=0x01C, CFG_APPLIED=0x020,
  MODEL_ID=0x024, WEIGHT_CRC32=0x028, WORK_ORDER=0x034, DMA_BYTES=0x084, FW_DECISION=0x08C
  DMA@0x40010000: DMACR=0x00, DMASR=0x04, SA=0x18, LENGTH=0x28
  GPIO@0x40020000: GPIO2_DATA=0x08
  板上快速快照优先用 SSH：`sudo -E $PY payload/tools/cop_payload_loader.py` 的报错已含寄存器；
  串口通道时用 `serial_send_v2.ps1` 发单行 python -c 读 /dev/mem（命令 ≤3000 字节限制）。
- 传输通道优先级：SSH/SFTP（board_ssh.py --upload）→ 串口（serial_send_v2.ps1）。
  SSH 网络与 COM12 是两条独立物理链路，当前同时不可用（见上表），恢复任一即可开工。

## 训练权重预置（B6 备用，不替代 A 的 trained 包门）

- 本机已有归档 `data/logs/2026-10-26-trained-payload/`（manifest.json + payload.bin + network-vectors），
  README 申报：payload.bin sha256=a31a26f734796aa9867507ae5fea68581b314e2c8eb3aed1aee26075cdbd8736，
  crc32=0x05b6f630，RTL 仿真 roi_001 PASS（logits=29e2f4 class=2 margin=53）。
- 仅作 A 包迟到时的候选素材，是否启用由用户决定；默认等 A 的 trained tar。
