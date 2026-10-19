# N03 custom DDR返板执行单（2026-10-14）

基线 `dev/model@5654eb5`；本轮仅离板复核，最终驱动尚未实机成功取帧。本单供NC返板时执行，当前不签N03/C01通过。
离板准备已完成：三份执行源码精确快照/指纹、既有专项、候选产物配对及98项输入审计；[本轮证据](../../data/logs/2026-10-14-n03-return-review/README.md)。

## 1. 版本与进入条件

| 项目 | 本轮核对事实 / 返板动作 |
|---|---|
| 候选产物 | sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.{bit,hwh,xsa}；哈希及地址见证据candidate-artifacts.json，XSA内嵌bit/hwh与独立文件一致 |
| 构建输入 | 98项严格匹配；当前96项同字节，build_capture_hdmi.tcl/run_c01_capture.ps1两项包装改动；不据此代签bit-to-source或板上运行版本 |
| 实验源码 | evidence inputs/中的c01_capture.py、c01_ddr_onboard.py、c01_status_onboard.py；runner-inputs.json逐文件SHA/长度，上传到同一个新的独立目录 |
| 板端依赖 | PYNQ/NumPy/OpenCV、XRT环境及原vision目录m2_onboard.py/vision_regs.py；记录实际版本/字节SHA，与本机观察分开，差异先核对不直接覆盖 |
| 原vision | /home/xilinx/vision_m2/vision.bit及同名hwh；使用入口固定期望哈希，boot_id、PL路径、smoke与UVC内容必须本轮重新确认 |
| 所有权 | 无其它捕获进程；flock仅约束遵守同一锁的调用者。WC/JL完成候选驱动与位流/地址/复位兼容评审后进入实测 |

## 2. 首次实验步骤

1. NC返板后先只读核查boot_id、PL路径、位流/脚本哈希、真实相机模式及设备；原vision load/smoke/UVC确认基线。
2. 使用新的板端目录上传三份执行源码，逐字节SHA与runner-inputs.json核对；bit/hwh单独配对核对，不复用旧失败目录。
3. 在板端既有XRT/PYNQ环境中，将C01_BIT设为本轮已核对的候选bit绝对路径，执行该新目录的`python3 -u c01_ddr_onboard.py`；全量输出和退出码归档。此命令会操作PL/DMA，本轮未执行。
4. 入口先核对原vision/候选哈希及活动PL，下载前检查HWH三段地址；候选DMA须空闲、CAP锁定及有界smoke通过。
5. 单轮捕获须留下fresh IRQ、自动RS=0/Halted=1、slot0、地址/几何、boot/overlay实例及前后CAP错误证据；stream_seq不是DDR完成凭据。
6. 检查独立720×1280×3 uint8 BGR副本、strides=(3840,3,1)、2,764,800字节；PNG回读像素一致并保留PNG/像素SHA。
7. 原vision恢复load/smoke通过，boot_id不变，UVC实际内容正确；主失败与恢复失败分别记录。完成这一轮仅算单帧实验，后续逐项验收。

## 3. 异常处理

入口若报UNSAFE-STOP，保持板端进程与原生缓冲存活，禁止强杀/自动退出或重载overlay；由NC在场按复位恢复流程处理并保留证据。
`pynq_serial_command.ps1`主机超时124只表示远端完成未确认，不发送中断；不能据此释放缓冲或另开捕获。
`run_c01_status.ps1`是停止DMA的显示诊断，带timeout -k；不能将其强制超时包装套到DDR捕获入口。
入口main仅做离板语法检查；现有tb覆盖驱动及helper，完整main/PNG失败/进程保活的端到端替身覆盖仍缺，不能把七组驱动测试扩大为整入口验证。

## 4. N03必须另留的实机证据

| 用例 | 通过条件 |
|---|---|
| 颜色/完整帧 | 同一capture色卡与真实场景，实际B/G/R通道、边界与整帧无缺行；非全零不等于颜色正确 |
| 动态/慢复制 | 动态帧标记逐行一致；下一轮后旧副本SHA不变；仅本轮软件复制耗时不证明无混帧 |
| 失败/恢复 | 失锁、错误、超时、重载等拒绝发布；释放/隔离及原vision恢复均有证据，不能仅看PASS字符串 |
| 持续/共存 | 按用例记录预先约定时长、循环次数、错误/内存及HDMI OUT/UVC内容；未测不填0 |

统一记录：case/backend、实际版本、boot/PL实例、输入及动作、CR/SR/CAP/槽证据、副本与耗时、释放/恢复、退出码和人工判定。
未完成：完整custom实机N03、完整N02恢复/长测、N04定标/N05正式采集、真实LIVE后端与整机CNN/核判定。base历史27帧诊断不能代签custom。
