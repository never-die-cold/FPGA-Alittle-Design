# C01 捕获 RTL / 集成候选证据（2026-10-11）

最新状态（2026-10-11 22:30）：原 vision 已恢复，活动路径/提交应答/实际画面及 boot_id 均确认。修复候选已完成实机加载、MMIO、起始DMA停止与等待后帧首提交，20秒窗口UVC画面正常；但停止检查后 stream_seq=1474、恢复5秒等待仍不足，诊断整体未通过。C01/正式N03尚未验收；旧持续复位候选禁止重试。详见末尾本轮记录及 docs/project-handoff-2026-10-11.md。

基线 `dev/model@c292038`；新增源码未提交。用户授权接手阻塞依赖，快速模式免题；用户离线期间继续无需人工的工作。本记录不代签 C01/N03 全体验收。

## 实现与离板结果

新增 `capture_stream_monitor.v`、`capture_fault_cdc.v`、`capture_status_axi.v`、定向 CDC XDC，以及两个自检查 tb。观测 AXIS 接受握手、严格 SOF/EOL/几何，故障优先于帧尾；故障后等待新 SOF。溢出采用保持请求/确认同步，源停钟不丢 pending；读状态不因 HDMI 失锁失效。所有写、非法或未对齐读 SLVERR，分离 AW/W 和响应背压均覆盖。

`create_capture_hdmi_bd.tcl` 并联原显示和捕获。捕获原彩色位序转换、Video In 异步 FIFO、VDMA 24位 S2MM/4帧/64位HP0；MM2S关闭。pipe/status/DMA 为 0x40000000/0x42000000/0x43000000，各64KiB；IRQ连接PS。`stream_seq` 不是 DDR 写完成或缓冲所有权证据。

| 核查 | 原始证据 | 结果 |
| --- | --- | --- |
| Verilog-2001 默认解析 | verilog2001-final.txt | PASS |
| 视觉 Icarus 25 tb | vision-regression.txt / exit.txt | 0 |
| 全项目回归，含4种 CoreMark | full-regression.txt / exit.txt | 0；当时 Python 为原8组 |
| 最终 Python 10组统一入口 | python-entry-final.txt / exit.txt | 0；新增 UART receiver、板探针替身 |
| 捕获2 tb XSim | xsim-capture-final.txt / exit.txt | 0 |
| 原 axi_lock XSim | xsim-axi-lock.txt / exit.txt | 0 |
| 整体 BD | integrated-bd-second* | 0；1项 monitor 元数据 WARNING |
| Windows PowerShell5 一键 BD | one-key-validate* | 0 |
| 最终实现和 bitstream | bitstream-checked* | 0 |
| XSA 内嵌 bit/hwh 字节与地址/参数 | artifact-contract-check.txt / checked-artifacts.json | PASS |
| 接收器二进制/短读/拒绝覆盖/损坏 | uart-receiver-offline.txt | PASS；仅离板 |
| 板探针正常/坏哈希/加载/锁定/烟测/运行DMA保护 | board-probe-offline.txt | PASS；仅替身，不是实机 |

