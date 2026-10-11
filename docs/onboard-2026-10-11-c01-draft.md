# C01 集成与取帧方案：2026-10-11 审查稿

最新状态（2026-10-11 22:30）：原 vision 已恢复，活动路径/提交应答/实际画面及 boot_id 均确认。修复候选已完成实机加载、MMIO、起始DMA停止与等待后帧首提交，20秒窗口UVC画面正常；但停止检查后 stream_seq=1474、恢复5秒等待仍不足，诊断整体未通过。C01/正式N03尚未验收；旧持续复位候选禁止重试。详见末尾本轮记录及 docs/project-handoff-2026-10-11.md。

状态：方案草稿，未冻结；不代表集成 RTL、位流或 N03 已验收。
基线：dev/model @ c292038；现场接线依据用户本次说明。

## 当前系统

```text
CM3 → 树莓派（外部电源）→ HDMI → PYNQ-Z2 HDMI IN
                                      │ PYNQ 外部电源
                                      └ HDMI OUT → 采集卡 → USB → 电脑
电脑 USB → COM12/115200 → PYNQ shell
电脑 Ethernet → 树莓派 SSH（PYNQ eth0 当前 DOWN）
```

当前视频自定义位流只有 PS GP0→AXI-Lite 配置和 RGB 直通显示。
`create_hdmi_bd.tcl` 未例化 VDMA、RISC-V SoC 或 CNN；snapshot_debug 仅接 ILA。
不能从显示成功推断 PS 能读取原图，也不能把 224×224 灰度分析快照当原彩色 ROI。

## 两个交付阶段

1. 软件诊断：加载 PYNQ base，HDMI IN→VDMA→DDR 完整 BGR 帧副本，
   用同帧做定位/ROI/FP32诊断；配置并启动 HDMI OUT，验证与取帧共存。
   base 是整片替换，期间自定义视觉/RISC-V/CNN不运行。
2. 最终集成：保留自定义 RGB 显示支路，增加独立原彩色捕获支路与 AXI-stream/VDMA，
   PS 从 DDR 读取本轮完整副本，定位/共享 ROI 后把输入送往 CNN；
   RISC-V 调度、汇总并按工单判定，PS 服务管理检查及结果。
   此阶段需要 JL/WC/NC 冻结接口、生成新 bit/hwh 并上板验收。

## 内存与接口审查表

| 通路/存储 | 当前状态 | 建议与预算 |
| --- | --- | --- |
| 视觉配置 | 已有：pipe 0x40000000，64 KiB | 保留现有地址和帧首提交语义 |
| 原帧 DDR | 自定义位流未实现 | 1280×720×3=2,764,800 字节/帧；4帧约10.55 MiB；加1个PS副本合计13.18 MiB |
| 完整帧副本 | base短时诊断已验证；custom未实现 | uint8 BGR，720×1280×3；必须先复制再释放DMA缓冲 |
| 捕获写DDR带宽 | 未实测 | 720p60纯像素约165.9 MB/s，不含协议/仲裁开销 |
| 显示支路 | 已有彩色直通 | 捕获拥塞不得向显示施加反压；拥塞时丢弃整帧并记录 |
| 像素→AXI时钟域 | 新捕获链未实现 | 显式异步FIFO/时钟转换、完整帧和溢出规则 |
| PS DDR接口 | 新捕获链未实现 | 需启用HP口并审查突发、缓存一致性、中断和驱动 |
| ROI输入 | 离板共享模块已验证 | 同一capture的半开框→64×64 GRAY8，4096字节/目标 |
| CNN权重/激活 | 正式INT8未实现 | C02冻结量化、排布和缓存，不能沿用FP32预算作为实测 |
| 核/CNN/PS寄存器 | 未冻结/未实现 | C03明确地址、握手、超时、复位、目标关联及结果布局 |
| 网络结果 | PYNQ当前无网口链路 | 首先串口诊断；N06/N09前需独立提供PYNQ网络路由 |

165.9 MB/s仅为捕获写入理想字节率；PS复制/处理与VDMA显示回读另增DDR流量。
最终设计若保留直接显示，不能引用base经DDR显示的延迟作为自定义直通延迟。

