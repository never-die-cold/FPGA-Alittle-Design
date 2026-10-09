# 2026-10-09 协作记录：Codex／OpenCode两份仓库与RTL归档

> 标签：#build #工具链 #协作流程
> 平台：OpenCode（Windows，原会话10/06）＋Codex（VS Code／WSL，10/09归档）
> 模型：OpenCode `deepseek-flash`；Codex当日 `gpt-6.1-sol`（均据会话元数据）。
> 相关 commit：本次dev/rtl代码＋记录提交；归档读取基线 `051aefa`。
> 来源：[OpenCode项目会话摘录](../../data/logs/2026-10-09-collaboration-summary/opencode-project-session.json)，会话 `ses_f414e4730ffe4s0gyiHiOp5PYP`。

## 1. 任务与初始提示词

OpenCode原提示包括“把更新后的RTL拉取到本地”“克隆到VS Code”“分别在PowerShell和VS Code输入什么”。
本轮提示：读Codex／OpenCode协作记录，按模块独立归档，保留模板加索引；代码与记录一起提交到已有RTL分支，不建新分支，并教用户上传。

## 2. 模型第一版方案

OpenCode指出Windows和WSL是两份独立克隆；推荐在VS Code的WSL终端用 `code .` 打开仓库。
原方案为status→fetch→switch已有分支→pull→log；有改动先stash。
本轮采用WSL `/home/jianglibo/FPGA-Alittle-Design`；Windows克隆仅只读核查，不在两处同时提交。
每个模块独立md，`template.md`保留模板正文、只追加链接索引。

## 3. 失败现象

- 用户混淆“VS Code窗口”与当前目录／Git分支；Windows克隆仍在较旧main，不能当作WSL的最新代码。
- 读取时WSL在main，dev/rtl为其祖先；直接切换有未提交修改丢失／阻挡风险。
- 原OpenCode答复包含 `git checkout origin/main -- src/` 覆盖路径建议；本轮不执行，也没有据此发生代码丢失的证据。
- 初次WIP备份试写.git被只读权限拒绝；改为仓库data/logs保存，不丢弃修改、不使用/tmp。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 两个环境的仓库进度不同 | 不同clone不是同一工作区 | 明确实际路径、HEAD、来源日期 | Windows仅只读核查 |
| 2 | main有已审阅WIP，要求dev/rtl提交 | 需保护代码和证据 | stash全部WIP→切已有dev/rtl→ff-only main→apply | 191文件hash一致 |
| 3 | 要按模块查记录且保留模板 | 模板不是单次成果正文 | 四份记录＋模板索引 | 本地链接／模板保留检查 |
| 4 | 暂存区raw diff上下文空格报错 | diff证据并非源文件空白错误 | 改归档扩展名为已有规则支持的.patch | 两份原字节／SHA不变 |

## 5. 最终结论

本轮只在已有dev/rtl归档；main不变，未新建分支，未自动push。
dev/rtl从2daecc9快进到原main@051aefa，携带main已合入的团队历史；这32笔既有提交不是本轮新写代码。
已fetch核对远端；origin/dev/rtl当时无更新，上传前仍需再次核对。
[转移验证](../../data/logs/2026-10-09-collaboration-summary/branch-transfer.log)确认191个原WIP文件完整恢复。
新代码范围为已批准的下载脚本路径／回退修复、runner帮助与vision注释；没有另造新的RTL功能。
OpenCode最新项目会话为10/06的Git使用说明，没有新的RTL实现；不把旧会话记作10/09实现成果。
个人auth、数据库、原始工具输出、Windows备份目录和无关PPT不提交。
上传操作见[RTL代码与记录上传指南](../../docs/upload-rtl-code-and-logs.md)；若冲突／拒绝，停下，不强推。
相关提交可查询：`git log -1 -- report/llm_log/2026-10-09-git-workflow-collaboration.md`。

## 6. 经验沉淀

- 触发条件：跨Windows／WSL使用不同agent，目录名相同但分支、HEAD与WIP不同。
- 排查步骤：每份clone独立查cwd／status／log→确认唯一提交工作区→保存WIP指纹→转分支→验证再提交。
- 适用范围：多环境Git协作；只读聊天来源不等于另一份clone的代码自动可提交。
- #skill候选：只归档项目相关文本与来源元数据，不把凭据或整个agent数据库上传团队仓库。
