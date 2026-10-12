# 2026-10-11 现场续工记录

基线：dev/model @ c292038；时区Asia/Shanghai。
本次按用户明确接线继续N01/N02，并审查C01/N03；未改RTL/软件实现，未commit/push/切分支。
原有未跟踪的10/10日志、位流归档及串口/取帧脚本全部保留。

## 当前接线与环境

Pi与PYNQ均外部供电；Pi CM3→Pi HDMI→PYNQ HDMI IN→HDMI OUT→采集卡→电脑USB。
电脑USB串口COM12控制PYNQ；电脑网口连接Pi用于SSH。
主机枚举USB Serial Port(COM12)与USB Video均OK；COM12=115200/8N1/无流控。
板端uname/uptime/id/network/os/artifacts/environment/loaded八项均远端退出0。
PYNQ Linux 6.6.10-xilinx-v2024.1、armv7l；Python3.10.4、PYNQ3.1。
eth0 DOWN，配置169.254.87.99及192.168.2.99，不构成可用PYNQ网络连接。
PL.bitfile_name与timestamp均None，IP字典为base类元数据，不能据此推断实际PL配置。
bit SHA256=4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5。
hwh SHA256=c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5。
与10/10归档XSA内容一致；构建时源码快照追溯仍未闭环。

## 本次验证及原始输出

