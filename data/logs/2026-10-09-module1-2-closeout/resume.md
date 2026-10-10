# 续工记录：文档收口，禁止 commit／push

本文件为早期历史快照。后续停工与B13恢复状态以 [docs续工记录](../../../docs/resume-2026-10-09-module1-2-closeout.md) 为准；session 66951已中断，不再活动。

日期 2026-10-09；main@051aefaae9841e16237cc65a004b2c5ee5ec995d。
用户允许纯文档≤100行分批直接执行；脚本／RTL／接口行为须先审diff和理解题。

## 已落盘

- B01–B12 文档／获准两处注释、Q 登记、机器索引；B07脚本帮助与B13默认路径**未应用**。
- 报告 `report/llm_log/2026-10-09-module1-2-closeout.md` 已有范围、逐文件改动、历史保留与责任；§6最终检查结果待补。
- arch矩阵44/44，exit=0；静态core Verilog-2001无输出；16核RTL指纹一致；视觉去注释HDL不变。
- Python预检沙箱内socket拒绝exit=1；沙箱外相同入口7项PASS、exit=0。
- 原沙箱all主动中断exit=143，**不是完整PASS**，不得拼接其结果冒充新all通过。
- 完整all已在沙箱外从头启动，输出 `all-host.log`，结束后写 `all-host.exit.txt`；当前运行中。

## 接续顺序

1. 若有活动session，先等本次all结束（工具session 66951）；不得同时再跑另一个共享sim/build的CoreMark。
2. 检查 `all-host.exit.txt` 和完整原日志；四档CoreMark都须有PASS、retired/CRC一致、分类对账正确。
3. `all` 本身调用 v1_nofwd／v1_fwd／v1_fwd_bht1／v1_fwd_bht2；从同次完整原日志提取四档，注明不是另跑独立四次。
4. 补报告§6原命令／退出码／原始片段与代码／硬件收口界限；更新证据README运行中状态。
5. 刷新 `git diff --check`、本地链接、核指纹和只改授权文档／注释的检查，保留原始日志。
6. 汇报累计行数、报告／索引／日志链接与未验证项；展示18行待审patch，集中3题后等待用户。

## 不得越过的边界

- Q01只核查D6结果报文未知字段缺口，不修Python／tb、不放宽契约。
- Q02continue风险只登记；Q03不查远端／不补tag；Q04不删双语；Q05不重绘；Q06不改第三方／历史正文。
- 模块一已收口；模块二只RTL／已验证链路级；全项目M2未完成，CNN／网络硬件输出／工业闭环未完成。
- 无Vivado/XSim；不得生成新频率／时序／位流／上板结论。脚本Windows执行待验证线。
- 默认program_soc拟修为40MHz fwd／BHT关路径，绝不默认BHT2；patch仅供审核。
