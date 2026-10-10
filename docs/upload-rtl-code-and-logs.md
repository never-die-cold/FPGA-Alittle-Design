# 上传RTL代码与协作记录（已有dev/rtl，不新建分支）

本轮使用VS Code的WSL终端，工作区为 `/home/jianglibo/FPGA-Alittle-Design`。
Windows `C:\Users\jianglibo\Documents\FPGA-Alittle-Design` 是另一份克隆，不混用这份提交。
本次已审阅的代码、协作记录及验证证据一起做本地提交；GitHub上传由用户执行。

## 1. 核对本地提交

```bash
cd /home/jianglibo/FPGA-Alittle-Design
git branch --show-current
git status
git log --oneline -3
git show --stat HEAD
```

分支必须显示 `dev/rtl`，工作区应干净；HEAD应包含本次代码和 `report/llm_log/` 四份分模块记录。
若你在提交后又改了代码，不要直接照抄上传：先审核并验证新修改，确保代码与记录同步。
`template.md`保留通用模板，在末尾链接本次四份记录，不把模板替换成某个模块正文。

## 2. 同步后上传

按顺序运行；任何一步失败都先停下，不继续下一条。

```bash
git fetch origin
git pull --rebase origin dev/rtl
git push origin dev/rtl
```

- fetch只更新远端信息；pull在提交后、干净工作区内执行，按既有规则同步dev/rtl。
- rebase若发生冲突，停下交队友处理；不要猜着解冲突，不执行强推。
- push若被non-fast-forward或hook拒绝，保留错误输出；不得加 `--force`／`--force-with-lease`。
- 不运行 `git switch -c`／`git checkout -b`，不向main直接push。
- VS Code“同步更改”可能合并pull和push；本轮建议用上面的明确终端命令。

## 3. 检查上传结果

```bash
git status -sb
git rev-parse HEAD
git rev-parse origin/dev/rtl
```

正常情况下两个哈希一致；如队友随后又更新远端，需fetch后重新核对，不能仅凭缓存宣称一致。
浏览器打开[团队仓库dev/rtl](https://github.com/never-die-cold/FPGA-Alittle-Design/tree/dev/rtl)，检查代码及 `report/llm_log/template.md` 索引与四份记录。
上传分支不等于合入main；是否提PR及合并由团队流程决定。

## 4. 验证与范围

本次提交沿用同一源码指纹下完整all exit=0、arch44/44、Verilog-2001零输出的原始证据，见[收口报告](../report/llm_log/2026-10-09-module1-2-closeout.md)。
本轮默认仍为40MHz／转发开／BHT关；下载BHT2必须显式选择位流。
Windows下载脚本实际执行仍待验证；不因提交／上传而新增时序或硬件验收结论。