## N03 具体下一步

- 先加载并烟测现有vision，确认采集卡实际画面恢复，保存boot_id与位流指纹。
- 核实板端base路径/哈希、OpenCV/NumPy/PYNQ及视频驱动版本。
- 现有`n03_board_capture.py`只启动HDMI IN；需补HDMI OUT配置/启动/关联及finally清理。
- 用新的capture文件名；现有n03-base-001.png若已存在不能覆盖。
- 按实际驱动核对mode/shape/dtype/stride；复制后释放DMA缓冲，PNG逐像素回读与SHA256。
- 同时取得UVC画面；两个来源未做帧号关联，不宣称逐帧对应。
- 验证结束恢复原vision位流，重建驱动后再烟测与UVC取图。
- base取帧成功仅算软件诊断；自定义原帧捕获/核/CNN集成仍未实现。

依据：仓库`docs/inspection-v0-contract.md`、`sim/scripts/create_hdmi_bd.tcl`、
`src/vision/vision_axi.v`、`sim/scripts/n03_board_capture.py`及本次现场日志。
PYNQ官方视频API：<https://pynq.readthedocs.io/en/latest/pynq_libraries/video.html>；
文档支持hdmi_in.tie(hdmi_out)后读取输入帧，实际板端版本仍需核实。

## 2026-10-11实机进展（补记）

现有vision位流重载与帧首烟测通过，UVC真实画面恢复，已留日志。
N03首试输出全零PS帧；暖机复验读到5帧非零像素后停滞并超时，随后vision恢复进程段错误。
已软件重启PYNQ并确认启动输出；原视频恢复待用户登录/sudo后完成。
最终取帧脚本使用PIXEL_BGR、HDMI OUT共存、独立副本和每帧5秒异步超时；四类离板检查通过，实机未复验。
因此C01仍为未冻结草稿，N03仍未通过。详细证据：data/logs/2026-10-11-onboard-resume/README.md。


## 输入隔离诊断补记

此前重启后vision加载/烟测及UVC真画面已恢复。后续仅HDMI IN模式读到两帧非零像素后段错误139，未完成清理；新进程的PL元数据查询也段错误，已再次发起软件重启。
实际缓冲函数离板复现了缓存归还后第二次释放会munmap的分支，尚不能定为唯一根因；未修改板端驱动。最终恢复待认证后复验。C01仍未冻结，N03仍未通过；不推进N04/N05正式采集。


## 最终恢复完成

第二次重启后认证成功，vision加载/帧首smoke及24帧UVC抓图均退出0，实际视频已恢复。boot_id=f3321177-d8ab-4db8-9c1e-04f9f0cfe40f，恢复过程未再重启，bit/hwh指纹与原版本一致。本节替代之前恢复待认证的状态。N03仍未通过，C01仍未冻结；本轮不继续base取帧。


## 缓冲修复与捕获基线补齐

局部释放保护后单输入/共存三次短测共27帧通过，PS完整PNG传回核对双哈希且真实图像正常；原vision恢复成功，boot_id未变。正式N03仍未整体验收。已接手C01离板连接，24位/64位HP0/4帧VDMA子系统BD验证通过；实现选择和下一步见[c01捕获实现基线](c01-capture-implementation-baseline.md)。完整C01仍未冻结，溢出状态/显示并联/字节适配/综合位流尚未实现。

## 2026-10-11 C01 RTL 与实现更新（覆盖早期未实现状态）

续工已完成 capture_stream_monitor、capture_fault_cdc、capture_status_axi 和定向 CDC 约束；并联 RX 原彩色捕获、RGB 字节适配、异步 Video In、4 帧 S2MM、64 位 HP0、状态及 VDMA 地址译码，原 pipe 接口保留。整体 BD、25 个视觉 Icarus tb、全项目回归、捕获两项及原 axi_lock 的 XSim 和最终10组 Python 入口通过。

