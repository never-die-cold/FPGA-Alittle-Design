# C01 原彩色捕获实现基线

最新状态（2026-10-11 23:15）：stream_seq 疑点实测闭环——停止期 60fps 满速"接受-丢弃"为 IP v6.3（FSYNC=2）行为，
改进版诊断（起止 CR/SR 实值 + SEQ 增量 + 异常分离 + 有界恢复）实机整体 PASS；显示/状态口径可复现，DDR 取帧验收仍未做。
详见本轮证据 `data/logs/2026-10-11-c01-probe-evidence/README.md` 与 docs/project-handoff-2026-10-11.md 增补节。

2026-10-11；基线 dev/model@c292038，新源码尚未提交。状态：捕获状态 RTL、整体 BD、实现及配套 bit/hwh/XSA 已离板验证；C01 整体尚未冻结、正式 N03 尚未通过。
现场结果与原始证据见 `data/logs/2026-10-11-c01-capture-rtl/README.md`。本文件替代早期“未实现 RTL/位流”的状态描述。

## 已实现的连接

```text
HDMI RX 原彩色 R,B,G（pixel clock）
 ├─ 原 vision_axi → HDMI TX → UVC → PC
 └─ R,B,G → R,G,B 字节适配 → Video In async FIFO
       → AXIS 24-bit → VDMA S2MM → AXI4/AXI3 → HP0 64-bit → DDR
                       └─ capture_status 旁路观察握手/完整几何/错误
PS GP0 → AXI-Lite 解码 → pipe / capture_status / VDMA
VDMA S2MM IRQ → PS IRQ_F2P[0]
```

捕获反压不返回显示支路。VDMA MM2S 关闭，4 个帧存储；控制、AXIS、HP0 使用 FCLK0 100MHz。像素域使用真实 RX PixelClk，异步 FIFO 处理跨域。失锁只触发像素复位，AXI 状态和历史计数仍可读；PS 复位同步释放。

| 接口 | 地址/范围 | 含义 |
| --- | --- | --- |
| pipe | 0x40000000/64KiB | 保留已有参数及帧首提交 ABI |
| capture_status | 0x42000000/64KiB | CAP1 只读状态；写及非法读返回 SLVERR |
| capture_dma | 0x43000000/64KiB | VDMA S2MM；本轮板端探针保持停止 |
| 核/CNN | 未接入 | 地址和握手仍待 C03 |

状态与故障规则见 [捕获状态契约](c01-capture-status-contract.md)。`stream_seq` 仅统计接受到的完整像素几何，不证明 DDR 写完成或缓冲归 PS 所有。`rejected_frames` 统计已开始跟踪而作废的帧；保持故障和跨域握手会合并事件，不能当所有源帧丢失总数。

## 内存与颜色边界

| 项目 | 预算/实现 |
| --- | --- |
| 首版几何 | 1280×720，uint8 BGR；行 HSIZE=STRIDE=3840 字节 |
| 单帧 | 2,764,800 字节 |
| 4 DMA 帧 + 1 PS 完整副本 | 13,824,000 字节，约13.18MiB；不含 ROI/额外缓存 |
| 捕获写入 | 720p60 理想165.888MB/s；DDR 吞吐未实测 |
| 位序 | 原 Digilent 高到低 R,B,G 转 R,G,B；预期 DDR 低地址 B,G,R |

字节适配已有逐字节 RTL 测试；真实 DDR 颜色、动态图像无混帧和色卡定标未验证。PS 完整帧所有权适配未实现：必须完成 VDMA 写完成/错误/写槽交接、缓存同步、独立复制和幂等归还。base 短测已通过27帧，不替代 custom DDR 或长测验收。

## 构建与验证

