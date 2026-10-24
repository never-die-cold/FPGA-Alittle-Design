# 2026-10-19 协作记录：Q5 策略/能力分层、未完整计数诚实展示、快照 ROI 哈希链

> 标签：#vision #架构决策 #bug修复
> 平台：ZCode（DeepSeek Flash） ｜ 相关提交：本次（`fix(chain)`）
> 上下文：NC 10-14 评审单点名 WC 三项：①分开协议能力16与检查策略10并覆盖 10/11/16/17 与空场景边界；
> ②超限映射的零计数/缺件差额不得当实测展示或导出；③快照核对按 Q3 细则补 ROI 哈希链。

## 1. 任务与初始提示词

「按 NC 评审单三项修复：策略与能力分离、部分计数诚实表达、快照核对补 ROI；改动后全量回归并留证。」

## 2. 模型第一版方案

- `inspection_rules.judge`：新增 `policy_max`（默认 `min(10, max_targets)`，业务放行上限），
  目标数或工单总数超策略即 `target_limit`；`max_targets` 仍为协议/硬件能力上限（16），**不互替**。
- `inspection_replay.inspect_frame`：超**策略**即 RECHECK、不启动分类、targets=[]、计数 None；
  结果 `parameters` 显式记录 `policy_max`；`inspection_run` provenance 同步。
- EXE：`live_view` 识别 `target_limit` → `partial=True`、`counts=None`、`delta` 清空；
  横幅显示 `RECHECK 未完整计数`、计数列 `--`；CSV 导出对 partial 轮 missing/extra 留空（reasons 保留）。
- `round_artifacts`：引擎产物存在时逐目标核对 ROI（解码像素字节哈希 == `roi_pixels_sha256`），
  拒绝越界/缺失/篡改。

## 3. 失败现象

1. **真缺口（评审前）**：默认 `max_targets=16` 下 11–16 个目标会被当作正常 PASS/FAIL 放行，
   违反 C03 §8 的 10 件策略；
2. 新增策略测试首跑失败：`policy_max=1` 与工单总数 2 冲突（judge 设计上工单总数同样受策略约束，
   测试用例自身非法）→ 改为合法工单 + 目标数超策略的场景。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 评审单"FILE 默认 max_targets=16 未执行 10 策略" | 能力上限被误当业务放行上限 | judge 增 policy_max；inspect_frame 超策略不分类 | 边界矩阵 10/11/16/17 PASS |
| 2 | 策略测试 ValueError | 用例本身违反"工单总数 ≤ 策略" | 改为工单 sum=1、目标数 2>策略 1 | ✅ |
| 3 | 映射零值在 UI/CSV 显示为数量 | 派生值缺少来源标记 | live_view partial + 横幅"CJK 未完整计数" + CSV 留空 | 渲染验证 + 导出断言 |
| 4 | 快照核对只到 capture/源哈希 | Q3 细则要求 ROI 也入链 | `_verify_rois`（解码像素字节哈希，路径越界/缺失/篡改拒绝） | 篡改负例 PASS |

## 5. 最终结论

三项全部落地：策略/能力分离（10 默认、16 能力）、target_limit 轮全链诚实表达（UI/CSV/记录 reasons）、
快照核对覆盖 capture→源→逐 ROI 三层链。视觉栈 20/20、检查链 14/14、打包六关全 PASS；
`RECHECK 未完整计数` 渲染态已出图核对（混合中英文横幅排版正常）。

## 6. 经验沉淀

- 触发条件：同一系统存在"能力上限"与"业务策略上限"两层限制；派生/映射值进入展示或导出。
- 排查步骤：把两个上限显式命名并分层（能力=物理上限、策略=放行上限，前者不自动成为后者）→
  映射派生值必须带来源标记（partial/reasons）贯穿 UI 与导出 → 哈希链核对到"最小可消费单元"
  （ROI 像素而非文件字节）。
- 适用范围：换题目/换板卡仍成立（分层上限、派生值标记、证据链到消费粒度）。
- #skill候选：**"能力/策略分层"**（并入 contract-freeze-workflow）；**"映射派生值必须带来源标记"**
  （并入 bug-fix-playbook 的"存值不存指针"条目）。
