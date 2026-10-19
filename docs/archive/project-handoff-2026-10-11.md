# FPGA 项目续工交接上下文

> 状态：历史交接快照（2026-10-11）。当前入口见 [plan.md](../../plan.md) 与 [project-map.md](../project-map.md)。

更新时间：2026-10-11 23:15，Asia/Shanghai。用于换对话继续工作。

## 2026-10-11 23:15 增补：stream_seq 疑点已闭环（同日续作）

§7.2/§7.3 的两步已完成，**诊断整体 PASS**，证据全文见 `data/logs/2026-10-11-c01-probe-evidence/README.md`：

- 源码查证：板上同源 axi_vdma v6.3 在实际 HWH 的 `C_USE_S2MM_FSYNC=2` 下，**halted 状态会显式产生 dummy tready
  继续握手并丢弃数据**（vh_rfs.vhd 71761/71911/71925 行），且 `tvalid_int=tvalid AND chnl_ready` 保证不写 DDR。
  旧"停止时 stream_seq=0"判据无效，已替换为"窗口结束仍 halted + 锁定保持 + 故障位全零"。
- 实测（新远端目录 `c01-ab75f5d2…`，脚本 SHA `0f0905b2…`）：CR 全程不变、SR 起止 `0x00010001→0x00014811`
  （新增位为停止期 IP 粘滞错误位）、stream_seq 81→1281（**delta=1200=60fps×20s 精确吻合**）；
  BOARD_EXIT=0、UVC 24 帧真实场景、恢复 smoke 一次通过、CLEANUP 完整。
- 脚本改动（未提交）：起止 CR/SR 与 SEQ 记录、MAIN-FAIL/RECOVERY-FAIL 异常分离、faulthandler 单次兜底、
  有界恢复重试；改前版本归档于证据目录 `settled-script-archive/`；11 组 Python 回归退出0。
- 下一步相应更新：直接进入 §7.6 custom DDR 帧槽所有权协议；PS 驱动启动捕获 DMA 前须复位/清 VDMA 粘滞 SR 错误位；
  窗口前 81 帧（≈10fps）低于 60fps 的原因未解释，列为观察点。仍不把显示/状态 PASS 当 DDR 取帧或 CNN 验收。

以下为原交接正文（2026-10-11 22:30 状态，其中 §7.2/§7.3/§7.4/§7.5 已由本轮完成）。

## 可直接发给新对话的起始消息

请读取这份交接文件和 `E:/Projects/FPGA-Alittle-Design/AGENTS.md`，继续执行项目收工计划。用户已授权快速模式，完成诊断并记录、免出题；可以接手阻塞事项，无需重复询问已授权的串口/位流诊断，但不提交或推送代码。当前 PYNQ 已恢复原 vision 位流、提交应答和实际画面均正常。下一步优先解决 C01 的 VDMA 停止期间 `stream_seq` 增长疑点及重载后的恢复等待；不要重试旧的持续复位候选，不要把显示成功当 DDR 取帧或 CNN 验收。

## 1. 用户意图、授权与环境

- 原始任务：先浏览整个项目，结合 `docs/project-closeout-three-person-checklist.md` 继续执行。此前已经浏览项目、核对主计划与相关接口；新对话从当前诊断继续，不必从零重新跑所有历史步骤。
- 用户明确说过“快速模式，完成诊断并记录，免出题”。仓库古法技能本身有快速模式豁免；提交前理解门槛仍未通过，因此本轮没有 commit/push。
- 用户允许 Codex 内终端操作，并由用户自行输入 sudo 密码。密码不进入聊天或日志。仅在实际 `sudo -n` 失败时请求重新认证，不能猜密码或自动录入。
- 用户希望接手其他人负责但阻塞进度的工作；这不授权向队友发送消息、替别人签验收或自动创建子对话。最新请求是“这里做完给我一个交接上下文，我要换一个对话”。
- 仓库：`E:/Projects/FPGA-Alittle-Design`；分支 `dev/model`；HEAD `c292038`，PR #68 合并。大量本轮修改和新文件未提交，需保留。
- 本对话 cwd：`C:/Users/ASUS/Documents/Codex/2026-10-11/ji`，Windows PowerShell。E 盘仓库在本对话可写根外；repo 写入、Git 实际检查、串口/摄像头操作使用 `exec_command` 的 `sandbox_permissions=require_escalated`。本轮自动审批均通过。
- 普通沙箱可能隐藏 `.git` 或部分生成文件，曾产生“不是工作树/找不到文件”假象。必要时在已授权范围用提权工具核查真实状态。
- 本对话的用户交付文件在上述 cwd 的 `outputs/`。最终回复用绝对文件链接。

