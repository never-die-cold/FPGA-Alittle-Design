# HDMI 诊断显示证据（2026-10-07）

功能分支 `codex/pi-hdmi-diagnostics`，基线 HEAD `0669960`；本记录随诊断显示交付提交。
用户授权十步连续执行、末尾三题；既有相机文档、服务、密码重置脚本等改动保留。

## 状态与证据

- ✅ 四视图 RTL、帧首切换、循环行缓存及半帧复位屏蔽：仓库 tb 可复现。
- ✅ 板端 CLI 与参数保留；新 bit 已装载，四图和切回原图实际采集成功。
- ✅ 完整统一 all 退出0、70行PASS；本目录 all-complete.log 为最终执行的原始输出。
- 🟡 补充74.875秒/1800帧采集无全黑帧；真实拔线已实测，但自动恢复失败，手动恢复流程已验证。
- ⬜ 未实现：PYNQ 开机自动装载、CNN、自动定位、DDR 显示对照。

## 原始命令与结果

| 入口 | 日志 | 结果 |
|:---|:---|:---|
| `run_iverilog.sh all` | all-complete.log、final-check.txt | exit0、70行PASS；含四档CoreMark、视觉与Python检查 |
| `run_iverilog.sh vision all` | vision-final.log | exit0，28 tb、29 PASS；含 720p8帧/7372800像素 |
| `run_vision_xsim.sh diagnostic` | diagnostic-xsim.log | 4项 PASS（标准时序重跑） |
| `run_vision_xsim.sh diagnostic_reset` | reset-xsim.log | 1项 PASS，帧中复位/半帧/双 VS 极性 |
| `run_vision_xsim.sh axi_lock` | axi-lock-xsim.log | 1项 PASS，ENABLE_DIAGNOSTIC=1 在途 AXI 不受失锁影响 |
| `run_iverilog.sh vision axi_lock` | axi-lock-diagnostic.log | PASS，诊断参数开启 |
| `run_iverilog.sh vision_python` | python-final.log | 6组入口、8行 PASS |
| `iverilog -g2001 -s vision_axi -Pvision_axi.ENABLE_DIAGNOSTIC=1 ...` | verilog2001-full.log | exit0、PASS，综合 RTL 无 SV-only 依赖 |
| `run_vivado_hdmi.sh`（独立 OUT/EVDIR） | hdmi/driver.log | PASS，路由/bit/XSA 完成 |
| `make_board_pkg.sh sim/build/hdmi-diagnostic/vision.xsa` | package.log | PASS、ZIP/manifest 齐全 |
| `pynq_uart_send.ps1` | uart-transfer.txt | 239135字节、SHA256和文件哈希一致 |
| `m2_onboard.py load` | serial-load.txt | PASS、pipe @0x40000000、板端 exit0 |
| `display_view.py --view ...` | serial-color/gray/gauss/edge.txt | R12=1/2/3/4、R0=0/16/17/25、exit0 |
| `capture_hdmi.py --source 1 ...` | capture-*.log、*.json | 每模式24帧、1280×720/MJPG/约30fps、exit0 |
| `display_view.py --view color` 回切 | serial-restore-color.txt | R12=5、R0=9，清bit4且保留高斯/Sobel |
| 回切抓帧与开预览 | capture-restored-color.log、preview-restored.txt | 24帧成功，PID44064，窗口 M2 vision preview |
| 连续采集 | capture-stability.log、stability-color.json | 1800帧/74.875秒、black_frames=0、min_luma_std≈79.79 |
| 连续采集后再开预览 | preview-final.txt | 最终预览进程身份与窗口记录 |
| HDMI IN 拔插诊断 | hotplug-*、capture-card-*、post-pi-reboot-* | 拔后NOVIDEO；首次重插出现冻结花屏；按标准时序恢复流程后24帧0黑且首末帧不同 |

XSim 沙箱内首跑无法获得许可；允许本机进程后成功，失败保留 xsim-sandbox-failure.log。
统一 all 首次遇核声明使用在前、声明在后；all-before-declaration-fix.log 保留失败。
移动两个声明后 CoreMark 第一档 PASS；随后修改运行中的脚本补入口导致 EOF，
all-final.log 保留此中断。停止修改执行脚本，语法检查后从统一入口重跑 all-complete.log。
最终 all 中的 injected FAIL/ERROR/FATAL 属于 gate 自测的预期拒绝案例，8例判定PASS。
CoreMark 四档按既有 tb 的 CRC/tohost/退出条件判定PASS；固件原始观测仍打印 errors=1，
不将其描述为固件零错误，本次未改变该判定口径。

## 物理实现与已知报告项

