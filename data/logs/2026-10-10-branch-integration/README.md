# 2026-10-10 分支集成复验

用户授权：将本地改动拆为多个提交到 dev/model，开 PR 合并，并同步五分支及现有工作树。

EXE 测试版本：cccd30b7a9eb7e9f8c368242afae41aec66471aa（7577580 + 模型 PR #64）。
入口：仓库根目录执行 `bash sim/scripts/run_vision_python.sh`；Windows 本机使用 MSYS2 Bash，PATH 加入 /usr/bin。
结果：退出 0，八组全部 PASS，原始日志见本目录。rounds 中超时/重握手 WARN 为故障恢复用例输出，最终判据 PASS。

模型接收完整性入口：docs/outsource/fastener-handoff.md 内 PowerShell 命令；输出 Installed integrity PASS: 48/48 files。
本地文档分三提交：c2b9c1b、5ff0160、9dd518c，模型及 JSON 格式差异经 Git 归一化后无内容改动。
默认 diff --check 对外包原文提示四处 Markdown 双空格硬换行；按保留原文要求不改。项目维护文档与契约 staged diff --check 通过。

未实现/未验收：正式板端定位、原分辨率 ROI、正式 INT8 模型/协处理器、LIVE 协议与工业检查全链验收。
本次未重新综合、打包或上板；核侧已有 all-b13/core-g2001-final 的退出 0 证据由 PR #65 引用。