## 2. 硬件接线与当前板卡状态

```text
摄像头 → 树莓派（外部电源）→ HDMI → PYNQ-Z2 HDMI IN
                                      PYNQ 也是外部电源
PYNQ HDMI OUT → USB 采集卡 → 电脑
电脑 USB UART → PYNQ COM12，115200，8N1，无流控
电脑 Ethernet → 树莓派 SSH；PYNQ eth0 当前 DOWN
```

用户最后已现场重新连接、重启、登录 xilinx 并认证 sudo，退出串口控制台。当前串口 COM12 已释放，没有尚在运行的本轮串口任务。此前 PID 752 是 `/usr/local/bin/redirect_server`，不是遗留 DMA 取帧任务。

**本轮最终确认：**

- CPU 正常；boot_id `312c2889-f77a-438a-9c74-2a07e8a5b9c6`，修复版两次诊断前后没有变化。
- `PL.bitfile_name` 实际返回 `/home/xilinx/vision_m2/vision.bit`。
- 原 bit SHA256：`4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`。
- 原 hwh SHA256：`c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5`。
- 最终 smoke：R11 busy=0、R12 applied=1，提交配置号2后 applied=2，PASS，串口退出0。
- 最终 UVC：24帧，1280×720×3 uint8 BGR，实际场景有非均匀内容，已人工查看 PNG；PNG SHA256 `0f32b5451a486a59d1658154df432822b385106d2094a8165cc108b4a56f55d6`。
- 认证会自然过期。新对话先做只读/`sudo -n` 预检，不要因为旧报告的“恢复未确认”再次要求重启。

证据根目录：`E:/Projects/FPGA-Alittle-Design/data/logs/2026-10-11-c01-capture-rtl/`。最终恢复证据是 `reset-fix-final-original-smoke.txt`、`reset-fix-final-active-path.txt`、`uvc-final-original-restored/`。

## 3. 已完成成果与验收边界

✅ 原核/视频已有回归及历史实机证据；本轮捕获状态 RTL、几何/故障监测、跨域请求保持、颜色位序适配、完整 C01 BD 和候选 bit/hwh/xsa 已完成离板构建与检查。修复候选在板上成功加载、MMIO 可读、VDMA 起始停止、CAP1/1280/720 正确、视频锁定、等待后原 pipe 帧首提交通过；20秒共存窗口 UVC 实际画面正常。

🟡 **C01 当前诊断整体未通过**：VDMA 停止检查后 `stream_seq` 增长到1474，与探针的零计数假设冲突；恢复后等待5秒的 smoke 仍发生一次 NOVIDEO，稍后独立复查通过。不能宣称端到端捕获或稳定恢复通过。

⬜ 未完成：PS/VDMA 写槽所有权、缓存同步、真实 DDR 完整 BGR 取帧和动态图像/色卡对拍、正式 N03 长测与断源恢复、机位定标/正式数据、INT8、CNN RTL、核/CNN 集成、LIVE 和工业闭环。`stream_seq` 只表示监测到的完整 AXIS 像素几何，绝不是 DDR 写完成或 PS 拥有缓冲的凭据。

### N03 历史短测

base overlay 取帧与 HDMI OUT 共存：3次×9帧=27帧，PS完整副本约23.1–23.9ms，PNG串口双SHA校验，UVC24帧实际场景正常；当时已恢复原位流。局部 freebuffer 守卫避免已归缓存的指针被再次 munmap，没有全局修改 PYNQ 驱动。之前零图、warmup/重复释放引发的139/重启均保留。base 诊断不能代替 custom DDR 或正式 N03。

## 4. C01 实现及修复候选

