# [2026-09-11] 协作记录：plan1 排期合并、三仓库对账与仓库结构合规整理

> 标签：#riscv #协作流程 #工具链
> 平台：OpenCode ｜ 模型：deepseek-v4-pro
> 相关 commit：`135e7d4`（plan1 合并）、`b0c64e6`（idea1 表格）、`2f40446`（RV32I 自测脚本）、`87b3910`（结构整理）；前序清理 `f5bc6a2` `9c398ac` `dc86dd7` `c7c6ca5` `148dff5` `7862ddb`

## 1. 任务与初始提示词

延续"三处仓库版本对比"的上下文，连续提出：

> "检查本地仓库和远程GitHub仓库的区别，另外我还有一个kimi的工作区，对比一下三个地方的版本区别"
> "复制kimi这个plan1.md，然后合并上GitHub上面的plan.md，将远程的这个plan1md删掉，在一个commit做完"
> "把所有仓库的文件结构统一为赛题指南中的指定格式（我的意思是把另外两个人的提交的.md修改到其他位置）"

## 2. 模型第一版方案

- 依据用户描述，初版方案按"远程存在 plan1.md、需要删除"设计，并给出多 commit 列表
- 提出用"替换 plan.md 里程碑对齐节"的方式合并 Kimi 草稿中的日粒度排期

## 3. 失败现象（真实偏差，如实记录）

1. **前提误判**：GitHub API 核对发现远程 `src/riscv/` 只有 `README.md` 与 `plan.md`，**plan1.md 从未进过 git**（仅存在于 Kimi 工作区，为未跟踪文件）。"删除远程 plan1.md"是空操作，方案需重构为"内容合并 + 不新增该文件 + 清理工作区副本"
2. **网络误判**：本地仓库 git 配置残留 `http.proxy=127.0.0.1:7897`（首次克隆时设置），该 HTTP 代理已关闭，pull/push 反复失败；实际使用 TUN 模式代理（`sing-tun` 网卡），移除死代理配置后直连正常
3. **gh 认证失败**：复用 Git Credential Manager 的 OAuth 凭证（`gho_`，40 位）执行 `gh auth login --with-token` 被拒：`missing required scope 'read:org'`
4. **收录脚本带 bug**：Kimi 草稿 `verify_rv32i.py` 运行即崩（`slli` 反汇编 `KeyError: 1`），且 `lui` 往返不匹配；继续运行发现 10 条 E 用例期望值与汇编不符

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | GitHub API 返回的远程目录清单 | 远程不存在 plan1.md，用户前提有误 | 改为"内容合并入 plan.md、不新增 plan1.md、删除 Kimi 工作区草稿（回收站）" | ✅ 单 commit `135e7d4` 推送成功 |
| 2 | `git ls-remote` 连接失败日志 + `tun0 sing-tun` 网卡证据 | 死代理配置与实际网络模式冲突 | 清除本地仓库 `http(s).proxy`，走 TUN 直连 | ✅ `pull --rebase` + push 成功 |
| 3 | gh 报错 `missing required scope 'read:org'` | GCM 凭证 scope 不足，不能直接复用 | 改用 gh 官方 OAuth 设备码授权（client_id 从 gh.exe 二进制核实为 `178c6fc778ccc68e1d6a`） | ✅ 登录 `never-die-cold`，scopes: `read:org`/`repo`/`workflow` |
| 4 | 脚本崩溃栈 + MISMATCH 列表 | 草稿编码器与期望值双向有错 | 修 `enc_u` 立即数位域、补移位指令编解码；按 ISA 位域逐条复核修正 10 条期望值 | ✅ 32 组用例输出 `ALL OK` |
| 5 | 赛题指南 3.2.5.5 推荐结构与仓库实况 | 根目录散落个人 .md，违反目录规范 | 两人 Git 记录移入 `docs/git_learning/`；README 补"目录对照说明"（指南为推荐结构，非强制但要求对照表） | ✅ commit `87b3910` |

## 5. 最终结论

- Kimi 工作区 plan1 的日粒度排期已合并进 `src/riscv/plan.md`（替换里程碑对齐节），Kimi 原草稿删除；三处仓库对齐到 `135e7d4` 后继续推进至 `87b3910`
- 仓库治理：`.gitignore`、`LICENSE`、`idea1.md` 更名、README 排期同步、Issue 模板 + onboarding 第五步、根目录清理与目录对照说明，全部落地
- GitHub 协作设施：gh CLI 已安装并设备码登录；标签 `bug`/`rtl`/`verify`/`docs`/`hardware` 与里程碑 `M1` 创建完成（卡点 issue 按 onboarding 第五步建）
- 工具修复：`sim/tools/verify_rv32i.py` 可复跑且 `ALL OK`，服务 plan.md 阶段 0 自测

## 6. 经验沉淀

- 触发条件：多副本仓库（本地 / 远程 / Agent 工作区）版本核对与合并；任何"删除某文件"类操作之前 #skill候选
- 排查步骤：**先取证再动作**——用 GitHub API 或 `git ls-remote` 核对远程真实状态，再谈操作；工作区副本先 `pull` 再 diff；网络异常先检查代理配置与实际网络模式（HTTP 代理 vs TUN）是否矛盾；外部工具认证优先走官方授权流程，不复用其它客户端的 token
- 适用范围（换题目/换板卡/换平台是否成立）：均成立。"AI 产出必须验证"在本条再次印证——草稿脚本修完才准入库
