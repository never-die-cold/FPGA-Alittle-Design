# C01 捕获状态接口：实现候选 v0.1

初稿2026-10-11，原基线dev/model@c292038；源码已随PR #69合并，当前整合基线3e2e1c9。本文仍为捕获接口候选，不替代已冻结pipe参数，也不证明DDR帧槽所有权，最新验收边界见[C01基线](c01-capture-implementation-baseline.md)。

显示保持 RX→vision_axi→TX；原彩色捕获并联到 RX。采集 FIFO/VDMA 的反压只影响捕获支路。
首版 1280×720、单像素24位；Digilent R,B,G 转为总线高到低 R,G,B，DDR 低地址顺序 B,G,R。
VDMA S2MM 4帧存储、64位HP0；MM2S关闭。VSYNC/HSYNC来自真实HDMI时序，消隐未新增时间戳。

## 地址与只读寄存器

pipe 0x40000000/64KiB保留；状态0x42000000/64KiB；VDMA0x43000000/64KiB。
状态块所有写返回SLVERR，允许AW/W先后到达，响应背压时保持；未定义/未对齐读返回0+SLVERR。

| 字节偏移 | 含义 |
| --- | --- |
| 0x00 | 标识0x43415031（CAP1） |
| 0x04 | bit0锁定、bit1正在跟踪帧、bit2溢出故障仍保持、bit3曾有错误；其余0 |
| 0x08 | stream_seq：完整像素流计数，32位自然回绕 |
| 0x0c | rejected_frames：监测中途作废的帧计数，包含几何错、提前SOF、溢出和断源 |
| 0x10 | error_epoch：错误事件计数，同拍多种错误合并一次；同一保持溢出仅记一次 |
| 0x14/0x18 | WIDTH/HEIGHT（首版1280/720） |
| 0x1c | overflow_intervals：跨域请求/确认期间的溢出会合并，不是逐脉冲总数 |
| 0x20 | lock_losses：同步锁定信号的下降沿计数 |

## 帧完整性与故障

仅TVALID&&TREADY接受的像素推进计数；TUSER是首像素SOF，TLAST必须恰好落在每行第WIDTH个像素。
恰好HEIGHT行才增加stream_seq。半帧提前SOF使旧帧作废并从新SOF重新跟踪。
几何错、溢出或失锁作废当前跟踪；忽略后续孤立像素，等待锁定和故障解除后的下一SOF。
同拍故障优先于帧尾，禁止把故障帧计作完整。监测器不截断/修改AXIS，不产生显示反压。
rejected_frames统计已经开始跟踪而作废的帧；无锁/故障期间未开始跟踪的原始帧不保证逐帧计数。

Video In异步模式的overflow由写端像素时钟产生（已核对本机5.0.8 coupler源码）。
像素域先保持pending，AXI域同步并确认，源端收到确认且故障消失后清除。源时钟停摆不会清掉pending。
两个同步方向均2FF+ASYNC_REG，例外只约束第一级D；像素复位异步断言、两拍同步释放。
状态AXI、VDMA和控制总线使用FCLK0同步释放的PS复位；失锁不复位状态总线或历史计数。

## PS必须遵守的使用边界

stream_seq仅说明接受到的像素流具有完整几何，**不表示DDR写响应完成或某个缓冲已归PS所有**。
当前监测状态没有逐帧槽号/stream_seq与VDMA槽的原子绑定，不可单独作为“此DDR帧有效”的凭据。
PS适配仍未实现：必须核对VDMA帧完成、错误、当前写槽和缓冲交接，invalidate并复制独立副本。
读取状态采用前后error_epoch/stream_seq复核；中途变动、溢出、失锁或VDMA错误时拒绝结果。
发生故障须停止/复位捕获DMA、清理帧所有权并重新等待完整帧；不能靠显示仍有画面判断捕获安全。
CTR状态多次读取不是原子快照；计数器回绕和复位须与boot/overlay实例标识一起处理。

## 验证与尚未完成

仓库统一入口：run_iverilog.sh vision capture_monitor / capture_status / all。
测试覆盖几何、握手暂停、故障帧尾优先、下一SOF恢复、CSR背压/分离写、颜色字节和像素停钟/失锁。
整体BD入口：build_capture_hdmi.tcl -tclargs validate；离板构建：-tclargs bitstream。
每次创建sim/build内独立新工程和data/logs内新报告，保留原显示位流；不会打开硬件目标。
尚未完成：PS缓冲所有权、真实DDR颜色/动态图像对拍、断源恢复/长测，以及核/CNN集成。

接口标注依据：[AMD UG994支持的X属性](https://docs.amd.com/r/2025.2-English/ug994-vivado-ip-subsystems/List-of-Supported-X_-Attributes)。
AXIS使用monitor模式，整体接口连接旁路观察；像素复位显式标注高有效，避免名称推断错误。