- `src/vision/capture_stream_monitor.v`：接受握手、严格SOF/TLAST/宽高、故障胜过末像素、错误后等新SOF。
- `capture_fault_cdc.v`：overflow 请求/确认两级同步，源停钟保留 pending，故障合并，不把所有丢帧计成精确事件。
- `capture_status_axi.v`：只读 AXI-Lite、分离AW/W、响应背压、非法读和所有写SLVERR、颜色R,B,G→R,G,B使预期DDR低地址B,G,R、锁定和像素复位同步。
- `capture_cdc.xdc`：仅指定3个首级D例外及 ASYNC_REG。已有 config CDC 两条同步检查也保留；未用全时钟域豁免掩盖问题。
- `sim/scripts/create_capture_hdmi_bd.tcl`：并联已有 HDMI直通显示和 Video In async FIFO→24-bit VDMA S2MM→AXI4/AXI3→HP0 64-bit；4帧，DRE，MM2S关闭，IRQ_F2P[0]。FCLK0 100MHz 控制/AXIS/DDR，RX真实PixelClk。反压不返回显示。

| 地址 | 范围 | 功能 |
| --- | --- | --- |
| 0x40000000 | 64KiB | 原 pipe，保留帧首配置 ABI |
| 0x42000000 | 64KiB | capture_status CAP1 |
| 0x43000000 | 64KiB | VDMA S2MM |

捕获CSR：0x0 CAP1=0x43415031；0x4锁定/active/fault/错误历史；0x8 stream_seq；0xC rejected；0x10 error_epoch；0x14宽；0x18高；0x1C overflow区间；0x20 lock_losses。

**可继续核查的修复版产物：**

`E:/Projects/FPGA-Alittle-Design/sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.{bit,hwh,xsa}`

| 文件 | 字节 | SHA256 |
| --- | --- | --- |
| bit | 4045769 | 86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f |
| hwh | 557643 | eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c |
| xsa | 609696 | 421c52355dedc1185499ef794d981ddd7315dbc68f89688288fdadc3a04cc4a7 |

独立新综合/实现/bitgen退出0，实际artifact checker逐字节检查XSA内嵌bit/hwh、地址、参数、RGB和复位释放通过。实际使用输入与构建日志：`data/logs/c01-capture-e2a602d6e0da49a2b6da072abca47c70/`，含固定Digilent IP、PS配置、引脚和源码快照。部分构建包装器及skew报告改进是在构建后增加的，不能说它们参与了此前构建。

报告：`data/logs/2026-10-11-c01-hdmi-1791713720540454/`。WNS+0.495ns、TNS0、WHS+0.050ns、WPWS+0.264ns；LUT6370、寄存器8340、BRAM44.5、DSP0；DRC无Error/Critical。单独路由DCP的总线skew报告6条路径MET，最小余量+8.903ns。**CDC仍8 Critical（5 Digilent RX、3组合复位）与35配置束Warning；没有全部清零，不能称生产验收通过。**

## 5. 历史失败和本轮实际诊断

### 禁止重试的旧候选

旧 bit SHA256 `550c2f1e4417aedbaf295e1ccd64bd09203a4e71b9dc11d3a1de099e12213d41`，旧HWH SHA256 `9ba79d781164946140de27ac648d6fd9a6f5401c1be6865dd347aea27da62516`。旧remote：`/home/xilinx/vision_m2/c01-a2a0452a39f94cfdbb0da5bcb750e5ca`。

实际HWH的 C_AUX_RESET_HIGH=0（低有效），aux_reset_in却接常量0，持续复位。首次上板没有阶段输出，85秒退出124、CPU命令无回包、UVC均匀BGR[8,6,8]黑屏。确切运行停点无法还原。已改接常量1，并增加BD及artifact reset gate，新检查器明确拒绝旧HWH。历史证据保留，不删除、不重载这个旧bit。

### 修复版第一次：等待前

`board-c01-reset-fixed-coexist/board.txt`：正常到达metadata→download返回→DMA停止读→CAP1/geometry→lock。pipe smoke 1秒未收到帧首，退出3；finally加载原vision后立即smoke也NOVIDEO。没有共存窗口，不能计显示通过。稍后 `reset-fix-post-probe-smoke.txt` 独立smoke通过且boot不变；UVC原vision有正常内容。

对应 `reset-fix-deployment.json`，remote `/home/xilinx/vision_m2/c01-cefc3ffab83448b1ae9e41b345276c4e`；脚本SHA `d54e99e2189922a442220d46929c6b867befc3af73a1ebb6f526bf7547aef62c`。