WNS +0.408ns、TNS0、WHS +0.025ns、脉宽余量 +0.264ns，所设约束全部满足。
LUT4372、FF5488、BRAM50.5/140、DSP0；完整报告在 hdmi/ 下。
DRC 无 Error/Critical Warning 阻断项，保留 RAM 输出寄存/异步控制等 Warning。
CDC 仍有 Digilent RX 内既有3个 CDC-7、2个 CDC-11 Critical，端点与
2026-10-02基线相同；不能描述为 CDC 零告警。新增显示逻辑只在像素时钟域。
配置保持总线沿用 max_delay datapath_only；本次增加 bit4 的有效配置位。

## 实机画面

| 模式 | 最后原始帧 | 灰度均值 | B/R平均差 | 拉普拉斯方差 |
|:---|:---|:---|:---|:---|
| 彩色 | [color-last.png](color-last.png) | 130.35 | 38.33 | 3989.52 |
| 灰度 | [gray-last.png](gray-last.png) | 129.82 | 0 | 4238.01 |
| 高斯 | [gauss-last.png](gauss-last.png) | 128.98 | 0 | 426.85 |
| 边缘 | [edge-last.png](edge-last.png) | 45.94 | 0 | 21421.48 |
| 恢复彩色 | [restored-color-last.png](restored-color-last.png) | 131.91 | 41.95 | 4017.48 |

这些是同一 USB Video 的实际 HDMI 输出；脚本不生成滤波图。先丢30帧旧缓存，再取24帧。
画面是相机对着的椅子、包、织物等；高斯平滑纹理，边缘显示轮廓。照片先后采集，
不当作固定输入逐像素硬件黄金对拍；该口径由独立参考 tb 承担。
30fps 是 USB 协商结果，不能替代输入 HDMI60Hz 的时序证明。
连续采集在R0=9（彩色显示，高斯/Sobel分析开启）运行；统计处理时间包含在74.875秒内，
不把协商30fps或1800次成功read当作硬件帧率/无丢帧测量。

## HDMI IN 拔插恢复

开始拔插测试时物理链为黑屏，首次抓取为24个黑帧；该失败保留在hotplug-before.*，
不冒充正式基线，也不据此推断具体原因。重新加载已校验bit并切至COLOR后，正式基线24帧、
黑帧0、最小灰度标准差69.03。拔掉树莓派到PYNQ HDMI IN后，采集卡仍返回24帧，
但全部纯黑；板端commit返回NOVIDEO(exit3)，同时AXI寄存器仍可读。

重插同一根线后，R12一度恢复确认且抓取24帧非黑，但随后实时预览暴露左半幅紫白噪声。
异常原始帧在重载bit前后四张PNG哈希完全相同，证明采集卡冻结并重复损坏帧；此前“自动
恢复成功”的初判作废。仅拔USB不足以掉电；同时拔USB和采集卡HDMI后冻结帧清除，OUT变黑。

树莓派此时报告HDMI-A-1 disconnected，并退回1280×720@59.97、74.440MHz、总时序
1664×746；这不符合诊断bit限定的CEA 720p60 1650×750。虽然cmdline已有
`video=HDMI-A-1:1280x720@60D`，无有效EDID时该强制模式仍未产生目标CEA porch。
在PYNQ bit已加载的条件下重启树莓派，重新取得EDID后恢复connected、74.250MHz、
1650×750；随后再次加载同一bit并切COLOR，最终抓取24帧、黑帧0，首末帧SHA256不同，
目视无花屏。结论：AXI失锁隔离通过，但当前系统不支持无需干预的HDMI IN热插拔自动恢复。

## 文件身份与回退

新bit SHA256：`e90ddde20f3340b383098744eed8a1863ba34d94ae73cb10836164974bf057ff`。
新hwh：`acdec6183aeefdbe3fa593c2fc241d8ab6bb47505b549e9bbf4d92ee496ed8b7`。
板端原bit：`4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`，仍在 `/home/xilinx/vision_m2`。
本地旧bit：`38f24077254fc73efec275e34face61a061d41f6c2fa205a04a52c8e96e42b17`，仍在 sim/build/hdmi-project。
新工程 sim/build/hdmi-diagnostic，新包 sim/build/board_pkg_diagnostic，板端 `/home/xilinx/vision_diag`。
生成物不入库，manifest带各文件哈希、HEAD及dirty标记；实际回退操作见 docs/pi-pynq-display-runbook.md。

用户已回答三题、核心理解通过，并明确请求commit；完整答案及精确口径修正见本轮llm_log。
`git diff --check` 退出0、无输出；拔插后的新增检查结果见本节和对应原始日志。
