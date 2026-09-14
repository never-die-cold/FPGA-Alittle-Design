# [2026-09-14] 协作记录：Vivado 版本决议更新——2025.2 改为 2026.1（BASIC 免费档）

> 标签：#工具链 #架构决策
> 平台：OpenCode ｜ 模型：opencode-go/deepseek-v4.1-flash
> 相关 commit：本条记录本身
> 取代：`report/llm_log/2026-09-11-vivado-licensing-research.md`（旧结论选 2025.2，现降为回退备选）

## 1. 任务与初始提示词

安装器与许可管理器逐页实测后，团队作出决议：

> "我们决定使用 2026.1，官方说后期 2026 版本会加支持"
> （前置事实：本机 2026.1 已装完、BASIC license 已生成并加载生效）

## 2. 模型第一版方案

沿用 2026-09-11 结论：选 **2025.2（ML Standard，免费）**——7 系列无需 license 文件、仿真功能完整；**2026.1 BASIC 仅列备选**，理由是"需年度续期 + Simulation 仅 Limited Features"。

## 3. 失败现象（旧结论与新事实的偏差）

旧记录只掌握"仿真受限"这一**笼统**说法，未量化阈值，导致"受限 = 不可用"的过度保守判断。本次查证官方 **UG973《Feature Availability by Subscription Tier》** 与 AMD 官方支持论坛，拿到 BASIC 档限制的准确清单：

| 限制项 | BASIC 档实况 | 对本项目影响 |
|:---|:---|:---|
| XSim 仿真 | ≤ **50K 实例**；无 UVM；无 XCRG 覆盖率；**仅 Windows**（Linux XSIM 被拒）；禁 `-jobs` 多线程 | 核级 tb 实例数远低于 50K；团队全在 Windows；不用 UVM → 无阻塞 |
| ChipScope 调试 | 1 个 ILA、最多 5 探针、仅例化流程（不支持插入流程）；无 System ILA / IBERT IP | 轻量调试够用 |
| License | **无有效 license 文件 Vivado 不启动**；BASIC 免费但需每 **12 个月**重新生成 | 赛事 11 月结束，在首个有效期内 → 无风险 |
| 第三方仿真器 | 完全支持 | iverilog 回归流不受影响 |

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 团队决议 + 官方"后期 2026 版本会加支持" | 旧结论基于笼统"受限"描述，过度保守；应按官方限制表逐一量化 | 查 UG973 与官方论坛，列 BASIC 限制清单，逐项对照设计规模评估 | ✅ 限制均不构成本项目阻塞 |
| 2 | 安装器 / 许可管理器截图 | 2026.1 起无 license 文件不能启动，BASIC 需年度续期 | 明确验收前置 = 生成并加载 BASIC license | ✅ license 已生效 |

## 5. 最终结论

- 工具链定为 **Vivado 2026.1（BASIC 免费档）**；**2025.2 ML Standard 降为回退备选**（若 BASIC 实测不可用再启用）
- 依据：BASIC 各项限制对本项目无实质影响；官方发布机制（每年 `.1`/`.2` 两版 + 更新）与"后期 2026 版本加支持"的说法一致，版本可持续获得更新
- 同步更新：`README.md` 工具链行、`docs/amd_track_awards.md` 第 6 条、`docs/repo_structure.md`；旧记录 `2026-09-11-vivado-licensing-research.md` 加取代横幅（按计划待删除）
- 验收：2026-09-14 当日完成——XSim 两套 tb PASS（与 iverilog 对拍一致）、v0 核综合基线出炉（**Fmax 86.8 MHz / WNS -1.530 ns**，未达 100 MHz，作为 Part B 对照），详见 [2026-09-14-vivado-2026-1-acceptance.md](2026-09-14-vivado-2026-1-acceptance.md)

## 6. 经验沉淀

- 触发条件：商业 EDA 工具版本 / 授权模式变更时的选型决策 #skill候选
- 排查步骤：
  1. 先读官方**限制 / 授权对照表**（UG973 Feature Availability by Subscription Tier）取**准确阈值**（实例数上限、OS 限制、功能开关），不要被"Limited"这类笼统词吓退
  2. 把每条限制对照**自身设计规模**逐项评估（本例：50K 实例 vs 核级 tb）
  3. 记清前置约束（如 2026.1 起"无 license 不启动"），写进安装验收清单
  4. 变更后同步仓库全部版本引用，避免文档与实机脱节
- 适用范围（换题目 / 换板卡 / 换工具是否成立）：成立；换成 Quartus / Vitis 等同样"先查官方限制表、再对照自身规模决策"

### 风险登记

- **年度续期**：2027-09 前需重新生成 BASIC license（赛事 11 月结束，首个有效期内无风险，此处留痕备忘）
- **仅 Windows**：Linux 成员无法用 XSim；若后续有人转 Linux，仿真退回第三方（iverilog）或启用回退版 2025.2
- **git 流程**：本次为领队单人、组员暂时联系不上，按 `2026-09-14-three-line-workflow.md` 记录的兜底程序（**停用规则集 → 合并 → 立即恢复**）提交 main，事后 API 复核规则完好