### 修复版第二次：有限等待后

仅改 `sim/scripts/c01_status_onboard.py`：候选锁定后等待5秒再smoke，恢复原vision加载后等待5秒再smoke；`sim/vision/test_c01_status_onboard.py`核对等待在smoke和20秒窗口之前。初次PowerShell引号编辑失败，代码未应用；`board-probe-settle-offline.txt`是旧脚本测试，不作为新改动通过证据。正确应用后的证据是 `board-probe-settle-applied-offline*` 与 `python-entry-handoff*`。

对应 `reset-fix-settle-deployment.json`，remote `/home/xilinx/vision_m2/c01-8b4d42b3653c4c31a70626bf9a971abf`；最新脚本SHA `07e471caf2b8451968fe37c06da538f5ee67f094d90c4bf1af791f5898a56d94`。在板端新目录复制同一bit/hwh，校验SHA，再上传新脚本；没有覆盖首次脚本。

`board-c01-reset-fixed-settled-coexist/`实际结果：

- metadata、download、三个地址、起始DMA停止、CAP1、1280/720、视频锁定均通过。
- 等待后pipe配置号1帧首应答通过，进入20秒显示窗口。
- UVC窗口内24帧，1280×720BGR，PNG人工查看有真实场景；PNG SHA `4cfc0e5166f08f11c3a7c6daa5936d7615712977c70d4fce0e2d3be1e97f9fac`。
- host时间：WINDOW观察14:27:28Z，UVC结束14:27:34Z，确认早于cleanup。
- CSR快照：`{0x0:1128353841,0x4:3,0x8:1474,0xC:0,0x10:0,0x14:1280,0x18:720,0x1C:0,0x20:0}`。
- 探针现有规则要求“停止DMA时stream_seq=0”，此条件不成立；随后finally恢复原vision，等待5秒的smoke又NOVIDEO，SystemExit3掩盖了前一RuntimeError；串口/BOARD_EXIT=3，wrapper退出1。未得到CLEANUP成功标记。
- `faulthandler.dump_traceback_later(15,repeat=True)`在正常20秒sleep时输出两段Timeout栈；它是定时转储，不是65秒进程timeout，也不是CPU挂死证据。
- 后续独立最终smoke通过、活动路径原vision、boot不变、UVC正常；最终恢复已完成。

生成的实际顶层 `sim/build/c01-hdmi-1791713720540454/c01_hdmi.gen/sources_1/bd/vision/synth/vision.v` 已只读核对：VDMA `.s_axis_s2mm_tready`、VideoIn `.m_axis_video_tready`、status `.stream_tready`都接 `capture_input_video_out_TREADY`；其余AXIS数据/valid/user/last也同网。暂未发现监控ready接常量的证据。**还没有读取窗口结束后的DMA CR/SR；不能断言这20秒一直停止，也不能断言IP在停止时一定不接收流。**

## 6. 已验证的离板回归

- 25项视觉Icarus、Verilog-2001默认解析：通过。
- 整体25项XSim：`xsim-all-final.txt` / `xsim-all-final-exit.txt=0`；之前全tb被当Verilog编译的SV问题已改为仅选TB `-sv`，所有旧失败日志保留。
- 全项目 `run_iverilog.sh all`，含4种CoreMark CRC变体，退出0；当时Python为原8组。不要声称那次全回归包含后来11组。
- 最终11组Python统一入口，含UART接收器、诊断替身、复位8类负例：本轮 `python-entry-handoff.txt` / `python-entry-handoff-exit.txt=0`。
- 无本轮RTL修改，未重复跑已通过的全RTL回归。Git diff --check退出0；对新增未跟踪源码另检查空白，不把Git检查当覆盖所有新文件。

工具链：`C:/msys64/usr/bin/bash.exe`（普通bash会误入WSL stub）；PATH前加`C:/msys64/ucrt64/bin;C:/msys64/usr/bin`；`VISION_PYTHON=C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe`。XSim用`VISION_VIVADO_BIN=/d/Vivado_downloads/2026.1/Vivado/bin`，Vivado实际`D:/Vivado_downloads/2026.1/Vivado/bin/vivado.bat`。

