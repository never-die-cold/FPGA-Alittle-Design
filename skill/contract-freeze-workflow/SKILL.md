---
name: contract-freeze-workflow
description: Use when freezing a protocol/interface/module contract before implementation, when designing register maps or packet schemas with reserved fields, when writing validators for packet/message formats, or when reviewing whether an interface change is compatible. 契约冻结工作流：冻结前核对编码空间与全部用例 → 差集式双层白名单校验器 → 负例对旧代码 FAIL 留证 → 修复 → 正负例矩阵；缺口只登记不放宽。Trigger on 契约 / 接口冻结 / 报文 schema / 白名单 / 寄存器映射 / 编码空间.
---

# 契约冻结工作流（contract-freeze-workflow）

一句话规则：**冻结前先枚举全部用例核对编码空间，冻结后任何缺口"只登记、不放宽"；校验器用差集式白名单，修复用负例先行——先让旧代码 FAIL 留证，再让矩阵 PASS。**

## 流程

1. **冻结前**：列出目标域**全部**用例（全部子运算×编码、全部字段×类型、全部状态），逐项对照预留位宽/白名单/枚举——"先冻结后补功能"时，预留端口往往装不下真实需求（实例：3 位 `muldiv_op` 装不下 RV32M 8 种运算，MULH 落"除"、DIVU/REM 分不出符号，高位还被截断）。缺口写成"问题清单+选项"在实现前拍板。
2. **冻结**：决策单逐项记录（D1…Dn，含**禁令**——如"未知字段一律拒绝""errors_raw 只作证据"）；验收条款若含幂等/去重类"某重复不得计数"，优先**结构性保证**（在源头关断产生路径，如"自动轮次无记录路径"），运行时过滤器只是兜底。
3. **校验器**：差集式白名单——`实际字段 − 白名单 ≠ ∅` 即拒绝；顶层与嵌套对象**各一层**白名单（frozenset 防运行时增删）；先 `isinstance(dict)` 再 `.get`（让 None 抛预期校验错误而非 AttributeError）；可选字段允许缺失、未知字段一律拒绝。
4. **负例先行**：修复前先写会 FAIL 的测试并对旧代码跑出 FAIL（留证"缺口真实存在"），再修复；矩阵式正负例（如 3 合法/12 非法）一次覆盖：合法边界与拒绝边界（退化/反向/越界/未知枚举/重复 ID/未知字段/非对象）成对写。
5. **演化纪律**：实现缺口被发现时只登记不放宽冻结条款（登记→用户授权→修复→契约随版本评审更新）；新增字段走版本评审（决策单登记+版本号+校验器/测试三处同步）；契约变更**三处同步**（固件/链接脚本、仿真 tb、RTL——扩存储时只改一处会让高位绕回"侥幸 PASS"）。

## 踩坑

- "请求侧校验"不能替代"结果侧校验"：只拒绝 POST 请求的未知字段，不等于结果报文的嵌套 targets 也有白名单（实例：顶层合法 + `targets[0]` 多出字段被放行）。
- 加载契约：`load_state_dict`/反序列化只验形状——加载前必须校验元数据（类别顺序/输入尺寸/预处理标识）；预处理标识绑定像素语义，换插值/填充不换名 = 伪造兼容。
- 冻结 ≠ 猜测：引用任何"已冻结"章节前 `git show <branch>:<file>` 确认存在——引用不存在的契约章节会被答辩当场戳穿。
- 有上板/有运行的证据只证明"能用"，配置语义以契约文本为准；"改动只影响 X"的默认假设在契约边界处一律先查。

## 已验证效果

- 12 非法/3 合法报文矩阵对旧代码 FAIL 留证 → 修复后全 PASS，八组回归退出 0；
- RV32M 接口缺口在实现前拍板扩位，接入后 RV32IM 整核首次跑通（`tohost=142879`）；
- 32KB 存储契约三处同步后全量回归全绿、六份 hex 哈希不变（旧口径的高位绕回案例被 tb 成对改宽当场暴露）。
- 来源（`report/llm_log/`）：`2026-09-15-muldiv-interface-gap.md`、`2026-09-22-memory-contract.md`、`2026-10-06-vision-sync-protocol-decision.md`、`2026-10-10-q01-result-fields.md`、`2026-10-08-exe-batch-records.md`、`2026-10-09-module1-2-closeout.md`、`2026-10-10-offline-inspection.md`

## 失效条件

- 探索性原型阶段（契约本身未定）——先实验后冻结，但冻结前用本流程第 1 步核对；
- 单人单文件内部接口（无跨端对齐需求）——白名单/版本评审成本可能大于收益；
- 第三方协议只实现不定义时，本流程管"客户端校验与登记"，管不了对方违约。