仓库根目录执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_c01_capture.ps1 -Stage validate
powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_c01_capture.ps1 -Stage bitstream
```

需已准备锁定的 HDMI IP、PS 配置及管脚输入；入口检查缺项后停止，不覆盖旧工程。每次在 `sim/build/` 新建工程，并在 `data/logs/` 保存输入文件、SHA256、原始日志及退出码。Digilent 锁定提交为 `f4613fff005b098065fd5d619a2b88e55720a423`。

复位修复前的首次上板候选为（现已隔离） `sim/build/c01-hdmi-1791710185764742/capture-1791711069004993.{bit,hwh,xsa}`，XSA 内嵌 bit/hwh 与外部文件逐字节一致。第一次实现中的 XDC 不支持 `if` 诊断已保留；断言移至 Tcl，验证 RTL 与原综合输入同哈希后复用本轮已完成综合并重新实现，最终构建退出0。

首次候选时序 WNS +0.495ns、TNS 0、WHS +0.050ns、WPWS +0.264ns；LUT 6370、寄存器8340、BRAM44.5、DSP0。DRC 无 Error/Critical；仍有8项 Critical CDC（5项 Digilent RX、3项复位组合路径）及35项既有配置束 CE 警告，不能称 CDC 全部通过。新增3条单比特同步路径报告为 Info；未新增全时钟豁免。完整报告见 `data/logs/2026-10-11-c01-hdmi-1791711069004993/`。

Icarus 25 个视觉 tb、全项目回归退出0；新增两个捕获 tb 与原 axi_lock 在 XSim 通过；最终10组 Python 入口通过。整体 BD 保留1项 AXIS monitor 元数据 WARNING，已归档。

## 尚未完成

- PS/VDMA 帧槽所有权与完整 DDR 副本、真实颜色/动态对拍、断源恢复及长时间运行。
- 核/CNN/C02/C03、正式 INT8 模型、真实 LIVE 网络与工业闭环。
- 工位定标、真实三类数据与正式 N03/N04/N05。现有天花板画面仅用于链路诊断。

显示/状态板端诊断只验证地址、锁定、原视觉 smoke 和 UVC 共存；它不启动 DMA，不代签完整 C01 验收。

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

## stream_seq 疑点实测闭环与改进版诊断 PASS（2026-10-11 23:15，Asia/Shanghai）

按交接 §7.2/§7.3 完成，证据与源码引证全文见 `data/logs/2026-10-11-c01-probe-evidence/README.md`。要点：

- **判据修正有据**：与板上同源的 axi_vdma v6.3 源码（本地 Vivado 2026.1）显示，实际 HWH 的 `C_USE_S2MM_FSYNC=2`
  配置下，halted 状态显式置 `d_tready_before_fsync`/`clr_flag1`（vh_rfs.vhd 71911/71925 行），产生 dummy tready
  （71761 行或项）；同时 `tvalid_int = tvalid AND chnl_ready`（71760 行）保证停机不写 DDR。
  "停止时 stream_seq=0"旧判据与该 IP 行为相悖，予以替换。
- **新判据**：窗口结束时通道仍 halted（CR.RS=0、SR.Halted=1）+ 锁定保持 + 捕获故障位/error_epoch 全零；
  起止 CR/SR 与 SEQ 增量全部打印实值。
- **实测**（候选 bit `86d2adb0…`，远端新目录 `c01-ab75f5d2…`）：CR 全程 0x00010002 不变；
  SR 0x00010001→0x00014811（新增 DMAIntErr/FSIZE_MORE_OR_SOF_LATE_ERR/ERRIRQ 粘滞位，属停止期 IP 自身行为）；
  stream_seq 81→1281，**delta=1200=60fps×20s 精确吻合**。CAP1 全零故障。BOARD_EXIT=0，UVC 24 帧真实场景。
- **脚本纪律落地**：主检查异常与恢复异常分离（MAIN-FAIL/RECOVERY-FAIL/MAIN-FAIL-WAS 分别打点）；
  faulthandler 改单次 60 秒兜底；恢复改有界单次重试（两次 5 秒 settle+smoke），本轮恢复 smoke 一次通过。
- 改前脚本/测试逐字节归档于证据目录 `settled-script-archive/`；11 组 Python 回归退出0；
  本轮无 RTL 改动，不重跑 RTL 回归。
- **仍未完成**：DDR 帧槽所有权协议、真实 BGR/动态对拍、N03 长测；PS 驱动启动捕获前须复位/清 VDMA 粘滞 SR 错误位。
  窗口前 81 帧（≈10fps 均值）低于窗口内 60fps 的原因未解释，列为下轮观察点。