## 7. 新对话建议的下一步

1. 先读AGENTS/workflow、当前README、捕获契约和这份交接，核对分支/未提交工作。快速模式仍有效；禁止因旧历史标题误判板卡还未恢复。
2. 优先小步完善诊断证据：记录开始及窗口结束时VDMA 0x30 CR、0x34 SR的实际数值；记录窗口起始和结束stream_seq。当前只做了起始RS=0/Halted=1判定，没打印数值，没有结束读数。
3. 查AMD PG020及实际VDMA源码/参数，确定RS=0/Halted=1期间TREADY/丢弃行为；重新核对生成顶层与路由网表的握手。**不要仅删除stream_seq=0断言来得到PASS。** 若停止通道本来允许消费/丢弃流，修改诊断判据必须有来源与实测支撑，仍明确没有DDR写完成证据。
4. 诊断脚本应分别记录主检查异常与恢复异常，避免finally抛SystemExit遮住主失败；改掉正常20秒wait也打印Timeout的转储方式。小步加有效替身测试，保留历史脚本版本和日志。
5. 用有界恢复策略等待视频帧首提交，不要盲目反复reprogram。5秒恢复等待这次仍不足；稍后通过只证明最终恢复，具体最短稳定等待未测定。NOVIDEO不能据此断言线缆或输入源坏。
6. 稳定显示/状态诊断之后才推进custom DDR：冻结安全的DMA写完成/错误、frame store交接、cache invalidate、独立完整副本和幂等释放；stream_seq不能替代该协议。再实测BGR颜色、整帧无混帧、HDMI共存与错误恢复。
7. C01整体还需核/CNN/PS接口等后续计划。正式数据与模型尚未具备，不跳过验收门。用户目前要换对话，本轮已经停止硬件试验。

## 8. 常用脚本与操作纪律

- `pynq_serial_console.ps1 -Port COM12`：用户登录xilinx、`sudo -v`自行输密码，按Esc释放；不要和其他UART任务并行。
- `pynq_serial_auth.ps1 -Port COM12`：已有shell的隐藏密码认证辅助；仅实际需要时请求用户操作。
- `pynq_serial_command.ps1 -Command <单行命令> -LogPath <仓库内新日志> -TimeoutSeconds N`：命令≤3000字节；超时124不意味着远程任务结束。
- `send_pynq_file.ps1`：只传新`/home/xilinx/vision_m2/c01-32hex/文件名`，gz/base64、rawUART、接收器xb拒覆盖、SHA重读验证；必须`timeout --foreground`否则TTY读取失败。短文件先测，大bit再传。部分raw传输失败要等180秒远端超时恢复TTY，不能立即复用COM12。
- `run_c01_status.ps1 -CheckOnly`核对命令长度；实际runner65秒远端timeout/85秒hosttimeout，保持VDMA停止，finally恢复原vision。
- `run_c01_status_coexist.ps1`：新OutputDirectory，观察WINDOW后UVC24帧，要求采集结束早于cleanup、board0/UVC0/CLEANUP/HOST0；当前第二次返回失败，应保留。
- `capture_uvc_raw.py --output-dir <仓库内新目录>`默认USB Video index1/24帧；“读取PASS”不代表内容正常，要看PNG/空间跨度。旧黑屏也是UVC读退出0。
- 原位流helper在板端`/home/xilinx/vision_m2/m2_onboard.py`；PC副本`sim/build/board_pkg_diagnostic/m2_onboard.py`。加载/查询/烟测需root环境source `/etc/profile.d/xrt_setup.sh`、`/etc/profile.d/pynq_venv.sh`。
- 新日志/部署目录使用新名称，不覆盖旧失败证据；不进行无证据的反复位流重载。若UART/MMIO又阻塞，先有限只读CPU检查并保留证据，再判断是否需要用户现场恢复。

旧 `outputs/c01-reset-fix-offline-bundle.zip` 是此前离线阶段快照（SHA `b8390d40b04cd39128495c35bce5d9f7a44984f7e30f7331ac81a8a11ca37c66`），不含本轮等待修改与实机结果。本轮新交接包另存，避免覆盖旧快照。仓库 `final-inputs/`同样是历史快照，不能覆写来伪造旧构建输入。
