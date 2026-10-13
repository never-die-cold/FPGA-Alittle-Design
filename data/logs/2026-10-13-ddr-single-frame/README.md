# C01 单帧 DDR 驱动与失败实验（2026-10-13）

基线 `3e2e1c9`，`dev/model`，未提交。用户先选择 CNN MAC，后要求快速模式、理解题留到最后；最新要求当前只做离板事项。

**结论：PS 单帧适配与七组离板异常测试通过；完整 custom DDR 帧尚未取得，正式 N03 未通过。**

## 当前离板验证

入口 `bash sim/scripts/run_vision_python.sh`（已接入总回归），专项可用 `python sim/vision/test_c01_capture.py`。
最终 `bash sim/scripts/run_iverilog.sh all` 退出0，视觉Python阶段也执行补齐追溯字段后的七组DDR测试并PASS；[完整原始记录](../2026-10-13-cnn-arithmetic/rtl-full-final.txt)。该入口全程离板fake，不进行实际设备访问。
原始输出 `python-owner-final.txt` 退出0；补齐实例/缓冲/缓存属性及脚本追溯字段后 `python-owner-metadata.txt`、配对退出码0，七组测试再验 PASS。板端最终入口只做离板语法检查，尚未实机执行。
包含 IRQ 先于停机、无 IRQ/错误槽、超时、DMA错误/失锁/代次/描述符变化、地址/分配失败、复制期间源变化、cache失败、释放失败和不确定停机时的缓冲隔离。测试缓冲均仓库 TB 内构建，无板端调用。

驱动使用单帧计数与 park slot 0，完成转移后自动停机；只有 fresh IRQ、RS=0、Halted=1、正确 slot/地址/几何和无新增错误共同成立才 invalidate/copy。手工停止只支持失败清理，不将部分帧发布为正常结果。正常返回是完整独立 ndarray；无法确认停机则保留原生缓冲且不重载 overlay。
IP依据及限制见[所有权候选](../../../docs/c01-ddr-frame-ownership-v0.md)。

## 已执行的两次实验

| 原始记录 | 退出码 | 实际结果 |
| --- | ---: | --- |
| `onboard-first.txt` | 1 | 首次在配置几何前清粘滞错误失败；尚未写 RS=1，四缓冲已释放，原 vision load/smoke 恢复 |
| `onboard-config-first.txt` | 3 | HDMI 重载后首次 smoke NOVIDEO，尚未启动 DMA；原 vision load/smoke 恢复 |

两次 boot_id 前后均 `2d61ca6a-03dc-4628-88e3-1203ac8b0e3c`。
候选 bit SHA256 `86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f`；HWH `eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c`。
COM12顺序操作，上传文件哈希与板端保存值匹配；上传/串口日志原样保留。

后续增加先配非零几何再清错误、候选 smoke 有界等待重试和更完整的失败释放处理。第三次上传/实测请求因自动审批服务额度错误未执行；随后用户明确转离板，因此**最终源码未上板复测**。没有正常帧 PNG 或成功捕获标记。

两次旧实验精确源码已恢复到[输入快照](../../../data/evidence/2026-10-13-ddr-experiment-inputs/)；`recover.py` 重建后只有 SHA256 与原上传日志逐字节一致才写入，`recovered-inputs.txt` 退出0。补齐追溯字段的当前源码另有[最终离板归档](../../evidence/cnn-ddr-offline-0635d33e8e274f88a88cd2a6a90464b2/manifest.json)，前一快照保留。

## 返板未完成项

- 最终驱动取到完整 720p BGR，PNG/像素哈希及实际通道核对；
- 动态整帧/慢复制无混帧、同一副本不会随下一轮改变；
- 完整 N03 错误/恢复/持续运行与 HDMI OUT/UVC 共存；
- LIVE 服务取帧接入与正式工位定标、正式数据采集。

当前距离、背景、光照只作测试，不冻结为正式工位标准。