表中的 `xxx / exit.txt` 对应实际 `xxx-exit.txt` 文件；所有失败和通过日志并存。统一命令为 `bash sim/scripts/run_iverilog.sh all`、`... vision`、`... vision_python`、`bash sim/scripts/run_vision_xsim.sh capture` 和 `... axi_lock`。构建入口 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_c01_capture.ps1 -Stage validate|bitstream`。

## 最终配套产物与源码

工程 `sim/build/c01-hdmi-1791710185764742/c01_hdmi.xpr`，最终同 basename `capture-1791711069004993`：

| 类型 | 字节数 | SHA256 |
| --- | --- | --- |
| bit | 4045769 | 550c2f1e4417aedbaf295e1ccd64bd09203a4e71b9dc11d3a1de099e12213d41 |
| hwh | 557657 | 9ba79d781164946140de27ac648d6fd9a6f5401c1be6865dd347aea27da62516 |
| xsa | 609681 | afb4b1e417b67c1bf59d3479f0c3bea78ee7937b60f4586fdbd6b429648c8992 |

`input-manifest.json`/`inputs/` 保存首次综合 RTL 输入；`reuse-rtl-check.txt` 证明最终复用综合前 RTL 哈希一致。最终 XDC 和 pinned IP/PS/pins 完整输入另存 `data/logs/c01-capture-19af0b2c829447b89d442a6f4f09f8f3/`。Digilent 提交 f4613fff005b098065fd5d619a2b88e55720a423。本轮最终新增脚本及文档另有 final-source-manifest.json / final-inputs/；不是已合并源码提交。

报告在 `data/logs/2026-10-11-c01-hdmi-1791711069004993/`：WNS +0.495ns、TNS0、WHS +0.050ns、WPWS +0.264ns；LUT6370/53200，寄存器8340/106400，BRAM44.5/140，DSP0。没有内部 unconstrained/no_clock；RX物理时钟最坏165MHz约束未放宽。DRC 50项为 Warning/Advisory，没有 Error/Critical。

**CDC 未全部关闭**：8项 Critical（RX 内3项 CDC-7、2项 CDC-11，3项复位组合 CDC-10），35项既有配置束 CDC-15 Warning。新增3条单比特同步报告为 CDC-3 Info，源复位 CDC-9 Info；结构断言配置2条/捕获3条在综合及路由后通过。没有对整个时钟组加豁免。仍需工程审查和实机断源/长测。

## 保留的失败与修复

- 第一次整体 BD：像素 reset 极性误推断、复位同步/接口连接问题；增加明确极性、同步释放及 AXIS monitor 后通过。保留 `integrated-bd-first*`。
- XSim 首次：旧入口把所有 tb 默认按 Verilog 编译，引入其它 tb 的 SystemVerilog 错误；改为 RTL 默认 Verilog、只编译选定 tb 并对 tb 使用 `-sv`。中间 Bash 续行错误也保留；最终捕获及原 axi_lock 通过。
- 第一次实现：旧 config XDC 和新 capture XDC 中的 Tcl `if` 不被 XDC 支持。首次产物已归档到 first-build-artifacts，未用于上板。断言移到 `validate_vision_cdc.tcl`，在综合和实现打开设计后执行；只复用本轮同输入已完成综合，重新实现获得最终产物。
- UART 第一次小文件：真实 READY 但 EXIT124，未产生 PASS，未上传位流。`timeout` 默认进程组影响终端读取；实际板端 `timeout --help` 明确要求 `--foreground` 才允许此类 TTY 输入。添加该选项后同一未覆盖小文件接收、保存 SHA256、终端恢复均通过。失败及成功分别见 upload-probe* / upload-probe-foreground*，只读核查见 uart-timeout-check*。

## 板端基线与诊断边界

`board-preflight.txt` AUTH_OK、boot f3321177-d8ab-4db8-9c1e-04f9f0cfe40f；ACTIVE_BIT 是 `/home/xilinx/vision_m2/vision.bit`。原 bit SHA 4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5，原 hwh SHA c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5。

`uvc-original-still-running/` 为真实原 vision 1800帧/60.121s/1280×720 BGR 观察，exit0；这是原视频证据，不是候选、DDR或逐帧关联证明。

候选探针保持 S2MM RS=0、DMASR halted=1，仅检查真实 HWH 地址、CAP1/几何/锁定、旧 pipe 帧首 smoke；20秒显示窗口内 UVC 取图，然后自动原 vision load+smoke。DMA 停止时源 FIFO 自然可能溢出，允许错误历史出现；不应产生完整流序号。若发现 DMA 意外运行，停止自动恢复，避免对活动 DMA 重新编程。

现场结果在本文件末尾补记。原始 board-probe-offline 中 PASS/WINDOW/CLEANUP 是替身测试，不能替代实际 board-c01-coexist/board.txt。

## 未完成

PS/VDMA 帧槽交接、缓存一致性、独立完整 DDR 原帧、真实颜色和动态对拍、断源/长测尚未完成。核/CNN 未接入，正式 INT8/C02/C03、LIVE网络和工业验收未完成。用户接线的 PYNQ 没有网口链路；Pi SSH 与 PYNQ 网络不是同一路径。摄像头当前天花板/红线场景不是正式三类工件数据。

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
