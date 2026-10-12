# 2026-10-11 现场N03诊断与恢复

用户请求：浏览项目后按三人收尾计划继续；确认Pi/PYNQ均外部电源、Pi HDMI进PYNQ、输出经UVC、PYNQ走COM12、Pi走电脑网线SSH。
用户补充授权：sudo认证完成；随后明确“快速模式，完成诊断并记录，免出题”。本轮按该授权免理解题，不commit/push。

先读仓库AGENTS.md、workflow、主计划、核契约、收尾清单及现有板务证据，并核对dev/model@c292038和未跟踪文件。
八项现场只读盘点、八组视觉与十三组离板回归通过；认证后vision加载/烟测与真实UVC画面恢复通过。
修改N03的PIXEL_BGR、HDMI OUT共存、唯一文件名、复制/释放及退出清理；初次取得全零帧，不算验收。
暖机复验读到5帧实际非零像素后停滞，timeout退出124；恢复vision进程段错误退出139。
已保存内核/进程/boot_id/驱动源码，并执行软件重启，收到systemd启动输出；尚待用户登录认证与原视频恢复。
最终脚本改为异步读帧5秒超时；四类假驱动故障检查通过，实机未验证，不宣称根因已修复。
新增串口交互脚本供用户本人输入登录与sudo，不写日志；语法通过，交互待验证。

证据入口：../../data/logs/2026-10-11-onboard-resume/README.md。
设计稿：../../docs/onboard-2026-10-11-c01-draft.md。
原始失败、修改前及两次实机脚本快照全部保留；未覆盖既有证据，未改RTL、接口契约或验收勾选。
未完成：故障后vision恢复确认、N03有效原图/HDMI OUT共存、正式集成位流、INT8/CNN/核/LIVE闭环。


续工：用户ok后验证新boot_id/sudo，恢复vision、烟测及UVC真画面通过。InputOnly隔离实机两帧后段错误139；停止工具在PL.ip_dict阶段也139，未进行MMIO写入。保存证据后再次软件重启，等待用户手动认证完成最终恢复。
新增无硬件缓冲函数分支复现，确认第二次freebuffer会munmap；候选保护仅离板验证，不宣称唯一根因已修复。五类假驱动测试通过。新runner加faulthandler/TERM后KILL上限；未改驱动、RTL、验收状态或提交。


最终恢复：用户回复ok后验证AUTH_OK及新boot_id，原vision加载/烟测/UVC24帧均退出0；实际图像正常，恢复后boot_id不变，原bit/hwh哈希一致。全部原始证据已归档；恢复确认完成，N03仍未通过。仅更新日志与文档，快速模式免题，不commit/push。


用户continue并要求接手阻塞依赖：加入局部cached释放保护，生产helper生命周期及五类取帧测试通过；三次实机短测共27帧均清理完成，无重启。有效PS PNG串口取回核对文件/像素哈希，输出共存窗口UVC通过；观察器首次ExitCode为空的误报保留，Handle修复后完整复验0。最终原vision加载/烟测/UVC及指纹/boot_id均通过。
接手C01：Vivado实际子系统BD验证与参数读回通过（24位、HP0/64位、4帧、RGB=2），保留只读参数/时钟缺口/Tcl续行/错误视频枚举导致失败。未改RTL、板端驱动或提交；C01/N03未整体验收。新证据data/logs/2026-10-11-n03-buffer-guard/及2026-10-11-c01-capture-probe/。

补记：C01持久xpr/bd复验0、实际文件存在；本轮生成目录安全保留到sim/build，根目录恢复干净。最终diff/未跟踪新增文件空白检查通过。

## C01 续工与用户离线期间的自主事项

用户要求接手阻塞依赖，并在离线期间继续无需参与的事项。沿用快速模式免理解题；没有 commit/push，也没有向真实队友发消息。

新增捕获 AXIS 几何监测、保持型 overflow CDC、CAP1 只读 AXI-Lite 状态和定向约束；并联原显示，新增原彩色位序转换/Video In async FIFO/4帧 S2MM/HP0、GP0解码及中断。25个视觉 Icarus tb、全项目回归（原8组Python）均0；新增捕获两项及原 axi_lock XSim0；后续最终11组 Python 入口0。Verilog-2001默认解析通过；无核/CNN接入、无PS帧槽所有权或DDR捕获验收。

第一次BD极性/复位/监视连接失败，修正后通过，仍保留1条monitor元数据警告。XSim旧入口误编译所有TB导致SV解析失败，随后Bash续行失败；最终仅选定TB按-SV、RTL默认Verilog通过。首次实现有XDC不支持if诊断；将原config和新capture断言移至Tcl。原综合RTL指纹一致后复用本轮综合、重新实现，生成capture-1791711069004993配套bit/hwh/XSA。WNS+0.495/TNS0/DRC无Error-Critical，但仍8项Critical CDC及35项配置束警告，未称CDC全部通过。所有失败产物和原始日志保留。

用户ok后实际AUTH_OK和原位流/boot/指纹验证0。UART第一次小文件READY后EXIT124，查板端timeout帮助发现TTY需--foreground；修改后小文件、bit4,045,769字节、hwh557,657字节均真实传输且板端SHA通过。原实际执行探针SHA5bd699...已逐字节复原归档。

首次候选真实显示/状态诊断没有返回PASS/WINDOW/CLEANUP，主机85秒超时124；之后普通CPU只读命令、一次Ctrl-C后探测均无回包，只读BREAK+w也0字符（不证明SysRq启用）。UVC24次读取本身0，但图片均匀黑屏BGR[8,6,8]，不算显示通过。恢复原vision未确认。用户离线，未重复索要密码，也未盲目试载/重启。

离板发现真实HWH C_AUX_RESET_HIGH=0 / aux_reset_in ACTIVE_LOW，却接capture_low_dout=0x0，明确导致总线与pipe永久复位。修正为high_dout=1，新增BD极性/连线断言及artifact复位释放检查；8类负例接入统一Python，旧HWH被拒绝，新生成HWH通过，原始对比JSON落盘。修复版在新项目重新综合实现，现场症状仍需恢复后复验，不宣称完整因果或实机修复成功。

诊断探针增加STAGE即时日志、Python15秒重复栈转储及下载前HWH地址校验；Python-u。正常/异常清理、活动DMA不重编程保护、错误HWH不下载的替身测试通过；新脚本未上板。一键构建今后自动校验配套产物和复位；本次构建启动时旧wrapper已载入，故另行实跑最终校验。

范围为src/vision、sim/vision、sim/scripts、docs、data/logs及本日志；新代码与完整输入摘要留存。C01总体未冻结，正式N03、PS所有权、真实DDR原帧/颜色/动态/断源长测、INT8/核CNN/LIVE/工业闭环未完成。返回后先复位/登录sudo再恢复原vision；旧失败候选禁止重试。详细证据../../data/logs/2026-10-11-c01-capture-rtl/README.md。

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
