# 模块一远程检查点收尾记录
2026-10-07：[PR #60](https://github.com/never-die-cold/FPGA-Alittle-Design/pull/60)已合并，merge commit=f3668f73ad2e6e779f5a2afe066e532770f94a02；[#20](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/20)、[#21](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/21)及M1技术里程碑已关闭。
用户理解补测通过并明确授权发布、合并、关闭与分支同步。草稿#59因GraphQL故障由相同内容的正式#60接续；按protect-main既定用户管理员例外执行，未代填非作者署名。技术证据固定于ad6db82，完整执行记录见[module1-pr.md](module1-pr.md)和本轮llm_log。

## #20：Part B 核验结果
- [x] IF / ID+EX / MEM+WB 三级；组合中间级未额外增加第四级。
- [x] EX/MEM/WB 逻辑来源旁路，valid/真实uses门控；连续RAW零数据气泡，load-use一拍。
- [x] 原v0 arch集合 add/addi/and 四档通过，另扩 RV32M 八操作。
- [x] 同CoreMark镜像 retired/CRC一致，固定Radix-4仅开转发 CPI 1.885683→1.693399（10.20%），≥8.0%回归门禁通过。
- [x] 当前默认转发检查点固定布线 @11.520ns STA WNS=+0.933、hold=+0.103；100MHz仍失败。
- [x] 自写benchmark、CoreMark、v0锚点与四档资源入收口报告。
- [x] 本轮脚本/数据/报告本地入库；用户理解补测通过。
- [x] 证据已推送，用户明确授权合并，PR #60与技术检查点关闭完成。

原issue的“100MHz硬指标/v0 86.8MHz”是旧快照；按仓库已确认本轮11.520ns最低门禁验收，v0同脚本83.8MHz为外推。原条款与未达事实保留，不把100MHz标通过。
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
- [x] 证据已推送，用户明确授权合并，PR #60与技术检查点关闭完成。
- [ ] 备考/断网模拟无本轮证据，已移交[#61](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/61)继续待办。

保留仅转发原25% FAIL（10/05实测8.14%）。当前Radix-4 nofwd→BHT2为14.83%，原Radix-2 nofwd→当前BHT2为32.00%，分母不同；25%为仓库已确认的组合尽力目标。100/125MHz不是当前最低门禁，不标通过。
已核对M1实际open-issue集合为空后关闭技术里程碑；汇总计数曾滞后，以issue实际状态和过滤列表为准。备考、产品集成与其他里程碑不随M1关闭而标为完成。
