# N03 缓冲保护与 C01 接手进展

基线dev/model@c292038；用户continue并要求主动接手阻塞依赖，沿用快速模式免题。
修改范围sim/scripts/、sim/vision/、data/logs/、docs/及report/llm_log/；未改RTL、板端PYNQ、Pi配置或已冻结接口，未commit/push。

## 本次修改与验证

n03_board_capture.py增加release_frame：cached pointer归还后把本对象标记freed，阻止析构再次munmap。
test_n03_buffer_lifecycle.py直接调用生产helper和已归档板端原函数：缓存帧不重复unmap、普通缓冲仍释放一次。
lifecycle-offline.log和capture-offline.log均退出0；后者覆盖五类取帧/失败/清理路径。
串口含完成标记2723/3000字节，serial-length.txt；Python/PowerShell语法与空白检查通过。

run_n03_coexist.ps1新增共存窗口观察/单进程COM12/UVC抓图及清理和退出码检查；
recover_n03_png.py新增串口PNG落盘校验，文件字节、PNG哈希及解码像素哈希全部一致才保存。
私有freed字段保护只针对本轮已核实的驱动路径；正式驱动须锁定版本并封装，不当成所有PYNQ版本通用修复。

## 实机结果

| 场景 | 模式/读取 | 取帧+复制单次耗时 | 实际结果 |
| --- | --- | --- | --- |
| input-only.txt | 1280×720/24bpp/60；2暖机+1副本+6连续帧 | 23.103ms | 非零图，输入close/清理完成，退出0 |
| coexist/board.txt | 同模式；9帧+20秒输出共存 | 23.821ms | 两路close/清理完成，板端退出0 |
| coexist-fixed/board.txt | 修复观察器后完整入口复验；9帧+20秒共存 | 23.942ms | 板端/主机/UVC退出0，清理完成 |

总计27次短时读取，不是长时间稳定性或端到端吞吐测试；本轮未再段错误、未重启。
boot_id在开始、恢复和最终检查中均为f3321177-d8ab-4db8-9c1e-04f9f0cfe40f。
独立副本shape=(720,1280,3)、uint8，DMA原stride=(3840,3,1)，BGR；保存后PNG回读像素一致。
coexist/ps-frame.png经串口传回986678字节：
PNG SHA256=800847432dea2d0874f5d54d2c196ec7a3dc2905cb6bff254b988c7cf5532654；
pixels SHA256=771eefbeca42f3132cbd8b687ac452f78f785af27ac721e46cb8a0fbca3f1c8c。
PS/UVC原图已人工查看，均为真实天花板、灯具和红线缆；未做色卡定标或逐帧关联。
首次窗口UVC_START_UTC=08:32:30.354、END=08:32:36.234，完成时尚无CLEANUP标记。
修正入口窗口UVC_START_UTC=08:46:52.968、END=08:46:58.429，同样早于清理。

首次观察器因Windows子进程ExitCode为空而退出1；原始host-status与console保留，不能说首次主机入口退出0。
固定进程Handle后，无硬件exit7探针通过；coexist-fixed完整实机入口随后退出0。
smoke-restored.txt的首版串接命令会由后续cat遮蔽失败码；保留原记录，使用&&的final-identity-and-smoke及最终恢复日志补正。

## 最终恢复

final-restoration.txt：load和smoke均PASS，&&传递失败码，远端退出0；pipe@0x40000000/64KiB，R12从0到1。
boot_id未变；bit/hwh哈希与原版本一致。uvc-final-restored/实际画面正常、24帧读取退出0。
最终UVC PNG SHA256=03743bfcc225b7a3a09d9f634a35620efd23c99b933bd3066d269ae6ba15bb4d。
串口已释放，板卡留在原vision配置；没有更改上游PYNQ驱动文件。

## C01 主动接手

新增validate_capture_subsystem.tcl构建PS/视频输入/VDMA/HP0/中断并做BD验证及真实参数读回。
最终subsystem-rgb-console.txt及.exit.txt=0，无WARNING/CRITICAL WARNING/ERROR；升级提示仅INFO。
stream=24、memory=64、frame_stores=4、MM2S=0、reset_high=0、RGB枚举2，控制0x43000000，IRQ_F2P[0]。
早期catalog日志含只读宽度设置警告，错误打印PASS不能算24位验证；已修正catalog入口语义并保留首次版本。
子系统首次未关闭多余PS AXI口导致缺时钟；一次修正有Tcl续行错误；格式0是YUV422使宽度断言失败。
全部失败日志/源快照保留，最终按本机component.xml的RGB=2修正后BD验证通过。
捕获实现基线见docs/c01-capture-implementation-baseline.md；4DMA帧+1PS副本预算13.184MiB。
这只证明离板连接/参数，未完成HDMI显示并联、字节适配、溢出/完整帧状态、综合/实现、bit/hwh或上板。

## 复现入口与未完成

```powershell
python sim/vision/test_n03_buffer_lifecycle.py
python sim/vision/test_n03_board_capture.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_n03_coexist.ps1 -Port COM12 -OutputDirectory "$PWD/data/logs/<new-run>"
```
最后一个会替换PL为base，结束必须按恢复流程回到vision；每次新目录，不同时占用COM12。
base软件取帧诊断子项通过；正式N03/C01未整体验收，动态无混帧、长时间、定标、断源及完整集成仍待验证。
CNN RTL、正式INT8、核/CNN/PS工业闭环及正式LIVE仍未实现/未验收；接下来直接补捕获溢出/帧状态与HDMI并联。


持久项目复验：subsystem-persisted-console.txt/exit.txt=0，BD和相同参数再次通过，无WARNING/CRITICAL WARNING/ERROR。生成xpr/bd路径见generation-layout.txt；入口自动创建sim/build内新项目。早期.srcs已核实为本轮生成物并完整保留到sim/build/c01-in-memory-srcs，未删除或覆盖既有项目。
