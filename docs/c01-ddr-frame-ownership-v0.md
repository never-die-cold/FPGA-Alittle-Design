# C01 custom DDR帧槽所有权：NC交接候选

2026-10-13，基线 `3e2e1c9`。状态：**单帧 PS 适配已实现并通过离板异常测试，待WC/JL评审与NC实机确认**；完整 custom DDR 帧尚未取得，驱动序列未冻结。
依据：[捕获CSR](c01-capture-status-contract.md)、[实现基线](c01-capture-implementation-baseline.md)、[停止期实测](../data/logs/2026-10-11-c01-probe-evidence/README.md)、[C03](coprocessor-integration-v0.md)。不新增CAP1寄存器或LIVE报文字段。

## 1. 已有硬件与证据能力

| 项目 | 当前事实/限制 |
|---|---|
| 数据流 | 1280×720，24bit；预期DDR低地址B/G/R，行3840字节，帧2,764,800字节 |
| 存储 | VDMA S2MM、4帧、HP0 64bit；4 DMA缓冲+1PS副本13,824,000字节 |
| CAP1 | stream_seq=握手几何完整；无完成槽号、无写响应完成、无槽/序号原子绑定 |
| 停机 | RS=0/Halted=1时仍可握手丢弃；20秒SEQ增加1200不是DDR完成证据 |
| 错误 | 停机可留下SR粘滞错误；启动前复位/清理并读回，采集中新增错误必须拒绝该帧 |
| 显示 | 原vision显示支路独立；UVC可见不证明捕获安全，UVC帧不代替本轮capture |

## 2. 首版候选：先证明槽不再被写，再复制

建议先做有界单轮捕获与停止后复制，以便验证所有权；连续自由环绕取帧留到可证明保护协议后。
**停止命令、Halted、frame IRQ、当前槽索引中的任意一个，单独都不足以授权PS读取整帧。**
WC适配必须给出实际IP/驱动依据，证明：目标槽确实完成一整帧、相关写事务完成、该槽在整个invalidate/复制窗口不会再被DMA重用。
若只靠软件“上一槽”推算，而硬件继续4槽环绕，PS慢于一圈时会读到混帧；Python锁不能阻止DMA覆盖。
若现有IP无法可靠绑定完成事件与稳定槽，先报告缺口，评审停帧/停机/地址轮换等机制；不得用stream_seq补猜。

```text
空闲/待装载 → DMA写入 → 已完成且受保护 → PS持有 → 独立完整副本 → 归还
                  └─ 错误/失锁/复位/超时 ─→ 无效，禁止发布结果
```

以上是逻辑所有权状态，不声称现有VDMA已经实现保护或状态机。

## 3. WC交付适配时必须说明的操作顺序

1. 记录boot/overlay实例、位流/驱动/脚本版本；读取几何、CAP1和VDMA初始CR/SR，验证后台没有其它捕获所有者。
2. 分配四个有效DMA地址，记录物理地址/大小/stride/缓存属性；存活期间不得free或让其它模块覆盖。ROI与结果区避开捕获区。
3. 按已核对的IP规则复位/清理错误并读回；重新等待锁定及完整帧起点，不能沿用复位前的计数或完成标记。
4. 有界启动/等待；明确完成事件、槽号、来源帧及事务完成屏障的实际对应关系。超时/失锁/错误只产生失败证据。
5. 建立该槽的硬件写保护窗口，确认数据写完后对正确内存范围执行缓存同步/invalidate，再复制完整BGR到独立PS内存。
6. 复制前后复核实例、完成/写保护证据、CAP1 error_epoch/锁定和VDMA错误；变化则丢弃副本。SEQ改变只作诊断，不能替代完成条件。
7. 副本通过shape/dtype/stride/完整字节检查后落PNG及像素哈希。只有独立副本可供定位/ROI/服务，不能向下游泄漏DMA可重用视图。
8. 成功与失败路径均按所有权归还/关闭；同一个租约重复释放不得二次归还或释放原生内存。恢复失败单独记录，不能遮住主失败。

停止后写事务完成、IRQ/槽对应及cache调用细节必须由实际实现提供；本文不发明寄存器位或“等待固定几毫秒”作为完成屏障。
实例重载/复位时生成新会话/代次；旧槽、旧租约、旧check结果全部失效。clear错误不使先前损坏帧重新有效。

## 4. 局部追溯元数据（不扩展LIVE协议）

| 字段 | 要求 |
|---|---|
| 实例/版本 | boot_id、overlay代次、bit/hwh/脚本/驱动SHA256、模型/预处理版本 |
| 轮次 | session_id/check_id/config_id、软件capture序号；frame_id不冒充cop_frame_id |
| 硬件证据 | 完成事件及对应槽、DMA地址/尺寸/stride、写保护与事务完成依据、前后CR/SR/CAP1 |
| 副本 | 完整BGR尺寸、像素/PNG SHA256、取帧/等待/缓存同步/复制分别计时 |
| 失败/释放 | 超时/错误/失锁/复位原因、是否复制/发布、归还次数、恢复结论 |

元数据写入本地采集/检查产物；HTTP若需要新增字段，另走C04版本评审。失败捕获不生成正常检查结果或有效批次。

## 5. 离板替身与NC实机验收矩阵