最终配套 bit/hwh/XSA 已生成并校验；WNS +0.495ns、TNS 0，DRC 无 Error/Critical，但 CDC 仍有8项 Critical 和35项配置束警告。不是 CDC 全通过，也不代表生产验收。第一版 XDC unsupported-if 诊断及初次 BD/XSim 失败已保留。详见更新后的[c01实现基线](c01-capture-implementation-baseline.md)及[状态契约](c01-capture-status-contract.md)。

custom PS/VDMA 帧所有权、DDR 原帧/颜色/动态对拍、断源/长测、核/CNN、正式 INT8 与真实 LIVE 仍未完成。板端显示/状态诊断结果以最新原始证据 README 为准；其保持 DMA 停止，不能替代 DDR 捕获验收。快速模式免题，不提交。

## 首次候选实机失败与离板复位修复（本节为最新状态）

首次上板候选 bit SHA550c2f... 经串口完整传输/保存验证；HWH9ba79...及实际执行探针5bd699...均核对。board-c01-coexist/board.txt 无 PASS/WINDOW/CLEANUP，主机85秒等待退出124，远端完成未确认。普通 CPU 只读命令20秒、一次 Ctrl-C 后15秒探测均无回包；只读 BREAK+w 内核请求收到0字符（不能据此断言 SysRq 已启用）。uvc-after-c01-timeout/ 24次读取退出0，但原始图像为均匀黑屏，BGR min=max=[8,6,8]、空间跨度0；这不算显示通过。原 vision 恢复未确认，当前 boot/活动位流/板端进程未知。

实际失败 HWH 显示 C_AUX_RESET_HIGH=0、aux_reset_in 为 ACTIVE_LOW，却连接 capture_low_dout=0x0，导致 capture_reset 一直复位；包括 pipe 和捕获控制/DMA 总线。这是已证实的结构缺陷，符合黑屏/MMIO阻塞症状；最后停在什么运行阶段与全部因果仍待实机复验。

已将 aux_reset_in 接 high_dout=1，保持低有效；BD 断言极性及高电平连线。新 artifact checker 强制检查辅助/外部/调试复位和锁定常量，8类负例接入统一入口；旧候选被明确拒绝。生成的新 HWH 通过复位释放检查，实际新旧对比见 reset-handoff-comparison.json。修复版正在独立新工程重新综合实现；未经现场恢复/验证，不再试载位流。

探针补 STAGE 即时日志、15秒重复 Python 栈转储、HWH布局校验后才下载，runner Python -u；离板正常/错误/活动DMA保护及预下载拒绝均通过。board-executed-c01_status_onboard.py 是按上传SHA256恢复的逐字节原失败脚本；当前改进脚本不同，未上板。最终11组 Python 回归见 python-entry-reset-final.txt / python-entry-reset-final-exit.txt=0；期间两次错误 Bash/WSL/PATH 入口的失败原样保留，实际通过入口使用 C:/msys64/usr/bin/bash.exe 和显式工具 PATH。

用户离线，因此不要求即时认证。返回后先现场复位/恢复 Linux，再用 pynq_serial_console.ps1 登录 xilinx、sudo -v、Esc释放COM12；随后先恢复原 vision 并验证 smoke/UVC/boot和原文件哈希。不要重新执行旧候选；修复版也需恢复后分阶段诊断，尚非发布位流。

## 修复版离板交付完成（2026-10-11 18:30，Asia/Shanghai）

独立重新综合/实现/bitgen退出0：sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.{bit,hwh,xsa}。实际新版artifact checker对配套字节、地址、VDMA参数、RGB及复位释放全部通过；不是实机通过。完整输入及原始构建日志在data/logs/c01-capture-e2a602d6e0da49a2b6da072abca47c70/。

| 产物 | 字节 | SHA256 |
| --- | --- | --- |
| bit | 4045769 | 86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f |
| hwh | 557643 | eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c |
| xsa | 609696 | 421c52355dedc1185499ef794d981ddd7315dbc68f89688288fdadc3a04cc4a7 |

