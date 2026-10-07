# 模块一远程检查点收尾草稿
2026-10-07 只读核对：[#20](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/20) 与 [#21](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/21) 均 open。
本文件尚未发布到 GitHub。用户理解门槛已补测通过，代码和证据已本地提交；自动批准审核拒绝推送，当前待明确发布授权。独立PR发布稿见[module1-pr.md](module1-pr.md)，发布后采用对应提交的永久链接。

## #20：Part B 核验结果
- [x] IF / ID+EX / MEM+WB 三级；组合中间级未额外增加第四级。
- [x] EX/MEM/WB 逻辑来源旁路，valid/真实uses门控；连续RAW零数据气泡，load-use一拍。
- [x] 原v0 arch集合 add/addi/and 四档通过，另扩 RV32M 八操作。
- [x] 同CoreMark镜像 retired/CRC一致，固定Radix-4仅开转发 CPI 1.885683→1.693399（10.20%），≥8.0%回归门禁通过。
- [x] 当前默认转发检查点固定布线 @11.520ns STA WNS=+0.933、hold=+0.103；100MHz仍失败。
- [x] 自写benchmark、CoreMark、v0锚点与四档资源入收口报告。
- [x] 本轮脚本/数据/报告本地入库；用户理解补测通过。
- [ ] 推送证据、PR复核与远程检查点同步。

原issue的“100MHz硬指标/v0 86.8MHz”是旧快照；仓库已确认本轮11.520ns最低门禁，v0同脚本83.8MHz为外推。保留原条款历史，说明修订依据后关闭，不能把100MHz标通过。
依据：`src/riscv/plan.md` §4.2、`design_v1.md` §14/§16.4、`report/module1-closure.md`、`data/logs/2026-10-07-module1-closure/`。

## #21：Part C 核验结果
- [x] 64项关闭/1-bit/2-bit BHT；同RTL参数切换，预测元数据与被接受指令一致。
- [x] 正确预测零冲刷；误预测清valid并恢复PC；错误路径写回、store、muldiv、退休被抑制。数据payload不必清零。
- [x] 同窗口BHT统计，CoreMark BHT2 91.18%；benchmark BHT2 75.78%，静态不跳方向命中率推导31.06%。
- [x] 自写benchmark四档接入all；arch扩展子集11条×4档共44次签名通过，不是上游全套认证。
- [x] v0外部锚点与v1四档CPI、CoreMark/MHz、资源、约束点和命中率已列入报告。
- [x] 优化后XSim四档逐位对拍；BHT2 @11.520ns独立实现 WNS=+0.538、hold=+0.167；40MHz主档已有人工上板观察。
- [x] 本轮完整all最终退出码0，汇总脚本交叉核对通过。
- [x] 本轮本地入库；理解门槛补测通过。
- [ ] 推送证据、PR复核后再关闭检查点。
- [ ] 备考/断网模拟无本轮证据；不冒充已完成，应与核技术验收分开维护。

保留仅转发原25% FAIL（10/05实测8.14%）。当前Radix-4 nofwd→BHT2为14.83%，原Radix-2 nofwd→当前BHT2为32.00%，分母不同；25%为仓库已确认的组合尽力目标。100/125MHz不是当前最低门禁，不标通过。
关闭issue后再核对M1里程碑剩余事项；不得凭关闭#20/#21自动宣称所有备考、产品集成或其他issue已完成。