- baseline/*.txt：八项查询各有唯一完成标记与HOST_EXIT_CODE=0。
- sudo-check.txt：sudo -n true远端/执行器退出1，明确要求密码；尚未加载位流或访问MMIO。
- uvc-before-load-console.txt及.exit.txt：现有capture_uvc_raw.py退出0，USB Video索引1，24帧，MJPG/30报告，uint8[720,1280,3]。
- uvc-before-load/raw.png：实际黑屏；PNG像素回读一致仅证明抓帧/保存成功，不证明视频恢复。
- PNG SHA256=08f1c9deef07be2f994555c18b6471d4c876c89b23eaa5dcdc33f513b955b0fe。
- vision-python.log及.exit.txt：首次退出1，MSYS dirname/mkdir未在PATH中；原失败保留。
- vision-python-msys-path.log及.exit.txt：进程内补MSYS工具PATH后八组视觉回归退出0。
- inspection-python.log及.exit.txt：十三组离板检查回归退出0。
- 两组成功入口均沿用仓库vision_gate.sh：退出码0、含PASS且无FAIL/FATAL/ERROR诊断；网络WARN为既有断联测试预期。
- git diff --check退出0；本次新增文档为未跟踪文件，另对其空白行进行检查。

复跑入口（PowerShell，仓库根目录）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_pynq_baseline.ps1 -Port COM12 -OutputDirectory "$PWD/data/logs/<new-run>/baseline"
python sim/scripts/capture_uvc_raw.py --output-dir data/logs/<new-run>/uvc
$env:PATH = 'C:\msys64\usr\bin;C:\msys64\ucrt64\bin;' + $env:PATH
& 'C:\msys64\usr\bin\bash.exe' sim/scripts/run_vision_python.sh
& 'C:\msys64\usr\bin\bash.exe' sim/scripts/run_inspection_python.sh
```

## 下步与未完成边界

Codex内PowerShell终端已打开，用户需运行已有pynq_serial_auth.ps1并隐藏输入sudo密码；密码不入日志/聊天。
认证后核对缓存、boot_id，加载同一vision.bit，核对pipe地址，再smoke及UVC抓帧。
N03已有脚本未配置HDMI OUT共存；需按仓库古法编程先确认小步方案，再改脚本并验证。
C01草稿：[连接图、内存与接口审查](../../../docs/onboard-2026-10-11-c01-draft.md)。
N02完整冷启动/长时间/断源与采集卡共存未验收；本次未进行物理HDMI拔插。
N03 PS完整BGR取帧、输出共存及capture关联未验证；自定义原帧捕获未实现。
CNN RTL、核/视频/CNN集成位流、正式INT8、真实LIVE工业闭环均未实现/未验收。

## 认证后续工与N03故障（最新状态）

用户已完成sudo；authenticated-boot.txt远端退出0，boot_id=99577b4d-f0d4-4163-89f2-6231324b6fd8。
load-vision.txt与smoke-vision.txt均远端/执行器退出0，pipe=0x40000000/64KiB，R12由0到1。
uvc-after-load/：24帧读取退出0，真实室内天花板/灯具画面恢复；PNG SHA256=2319390c8152f2ab76ebb1543bd438bfa1678af68a3959928d4d33754314650a。
恢复后boot_id未变；这只证明同位流重载与短时相机链，不构成完整N02。

用户明确批准“快速模式，完成诊断并记录，免出题”；本轮免理解题，未commit/push。
随后修改sim/scripts/n03_board_capture.py：PIXEL_BGR、输入输出连接、唯一文件名、复制后释放、退出清理。
新增sim/scripts/pynq_serial_console.ps1用于重启后用户本人登录，不写文件日志；PowerShell语法通过，实际交互待用户验证。
新增sim/vision/test_n03_board_capture.py：四类离板故障测试入口，未更改既有视觉回归清单。

### 三个实际问题与证据

1. video-pixel-buffer-contract.txt：板端当前pynq.lib.video没有COLOR_BGR，原脚本导入不兼容；已改PIXEL_BGR。
2. n03-base-capture.txt：模式1280×720/24bpp/60，read_ms=22.755，完整uint8帧副本/PNG回读一致，远端退出0；
   串口取回并核对哈希后，n03-ps-frame-001.png全部像素为0，因此该次不算有效取图。
   板端PNG=/home/xilinx/vision_m2/n03-base-c29e8a3a84a14ab8a20b5c6b17d9051d.png，3947字节；
   SHA256=d18b6ed038c377e1b60de4ae5065fe2f67e0bbedccb9b74d25385d7aabd6930e。
3. n03-base-warmup.txt：延迟2秒后连续读到5帧，像素范围分别13–255、11–255、12–255、11–255、11–255；
   后续取帧不返回，90秒timeout打印monitored command dumped core，远端/执行器退出124。
   restore-after-n03-timeout.txt中恢复vision进程出现Segmentation fault、退出139；不能说原位流已恢复。
   n03-failure-state.txt保存同一boot_id、进程、dmesg及实际缓冲源码；未判定唯一根因。

主机共存窗口观察第一次使用ReadAllText时因共享模式失败；改Get-Content后，
板端没有达到COEXIST_WINDOW，观察器明确失败，未获得有效的同步UVC共存证据。
官方与本机VDMA源码要求重编程前停止全部DMA通道；超时/段错误后不能保证清理成功，
本次直接恢复加载失败，已改为软件重启恢复，不将该故障后重载作为正常操作范例。

### 恢复与脚本加固

reboot-after-n03-failure.txt：sudo systemctl reboot --no-block远端退出0，仅证明已受理重启请求。
reboot-console.txt为空；后续reboot-prompt.txt实际收到systemd启动输出，证明已开始新启动。
重启后的新boot_id、登录、sudo以及vision恢复尚待完成；已请求用户用串口交互入口登录并sudo -v。
请勿同时用两个进程打开COM12；登录/密码不放聊天或项目日志。

最终N03脚本改用readframe_async与asyncio.wait_for，每帧5秒超时；外层90秒仍约束加载/配置/停止。
该版本仅通过离板测试，尚未实机复验；不能声明修复了驱动/VDMA故障。
n03-offline-test.log及.exit.txt=0，覆盖复制后释放仍保留像素、全零帧拒绝、异步读帧超时、配置失败；
后两类不创建捕获文件，所有场景验证untie→out-close→in-close；是假驱动负例，不是硬件证据。
复现：python sim/vision/test_n03_board_capture.py。
原始版本与两次实机版本保留为n03_board_capture.before.py、.first-run.py、.timeout-run.py。

板端依赖：实际pynq源码来自/home/xilinx/pynq，OpenCV4.5.4、NumPy1.21.5、PYNQ3.1；
不能把另一路/usr/local/share/...的视频包源码当成实际已加载模块。
查询导出类名的两次失败（退出1）及对不存在hdmi.py的查询（退出2）全部保留；后续用实际hierarchies.py与dma.py核对成功。
base.bit SHA256=d9aec0ff1cddeaf109dd08b1510c2ed38b4804bd29ef7648ee80eac8f06de505；
base.hwh SHA256=94dee45319dfecb22d9684eb565916e62f910eb999650c9a99fda51bdc9158fe。

参考：PYNQ官方v3.1视频DMA源码 https://raw.githubusercontent.com/Xilinx/PYNQ/v3.1/pynq/lib/video/dma.py。
未完成：故障后恢复确认、N03有效PS原图/HDMI OUT共存、原帧捕获集成、CNN/核/LIVE闭环。


## 输入单独诊断与释放分支复现（2026-10-11补记）

用户回复ok后，authenticated-after-reboot.txt远端退出0，sudo缓存有效；
新boot_id=e1fcc6f5-cf8e-45bd-ba18-3c7eabffa1b2。
restore-vision-after-reboot.txt与smoke-after-reboot.txt均退出0，pipe地址/大小正确，R12由0到1。
uvc-after-reboot/成功读取24帧，实际天花板/灯具图像；PNG SHA256=
6976accf833dec649b39a6200a4900120847fce483bb2de5311db7b6b8867792。
这证明此前故障已经恢复；不代表本节后续故障后的最终状态。

本步修改sim/scripts/n03_board_capture.py与run_n03_board_capture.ps1，补InputOnly隔离、
明确close完成标记、2帧暖机/候选帧先保存/6帧连续读检查。
扩展sim/vision/test_n03_board_capture.py为五类离板测试，全部退出0；
n03-offline-input-only.log及.exit.txt记录，仅为假驱动检查。
修改前异步版本另存n03_board_capture.async-before-input-only.py。

### 本步实机失败

- n03-input-only.txt：base已加载，MODE=1280x720/24bpp/60；仅HDMI IN启动，未启动/关联HDMI OUT。
  两帧暖机范围均11–255，随后Segmentation fault，远端退出139；未输出候选PNG或任何close完成标记。
  因此不能只把失败归因于HDMI OUT共存；异步超时无法拦截本次原生崩溃。
- n03-input-only-fault-state.txt：同boot_id、内核/进程/实际源码已归档；没有遗留N03 Python进程。
  只说明进程退出，不证明DMA停止。板上已有apport旧崩溃文件为9月21日，未当作本次证据。
- n03-buffer-free-lifecycle.txt：实际freebuffer、缓存源码归档；git查询因板端源码无.git退出128，失败保留。
- n03-vdma-address-and-allocation.txt：实际base HWH确认VDMA@0x43000000/64KiB；_xrt_allocate直接复用缓存buf。
- n03-stop-dma-after-input-fault.txt：新sim/scripts/n03_stop_dma.py尝试仅停止、绝不重编程/分配帧。
  确认CURRENT_BIT为base后，PL.ip_dict查询在垃圾回收阶段发生段错误，远端139；
  崩溃栈为/home/xilinx/pynq/pl.py的dict_views/ip_dict。失败在MMIO构造之前，未进行停止写入。
  因此该工具未取得硬件通过证据，不能以它的存在宣称DMA已停止。
- reboot-after-input-only-fault.txt：软件重启请求受理、退出0。最终恢复需重启后重新认证、加载vision及UVC复验。

### 可复现的代码分支与根因边界

实际PynqBuffer.__del__再次调用freebuffer。第一次cached pointer归还后pointer=0且freed仍False；
第二次进入munmap分支；VDMA缓存复用同一buf存在生命周期风险。
sim/vision/test_n03_buffer_lifecycle.py直接提取已归档板端函数，用无副作用munmap spy复现：
n03-buffer-lifecycle-offline.log及.exit.txt=0；cached对象归还一次，第二次释放调用munmap。
离板候选freed保护能阻止第二次unmap，但这只证明分支，不能等同于原生段错误唯一根因。
没有修改/home/xilinx/pynq或系统驱动；候选保护没有集成到正式取帧入口或实机验证。
内核/驱动/CMA及其他原生内存问题仍须进一步定位；当前入口保留用于复现，不视为稳定采集工具。

runner增加-X faulthandler与timeout -k 5s 90s，避免TERM后进程永久存活；
这不保证DMA停止，也不能把退出码0或非零像素当作完整N03验收。
本步没有HDMI物理拔插，没有更改Pi配置、RTL或主计划验收状态，没有commit/push。
快速模式免出题沿用用户明确授权。

复现离板检查：
```powershell
python sim/vision/test_n03_board_capture.py
python sim/vision/test_n03_buffer_lifecycle.py
```
实机InputOnly复现入口（仅在规划恢复方式、认证及当前状态确认后使用，不建议立即重复）：
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_n03_board_capture.ps1 -Port COM12 -InputOnly -LogPath "$PWD/data/logs/<new-run>/n03-input-only.txt"
```
每次新日志/新图目录；COM12仅单进程占用。正式N03仍未通过，C01仍未冻结；
原彩色帧捕获集成、正式INT8/CNN/核/LIVE链路仍未实现/未验收。

串口无硬件预检：run_n03_board_capture.ps1 -InputOnly -CheckOnly，含完成标记共2539/3000字节；n03-serial-length-check.txt记录。最终脚本哈希见n03-final-script-hashes.txt。


## 最终恢复确认（2026-10-11 16:52 CST）

用户完成第二次重启后的登录/sudo并释放COM12；authenticated-after-final-reboot.txt退出0、AUTH_OK。
新boot_id=f3321177-d8ab-4db8-9c1e-04f9f0cfe40f，与上一启动不同。
restore-vision-final.txt：原vision加载退出0，pipe@0x40000000、range=0x10000，PASS: load。
smoke-vision-final.txt：退出0，R11 busy=0、R12 applied由0到1，PASS: smoke。
uvc-final-restored-console.txt与.exit.txt：退出0，USB Video索引1，读取24帧，uint8[720,1280,3]。
uvc-final-restored/raw.png实际显示天花板、灯具与线缆，已人工视觉检查；PNG逐像素回读一致。
PNG SHA256=939c00823d2527cc39cc97aad73cb5dc95ade4318efa4723c286ebe729953ec3。
final-restored-identity.txt：退出0，boot_id仍相同、FPGA manager为operating，bit/hwh指纹与原始版本一致：
bit=4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5；
hwh=c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5。

本节取代此前“最终恢复待认证”的状态：本轮故障后的原视频链恢复已确认，串口已释放。
本步仅补data/logs/、docs/与report/llm_log/记录，没有修改采集脚本、板端驱动、RTL或Pi配置。
git diff --check与新增记录空白检查通过；未commit/push，沿用用户快速模式免出题。
N03仍未通过；重复释放候选仅离板验证、唯一根因尚未确认，未继续加载base。
C01仍未冻结，完整N02、正式原帧捕获/INT8/CNN/核/LIVE集成仍未完成，不把恢复成功替代这些验收。


## 后续缓冲保护与C01进展

局部释放保护后base单输入/共存27帧短测通过，取得有效PS完整PNG及UVC共存证据，原vision再次恢复且boot_id未变。正式N03未整体验收。C01捕获子系统离板BD验证通过；详细新记录见../2026-10-11-n03-buffer-guard/README.md及docs/c01-capture-implementation-baseline.md。
