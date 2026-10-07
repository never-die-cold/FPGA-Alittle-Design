# 模块一最终分支同步补记
日期：2026-10-07。用户明确指令：关闭符合验收的issue、开PR、合并、同步各分支。

## 同步事实
- 技术PR #60与纯文档PR #62已合并，最终main=f7102d2fedd8ad33900f53d0208f7c4b45694890；#20/#21和M1已关闭，备考#61保持open。
- dev/bench合并main保留Pi/视觉与收口提交，其余现存远程分支按祖先关系快进。
- 旧origin/CNN跟踪引用未被此前fetch清理，实际已改名dev/model；本次误重建旧名后确认它与dev/model均为最终main、无独有提交，再删除本次新建重复引用。保留dev/model，不删除原有分支工作。
- 本地codex/pi-hdmi-diagnostics保留95b853d诊断提交并合入main；不新建其远程分支。

## 自动合并后核文件对齐
旧诊断分支和main分别前移bp_predict_taken、redirect_target声明，Git自动合并把两对wire声明都保留，产生重复。差异核对表明core_top相对main仅多这两行。
使用git restore --source main -- src/riscv/core_top.v，对齐已经完成本轮理解门槛并明确授权合并的主干版本，不新增AI实现或改变核行为；诊断分支其他内容保留。
git diff --quiet main -- src/riscv sim/riscv退出0：核RTL及tb完整一致。沿用本轮已通过的理解记录，不重复引入设计题。

## 验证与交付
- iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v：退出0，见data/logs/2026-10-07-module1-branch-sync/verilog2001.log及.exit.txt。
- bash sim/scripts/run_iverilog.sh v1_flow：退出0，仓库已有tb专项PASS，见同目录v1-flow.log及.exit.txt。
- git diff --check及暂存检查通过。仅移除重复声明，未新增tb或核行为；完整核证据仍由main的模块一复现入口提供。
- 未实现/未接入：PS/CNN接口、工业固件、CSR/特权异常；本同步不改变上述状态。
- RTL工作树原有未跟踪d3-repro/id_ex_ooc日志保留；其他聊天的detached工作树不移动。