新报告data/logs/2026-10-11-c01-hdmi-1791713720540454/：WNS+0.495ns/TNS0、WHS+0.050ns、WPWS+0.264ns；LUT6370、寄存器8340、BRAM44.5、DSP0；DRC无Error/Critical。单独从已完成路由检查点生成FIFO总线skew报告，6条报告路径均MET、最小余量+8.903ns；相关报告补入今后构建。CDC仍8项Critical（5 RX/3复位组合）和35项配置束Warning，不称CDC全部通过。综合/路由后2+3条CDC结构断言均通过。

完整25项XSim all已退出0（xsim-all-final*）；Icarus25项及全项目回归先前0，最终11组Python0。新诊断脚本及修复位流均未再次上板。用户返回后探测发现COM12不存在，其余为蓝牙串口，USB Video仍存在；已请求重接串口/现场重启及用户私下登录sudo，密码不入聊天。原vision文件未覆盖，当前运行状态/恢复仍待连接后核实。

## 返回后实机诊断与交接（2026-10-11 22:30，Asia/Shanghai）

用户现场重连COM12、重启、认证后，先恢复原vision，smoke与UVC24帧正常；boot_id为312c2889-f77a-438a-9c74-2a07e8a5b9c6。修复候选bit SHA86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f，HWH SHAeaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c，两个独立remote保留不同脚本版本。

第一次修复版实机正常通过metadata/download返回、地址、VDMA起始RS=0/Halted=1、CAP1/1280/720、lock；原pipe即时smoke无帧首应答，finally原vision即时smoke也NOVIDEO，BOARD_EXIT=3，无WINDOW。稍后独立原vision smoke通过，CPU与boot不变。证据在board-c01-reset-fixed-coexist/及reset-fix-post-probe-smoke.txt。

本步只修改sim/scripts/c01_status_onboard.py与sim/vision/test_c01_status_onboard.py，增加候选锁定及恢复加载后的各5秒等待与顺序断言，没有RTL改动。第一次PowerShell引号编辑失败，未应用代码；board-probe-settle-offline.txt是旧脚本测试，不能当新改动证据。实际修订后board-probe-settle-applied-offline退出0，最终统一Python回归python-entry-handoff退出0（11组）。按用户快速模式免题，不commit/push。

第二次在board-c01-reset-fixed-settled-coexist/：等待后pipe配置号1帧首应答通过；20秒共存窗口内UVC24帧、1280x720 uint8 BGR、实际场景非均匀且人工查看。PNG SHA4cfc0e5166f08f11c3a7c6daa5936d7615712977c70d4fce0e2d3be1e97f9fac；UVC结束早于cleanup。CSR为{0x0:1128353841,0x4:3,0x8:1474,0xC:0,0x10:0,0x14:1280,0x18:720,0x1C:0,0x20:0}。stream_seq不为0，现有探针判据不成立；finally恢复等待5秒后smoke NOVIDEO的SystemExit3掩盖该RuntimeError，BOARD_EXIT=3/wrapper退出1，无CLEANUP成功标记。因此仍未通过完整诊断；有画面不代表DDR取帧通过。

实际生成顶层vision/synth/vision.v的VDMA、VideoIn、status TREADY同接capture_input_video_out_TREADY，未发现监控接常量。窗口结束DMA CR/SR没有读取；下一步需要记录起止真实值并核对AMD IP停止期间握手行为，不能无证据删除零计数判据。周期15秒faulthandler在正常20秒sleep输出Timeout栈，仅为定时转储，不是65秒进程超时或CPU挂死。

最终另行复查原vision：reset-fix-final-original-smoke.txt退出0，配置号2 applied=2；reset-fix-final-active-path.txt返回/home/xilinx/vision_m2/vision.bit；原bit/hwh哈希未变，boot_id未变。uvc-final-original-restored/24帧有正常真实场景，PNG SHA0f32b5451a486a59d1658154df432822b385106d2094a8165cc108b4a56f55d6。最终恢复完成、COM12已释放；不需因旧历史记录再要求现场重启。

未完成：custom DDR帧槽所有权/缓存/完整BGR实测、长测/断源恢复、核/CNN/正式INT8与LIVE工业闭环。用户要求换对话，本轮停止试载，完整交接另存docs/project-handoff-2026-10-11.md及Codex outputs同名文件。
