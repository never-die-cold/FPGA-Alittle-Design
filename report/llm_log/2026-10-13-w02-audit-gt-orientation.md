# 2026-10-13 协作记录：数据集审计扩展——GT×manifest 交叉核对与朝向覆盖统计（W02 工具链预备）

> 标签：#vision #工具链 #架构决策
> 平台：ZCode（DeepSeek Flash） ｜ 相关 commit：`0a92e1b`
> 上下文：审计入口挂账两项"未实现"（GT CSV 与 manifest 交叉核对、朝向覆盖自动统计）；
> NC 首会话原帧尚未到达，先在无数据条件下把工具链做齐（"先交先标"一到即用）。

## 1. 任务与初始提示词

「完成审计挂账两项：GT↔manifest 交叉核对与朝向覆盖统计；不得破坏存量数据的可复算性
（已归档夹具/报告要能继续复算）。」

## 2. 模型第一版方案

- **GT 交叉核对**：`gt/<session>/<frame_id>.csv`（表头恰为 `obj_id,class,x0,y0,x1,y1`）逐帧比对
  manifest 目标集合（排序全等）；篡改/缺失/多余 GT 文件**拒绝**；`gt/` 目录不存在时报告
  `gt_checked=false`（格式变体不拒绝，但不得据此宣称标注已核）。
- **朝向**：manifest 增**可选** `orientation` 列（受控词表 bolt=axial/tilted/head_up、
  nut/washer=face_up/face_tilted；留空=未标注；未知 token 或与类别错配拒绝；空场景必须空）。
- **报告 schema v2**：每 split 增 `orientations/class_orientations/orientation_lights` 计数、
  `missing_orientation_combos`、`missing_orientation_labels/all_orientations_labeled`、`gt_checked`。
- 夹具生成器出 GT 与朝向 token；测试扩三段（manifest 负例、`check_gt` 五段负例、审计断言）。

## 3. 失败现象

1. 兼容性决策点：存量归档夹具**没有 gt/ 目录**，若把 GT 设为必查会把历史可复算性打破——
   改为"存在即严格、缺席即 flag"。
2. 空场景的 GT 形态未定义：若不约定，逐帧比对会在空帧上永远失配 → 约定"仅表头 CSV"。
3. 文档编辑两次匹配失败（`missing_classes` 带反引号、句中换行）——凭记忆改文档不可靠。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 设计评审（自查） | 必查 GT 会破坏存量复算 | 引入 `gt_checked` 两级语义并写进文档 | ✅ 归档夹具复算不回归 |
| 2 | Edit "String to replace not found" ×2 | 记忆中的原文与磁盘不一致 | 用 Bash 打印精确原文再改 | ✅ 三份文档同步完成 |
| 3 | 全链回归 | —— | —— | ✅ 检查链 14/14；组数 13→14 文档同步 |

## 5. 最终结论

工具链就绪：`orientation` 可选列 + GT 逐帧核对 + schema v2 报告（朝向计数/缺口）。
审计文档/采集规程/采集交接包三处格式说明同步；NC 首会话起即可填朝向，报告计数直接回填覆盖矩阵。

## 6. 经验沉淀

- 触发条件：给已被引用的数据格式加字段/加校验；"无数据先备工具"的等待期工作。
- 排查步骤：先盘"谁在引用这个格式"（存量证据、复算入口）→ 新列一律**可选**、新校验一律
  "存在即严格"→ 缺省走 flag 而非拒绝 → 报告版本号递增并写变更记录。
- 适用范围：换题目/换板卡仍成立（数据格式的兼容式演进是通用工程问题）。
- #skill候选：**"格式演进=可选列+报告 flag"**（可并入 contract-freeze-workflow）；
  **"严格度分级：存在即严格、缺席即明示"**（审计类工具模式）。