| 用例 | WC/JL离板检查 | NC返板证据 |
|---|---|---|
| 正常帧 | 完成/保护/缓存同步/复制/归还顺序与唯一租约 | 完整原PNG、真实BGR色卡、独立副本不随下一帧变化 |
| 未完成/在写槽 | 拒绝读取或发布；不把IRQ/SEQ当所有权 | 动态标识逐行/整帧一致，慢复制无混帧 |
| DMA错误/失锁/超时 | 不发布、正确释放，恢复异常独立保存 | 原始CR/SR/CAP1、恢复后重新等完整帧 |
| 重载/复位 | 拒绝旧代次租约、旧完成标记/旧结果 | boot/overlay代次及新会话关联 |
| 复制/PNG/下游异常 | DMA缓冲恰一次归还，文件原子发布 | 故障记录、DMA停止/释放、原vision恢复及UVC内容 |
| 缓冲环绕/背压 | 无可用槽时有界等待或拒绝，禁止覆盖PS槽 | 持久运行、错误统计、地址/内存稳定与HDMI共存 |

`src/pynq_host/c01_capture.py` 实现 park slot 0、FrameCntEn/IRQFrameCount=1 自动停机、完成/槽/描述符/代次复核、缓存 invalidate、独立完整副本与幂等关闭。依据 [PG020 S2MM 控制](https://docs.amd.com/r/en-US/pg020_axi_vdma/S2MM_VDMACR-S2MM-VDMA-Control-Register-Offset-30h)及[状态](https://docs.amd.com/r/en-US/pg020_axi_vdma/S2MM_VDMASR-S2MM-VDMA-Status-Register-Offset-34h)，完整转移后自动清 RS，Halted 只在通道完全停止后确认；人工 stop 仅用于异常释放，不授权正常发布。

`sim/vision/test_c01_capture.py` 的七组离板测试覆盖 IRQ 先于停机、无 IRQ/错误槽/描述符变化/失锁/超时、分配/缓存/释放失败、复制期间源变化和未确认停机时的缓冲隔离；入口 `bash sim/scripts/run_vision_python.sh`。未确认停止时持有原生缓冲且板端进程保持存活，禁止析构释放或重载 overlay。

`sim/scripts/c01_ddr_onboard.py` 提供候选哈希/地址校验、实验与原 vision 恢复。两次实测均在 DMA 启动前失败并恢复：首次配置前清理粘滞错误失败，第二次 HDMI 未就绪；最终配置顺序与等待修正仅离板验证。2026-10-13 用户要求转为离板任务，未继续板端复测。[原始证据](../data/logs/2026-10-13-ddr-single-frame/README.md)。完整帧颜色、无混帧、持续运行和 N03 矩阵仍待实机。

## 6. 交接门

WC给出实际完成/槽绑定/保护/屏障/cache依据与仓库替身入口，JL确认集成位流/地址/复位兼容，NC才能安排custom N03实测。
随后再做真实工位定标/采集、同帧ROI与软件/硬件对拍。C01整体冻结及正式N03通过仍需这些证据。

## 7. WC 适配与离板评审注记（2026-10-13）

**适配件**：`src/pynq_host/c01_backend.py`（`C01Captures`）把 `SingleFrameCapture` 接进
`vision_live_service`——一轮 = 一个单次租约（factory 现场构造 owner，`capture()` 返回独立完整副本），
适配器立即编码 PNG 原子落盘，服务统一写 `capture.sha256`；捕获/引擎失败由服务转 **503**
（`do_POST` 捕获 RuntimeError），失败轮不写 `packet.json`。`prototype` 由后端结构性决定：
C01 = 真实硬件捕获 → **False**（FILE 后端恒 True，[C04 §3.2](vision-live-semantics.md)）。

**仓库替身入口**：`sim/vision/test_c01_backend.py`（接入 `run_vision_python.sh`）——最小
VDMA/CAP1/分配器/代次 fake 驱动真实驱动（`src/pynq_host/c01_capture.py`），服务级覆盖 §5 矩阵
离板行：正常帧与独立副本（缓冲换帧后上轮产物不变）、等待期 DMA 错误/完成超时 → 503 且无产物、
缓冲恰一次归还、采集期代次变化 → 拒绝发布且原生缓冲隔离（不归还）、新代次恢复、无 `.pending` 残留。

**§3 八步操作序 → 实现位置**：1 实例/版本 = identity + evidence；2 四缓冲分配/不重叠/几何 =
`capture()` 分配段；3 复位/清错/读回 + 重新等锁 = reset/clear 段；4 有界启动/等完成 = CR RUN +
VSIZE 最后写 + `completed()`；5 写保护窗口 = auto-stop（PG020：完整转移后硬件清 RS）+ PARK/描述符
复核 + invalidate + `np.array(copy=True)`；6 复制前后复核 = `_protected()` before/after，变化即丢弃；
7 副本几何复核 + 落盘哈希（适配层 + 服务）；8 归还/幂等 = `close()` 恰一次释放 + `QUARANTINE`
隔离未确认停止。

**尚未由离板验证、实机确认前不得宣称的硬件断言**：① "停止后写事务已完成"依赖 VDMA auto-stop 语义
与 invalidate 调用——需 NC 用动态标识逐行/整帧一致实测（§5 行 1/2）；② park slot 位域复核替代
"完成槽号绑定"（CAP1 无槽号，§1）属候选序列，**实机确认前不冻结**（§6 交接门）；③ 唯一在途租约由
"单次对象 + 单轮构造"结构性保证；板上进程存活与禁止析构释放按 §5 尾注执行。JL 需确认集成位流/地址/
复位兼容后，NC 方可安排 custom N03 实测（§6）。
