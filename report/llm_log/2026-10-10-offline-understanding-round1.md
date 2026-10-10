# 2026-10-10 协作记录：离板工作首轮理解核对

> 标签：#vision #模型接口 #理解门槛
> 平台：Codex desktop
> 基线：dev/exe @ aa23206；首轮答题时未提交，补测已通过，随后按原授权集成。

## 1. 任务与初始提示词

用户按此前要求集中回答离板检查 1–21 题和逐层参考 22–35 题。本步对照当前代码核对回答，
保存原答案、逐题判定与补测题；仅修改 report/llm_log，不改变实现或既有验证结论。
开工已核对分支、最近五次提交、工作区、workflow、主计划、核计划与接口契约。
使用古法编程及理解门槛；集中答题不取消提交前理解门槛。

完整讲解和原题分别见[离板检查记录](2026-10-10-offline-inspection.md)和
[逐层参考记录](2026-10-10-model-reference.md)。本文件保存用户首轮答案正文，去除行尾排版空格。

## 2. 用户原答案

## A — 协议/字段校验

1. **只查顶层会放行；真正拒绝在逐目标字段白名单处。**
   `src/pynq_host/vision_protocol.py:54` 检查 `set(target) - TARGET_FIELDS`，而 `TARGET_FIELDS` 仅含 `target_id`、`bbox`（第 20 行）。若只看顶层 `PACKET_FIELDS`，`targets[0]` 里多出的 `score` 不会被拒。

2. **差集检查允许可选字段缺失，同时拒绝未知字段。**
   `src/pynq_host/vision_protocol.py:31` 用 `set(packet) - PACKET_FIELDS`。若要求集合相等，像 `trigger_ref` 这类可选字段一旦省略就会报错（第 39–41 行），后续扩展也会不兼容。

3. **删掉 `dict` 检查后，`None` 会抛 `AttributeError`，而不是预期的 `ValueError`。**
   `src/pynq_host/vision_protocol.py:30–33` 先判 `isinstance(packet, dict)`；删除后 `packet.get("version")` 在 `None` 上直接失败，异常类型与契约不符。

---

## B — ROI 预处理

4. **框 `[10,20,11,21]` 裁剪出 1×1；右下角加 1 后变成 2×2，新增像素为 `(11,20)、(10,21)、(11,21)`。**
   `src/pynq_host/roi_preprocess.py:16–19` 采用半开区间 `[x0,x1)×[y0,y1)`，第 24 行 `image[y0:y1, x0:x1]` 直接取原图子集。

5. **预处理标识 `scene-gray-border-padding-v1` 已经绑定固定语义，不能换实现不换名。**
   `src/pynq_host/roi_preprocess.py:5` 定义版本；第 29 行固定 `INTER_AREA`，第 31 行用中位数边缘填充。改成其它插值或固定 0 会改变像素值，继续沿用同一标识就是伪造兼容性。

---

## C — 训练/快照/哈希

6. **两边都调用同一实现，会同时命中同一个 bug，对拍失去意义。**
   实际测试从交付原件快照里提取独立 `preprocess`（`sim/vision/test_roi_preprocess.py:12–17`），再与 `src/pynq_host/roi_preprocess.py:8` 的共享实现逐像素比较（第 27–30 行）。

7. **哈希是文件内容摘要，改 CSV 指向不能改变文件内容。**
   `data/evidence/2026-10-10-fastener-handoff/installed.csv` 记录了每个交付文件的 SHA256。篡改后的脚本哈希必然不同，无法冒充原件。

---

## D — 模型加载/精度/INT8

8. **`load_state_dict` 只校验形状，不校验输入契约。**
   `src/pynq_host/inspection_model.py:19–24` 显式要求 `classes`、`input_size`、`architecture`、`preprocess`、`preprocess_mode`；缺失任一都拒绝，防止用错误预处理 silent 跑通。

9. **合成图没有真值标签，且当前模型仍是 FP32。**
   `docs/offline-inspection.md:29–30` 说明合成结果只验证流程；`src/pynq_host/inspection_model.py:30` 标记 `precision: "FP32"`，没有 scale/zero-point，不是 INT8 模型。

---

## E — 规则判定

10. **`delta = actual − order`；`missing = max(-delta, 0)`，`extra = max(delta, 0)`。**
    `src/pynq_host/inspection_rules.py:39` 计算 delta，第 42–43 行计算 missing/extra。本题：bolt delta +1（extra 1），nut delta −1（missing 1），washer delta 0。

11. **应返回 `RECHECK`；不确定性优先级高于数量匹配。**
    `src/pynq_host/inspection_rules.py:40` 先判 `reasons` 是否非空。只有移除低分/触边等不确定目标后数量仍匹配且无 reasons，才会进入 `CHECK_PASS`。

---

## F — 上限/画框/帧关联

12. **超上限直接 `RECHECK` 且 `actual=None`，避免截断放行。**
    `src/pynq_host/inspection_replay.py:26–30` 在分类前直接返回；`actual=None` 表示未完整统计，`actual=0` 表示检测到 0 个目标（`docs/offline-inspection.md:71`）。

13. **在原帧上画框会污染输入像素；混用后一帧 ROI 会破坏 `capture_id` 关联。**
    `docs/inspection-v0-contract.md:33–34` 要求使用同一 `capture_id` 的原始 BGR 帧，不得使用加框图或后续帧。

---

## G — 产物清单与校验

14. **不能展示旧结果，因为清单要与所有产物哈希交叉校验。**
    `src/pynq_host/inspection_artifacts.py:32–35` 遍历 `artifacts` 并重算 SHA256。仅校验 `result.json` 存在无法发现 ROI PNG 被篡改。

15. **解析后检查目录归属是为了防止目录遍历；SHA256 不证明来源真实。**
    `src/pynq_host/inspection_artifacts.py:33–34` 拒绝越目录路径；`docs/offline-inspection.md:85` 明确 SHA256 仅检测意外修改，不提供签名或真实性认证。

---

## H — request_id / 原子写

16. **同一 `request_id` 重跑不应新增记录；改阈值会改变 fingerprint，必须换 ID。**
    `src/pynq_host/inspection_run.py:36–38` 复用已有目录；`docs/offline-inspection.md:32` 规定输入/权重/参数/代码任一改变须用新 `request_id`，禁止旧结果冒充重跑。

17. **`result.pending` 是未完成临时文件，自动覆盖会破坏现场。**
    `src/pynq_host/inspection_run.py:57–59` 先写 `result.pending` 再原子重命名为 `result.json`；`docs/offline-inspection.md:82–84` 说明中断目录应拒绝复用并保留现场。

---

## I — 回放与来源

18. **`--replay` 不能与 `--endpoint/--records-dir` 同用。**
    `src/vision_client/preview.py:161–163` 会报 `parser.error`。若允许，会混淆 FILE_REPLAY 离线快照与 LIVE/MOCK 网络来源，并可能把回放误计为手动触发批次。

19. **回放是静态快照，不适用实时新鲜度和触发按钮。**
    `src/vision_client/replay_viewer.py:25–31` 设置 `fresh=None`、`button=False`、badge `"FILE REPLAY"`、clock `"OFFLINE SNAPSHOT"`，状态栏显示 `"PROTOTYPE / verdict"`。

---

## J — 测试替身与回归门

20. **替身和几何图没有真实类别标签，不能验收真实精度。**
    `sim/vision/test_inspection_replay.py:18–19` 的 `StubClassifier` 固定返回 bolt；`docs/offline-inspection.md:29–30` 说明合成图结果只验证流程，不代表模型真实准确率。

21. **不应通过；回归门要求退出码 0 且无 ERROR/FAIL 行。**
    `sim/scripts/vision_gate.sh:11–13` 同时检查进程退出码、`^PASS:` 行、以及是否存在 `FAIL/FATAL/ERROR` 行。只检查 PASS 会漏掉非零退出码和后续错误输出。

---

## A — BN 折叠

22. **BN 折叠后的偏置包含 running_mean 与 beta 修正。**
    `src/pynq_host/model_reference.py:19–22` 计算 `factor=γ/√(var+ε)`、`bias=(bias−mean)×factor+β`；`docs/module3-prototype-reference.md:44–46` 说明即使原 Conv 无偏置，折叠后仍需要偏置，否则 BN 修正丢失。

23. **训练模式使用 batch 统计量而非 running 统计量；argmax 会漏数值误差。**
    `src/pynq_host/model_reference.py:9–10` 拒绝训练模式；`sim/vision/test_model_reference.py:30` 用 `assert_close` 校验逐元素，不只比 argmax。

---

## B — NumPy 参考实现

24. **NumPy 实现是互相关，与 PyTorch `conv2d` 一致，因此不反转卷积核。**
    `src/pynq_host/numpy_reference.py:18–20` 用 `sliding_window_view` 和 `einsum` 直接对位相乘；`stride=2` 通过 `::stride` 稀疏取窗，`padding=1` 通过 `np.pad` 在两侧补零扩展空间索引。

25. **rtol 照顾大值相对误差，atol 照顾零附近绝对误差；当前验证不支持“逐位一致”声明。**
    `src/pynq_host/numpy_reference.py:4` 定义 `RTOL=2e-5`、`ATOL=1e-4`；`docs/module3-prototype-reference.md:62–64` 说明判据为容差内接近，非 FP32 逐位相同。

---

## C — MAC/预算/板端

26. **MAC = 输出元素数 × 输入通道 × Kh × Kw；偏置/GAP 不计入同一数字。**
    `src/pynq_host/model_audit.py:18` 计算 `macs = math.prod(shape) * in_channels * kh * kw`，conv2 即 `32×32×32×16×3×3 = 4,718,592`；第 36 行把偏置加法单独记为 `bias_additions`，`docs/module3-prototype-reference.md:31` 说明 GAP 加法/除法也不计入 MAC。

27. **这两个数字只是张量口径，未含工作区、调度、搬运等开销。**
    `docs/module3-prototype-reference.md:36–38` 说明 130,956 字节参数和 49,152 元素相邻激活未涵盖滑动窗口工作区、流式调度、双缓冲、权重存放、DMA 等；第 40–41 行强调纯 MAC 理想耗时也不含数据搬运。

---

## D — FP32 hex / NPY / 哈希

28. **`3f800000` 是 IEEE754 单精度 1.0；不能直接送 INT8 MAC。**
    `sim/vision/test_reference_tensors.py:20` 给出 `[0.0, −0.0, 1.0, −2.5]` 对应 hex 含 `3f800000`；`docs/module3-prototype-reference.md:76,80` 说明这些是 FP32 位模式，未提供 INT8 scale/zero-point，不能直接 reinterpret 为 int8。

29. **同时保存 NPY/hex 可互相校验位模式，只检查哈希无法发现两份格式同时算错。**
    `src/pynq_host/reference_tensors.py:38–53` 在哈希校验后再对比 hex 与 NPY 的位模式是否一致。若导出时两份格式按同一错误算法生成，各自哈希可能都“匹配”，但对拍会发现位不一致。

---

## E — 黄金参考/诊断图

30. **原模型作为独立 oracle，防止 NumPy 自证自。**
    `src/pynq_host/model_reference.py:41–53` 的 `original_trace` 记录 BN 保留的 PyTorch 各阶段输出；`docs/module3-prototype-reference.md:53` 明确不把 NumPy 输出当作自己的期望值，以暴露卷积索引等实现错误。

31. **不能记为正确分类；缺少真实类别标签。**
    `docs/module3-prototype-reference.md:57,71` 说明三个输入为诊断像素，`truth_labels: None`；验收真实精度需要带人工真标的训练/验证/测试数据（`docs/module3-model-training.md:33`）。

---

## F — 参考包校验

32. **重算逐层结果和预算可发现清单与实际不一致；改哈希只能绕过文件哈希层。**
    `sim/vision/check_model_reference.py:41–42` 重算 `audit_layers`，第 50–52 行重算 `reference_trace`。仅更新错误黄金的哈希可让 `read_tensor` 通过，但躲不过逐层数值和预算重算。

33. **导出需要 PyTorch 加载 .pt 并计算 BN 折叠与原模型 oracle；哈希不证明板卡来源。**
    `src/pynq_host/reference_package.py:4–9` 导入 torch；`sim/vision/check_model_reference.py:68` 断言校验器未导入 torch。`docs/offline-inspection.md:85` 说明哈希仅检测修改，不提供来源签名。

---

## G — 子进程校验/负例

34. **`python -I` 子进程隔离父环境，验证包的自包含性。**
    `sim/vision/test_reference_package.py:27–29` 用子进程调用包内 `tools/check_model_reference.py`，避免父进程的 PyTorch/源模块污染，确认复制到别处后仍能独立复算。

35. **三负例分别验证工具哈希、预算重算、数值对拍；先 PASS 再失败不能收为通过。**
    `sim/vision/test_reference_package.py:37–60`：工具篡改验证 `check_model_reference.py:30–33`，预算被改验证第 41–42 行，黄金数值被改验证第 50–52 行。若日志先 PASS 再失败，进程退出码非 0 且含错误行，`sim/scripts/vision_gate.sh:11–13` 会拒绝。

## 3. 逐题判定

| 题号 | 判定 | 核对结论 |
| --- | --- | --- |
| 1 | 通过 | 顶层与逐目标字段分别检查，score 被目标白名单拒绝。 |
| 2 | 通过 | 可选字段可缺失，未知字段拒绝；新增字段仍须显式更新版本/白名单。 |
| 3 | 待补测 | 原题删除范围不够明确；只删类型条件而保留差集时，先 set(None) 抛 TypeError。 |
| 4 | 通过 | 半开区间的尺寸和新增像素正确。 |
| 5 | 通过 | 预处理标识绑定具体像素语义。 |
| 6 | 通过 | 保留独立原件参考避免共同错误。 |
| 7 | 通过 | 修改索引去向不改变原件字节及其摘要。 |
| 8 | 通过 | 权重加载不验证预处理契约；严格加载还检查键等，不仅形状。 |
| 9 | 通过 | 分数不是准确率，FP32 不是 INT8。 |
| 10 | 通过 | 差量符号与 missing/extra 正确。 |
| 11 | 待补测 | RECHECK 正确，但当前代码不移除低分/触边已知类别目标。 |
| 12 | 通过 | 超限流程返回未知计数；正常 actual 是逐类别计数字典。 |
| 13 | 通过 | 必须保留原帧像素及关联；实时 capture_id 链路尚未接入。 |
| 14 | 通过 | 需逐产物哈希检查，不能只查清单存在。 |
| 15 | 通过 | 路径归属与哈希真实性边界正确。 |
| 16 | 通过 | 请求复用与指纹变化规则正确。 |
| 17 | 通过 | pending 不是完成标记，保留中断现场。 |
| 18 | 通过 | 来源参数互斥，避免离线与在线批次混淆。 |
| 19 | 通过 | 静态回放不用实时新鲜度和运行按钮。 |
| 20 | 通过 | 测试替身和合成图不能验收真实精度。 |
| 21 | 通过 | 退出码、PASS 与失败文本三项同时满足。 |
| 22 | 通过 | 折叠偏置的均值与 beta 修正正确。 |
| 23 | 通过 | 训练统计变化，argmax 不代替逐元素对拍。 |
| 24 | 通过 | 互相关核方向、步长与填充索引正确。 |
| 25 | 通过 | 绝对/相对容差与非逐位一致边界正确。 |
| 26 | 通过 | Conv2 MAC 算式和预算口径正确。 |
| 27 | 通过 | 张量计数不等于集成资源或实机耗时。 |
| 28 | 通过 | FP32 位模式与 INT8 数值语义不同。 |
| 29 | 待补测 | 两份格式相同的错误值仍可位一致，需独立数值参考。 |
| 30 | 通过 | 原模型 trace 提供独立运算路径。 |
| 31 | 通过 | 无真实标签不能判分类正确。 |
| 32 | 通过 | 更新摘要不能代替独立重算；具体黄金错误须超过容差。 |
| 33 | 通过 | 导出/校验依赖区分和来源边界正确。 |
| 34 | 通过 | 隔离进程验证包内工具自包含性。 |
| 35 | 通过 | 三负例对应三层门槛，先 PASS 后失败仍拒绝。 |

合计：32 题通过，3 题待补测。不以文件引用的行号偏差扣分；按实际控制流和契约核对。

## 4. 缺口讲解

### 第 3 题：明确删除范围

原题“删除 dict 检查”有歧义，应明确到底删除类型条件还是整个 guard。
原实现 `not isinstance(packet, dict) or set(packet) - PACKET_FIELDS` 利用 or 短路：
None 在第一个条件即被判非法，因此显式抛 ValueError。
仅删除类型条件时，首先执行 set(None)，抛 TypeError，还没有执行 packet.get。
只有连同差集 guard 整段删除后，None 才首先到达 packet.get 并抛 AttributeError。
用户理解了类型保护目的，但需要澄清实际失败顺序；本轮不修改代码。

### 第 11 题：计数与不确定性各自保留

已知类别先计入 actual，随后分别记录 low_score/touches_border。
分数低或触边不会从 actual 中移除目标，reasons 非空就整轮 RECHECK，数量恰好匹配也如此。
unknown_class 无对应已知类别计数，但会保留不确定原因。当前流程没有过滤不确定目标再尝试放行的步骤。

### 第 29 题：一致性不等于正确性

read_tensor 的哈希层检查文件是否与清单摘要一致，格式层检查 dtype/形状/字节序等，
位模式层检查 NPY 与 hex 是否表示相同数据。如果两份都保存同样错误的数据且摘要更新，
这几层检查仍可能全部通过。独立输入和参数复算后与原模型黄金比较，才验证数值语义。
它也不提供真实性认证；不能宣称可识别输入、参数和黄金全部被一致修改的任意伪造。

## 5. 补测题

36. 只把开头改为 `if set(packet) - PACKET_FIELDS: raise ValueError(...)`，后续不变。
    输入 None 和 [] 各自先在哪里失败、是什么异常？为什么两者到达的位置不同？
37. 工单为 bolt=1、nut=1、washer=0，阈值 0.8；两个目标分别是 bolt/0.99 和 nut/0.20，均不触边。
    按当前代码给出 actual、delta、reasons、verdict；能否删除低分目标后继续尝试 CHECK_PASS？
38. 某层黄金输出的一项本应为 1.0，NPY 和 hex 都误写为 2.0，并更新所有相关摘要；
    输入、折叠参数与工具保持正确。read_tensor 能否发现？整包校验又在哪一步发现，为什么？

首轮判定时补测待答，没有执行 commit/push/PR；下方保存后续补测答案和最终判定。
依据 skill/understand-gate/SKILL.md：“用户答错或答不上 → 针对缺口再讲解，然后补 1 道新题再测，直到通过”。

### 补测用户原答案

**36. 仅保留 `if set(packet) - PACKET_FIELDS:`，其余后续不变**

- 输入 `None`：先在 `set(packet)` 处失败，抛出 **`TypeError: 'NoneType' object is not iterable`**。
  对应位置即原来的 `src/pynq_host/vision_protocol.py:31`（删掉 `isinstance` 判断后仍是这一行）。

- 输入 `[]`：`set([])` 得到空集合，`set([]) - PACKET_FIELDS` 为假，不会在这一行报错；继续执行到 `packet.get("version")` 时失败，抛出 **`AttributeError: 'list' object has no attribute 'get'`**。
  对应位置 `src/pynq_host/vision_protocol.py:33`。

---

**37. 工单 bolt=1、nut=1、washer=0；目标 bolt/0.99、nut/0.20，均不触边**

调用 `src/pynq_host/inspection_rules.py:7` 的 `judge`：

- **actual**：`{"bolt": 1, "nut": 1, "washer": 0}`
- **delta**：`{"bolt": 0, "nut": 0, "washer": 0}`
- **reasons**：`["low_score"]`（因为 nut 的 0.20 < 0.8）
- **verdict**：`"RECHECK"`

**不允许自动删掉低分目标再尝试通过。**
代码里 `actual[label] += 1`（第 31 行）与 `reasons.add("low_score")`（第 33 行）在同一个循环里完成：只要分数低于阈值就记 `low_score`，但目标仍被计入 `actual`。`judge` 没有“先剔除低分目标、再重算 delta”的分支，所以无法通过删除目标来把 verdict 变成 `CHECK_PASS`。

---

**38. NPY 和 hex 都错写成 2.0，且相关哈希/摘要已更新，输入和参数正确**

- **`read_tensor` 发现不了。**
  `src/pynq_host/reference_tensors.py:38–53` 只验证：文件哈希匹配、`NPY` 与 `hex` 的位模式一致。两份格式保存的是同一个错误位模式，互相一致，哈希也对得上，所以 `read_tensor` 会正常返回 2.0。

- **整包校验在 `check_model_reference.py` 的独立数值重算处发现。**
  第 47 行用输入像素和正确的权重/偏置重新跑 `reference_trace`，第 51 行把重算结果与包内黄金张量做 `assert_allclose`。由于输入和参数正确，重算结果本应是 1.0，而黄金张量被写成 2.0，二者偏差超过 `RTOL/ATOL`，于是抛出 `AssertionError`。也就是说，真正发现错误的是“独立重新计算”这道门槛，而不是文件格式自检。

### 补测判定与最终状态

| 题号 | 判定 | 结论 |
| --- | --- | --- |
| 36 | 通过 | None 先在集合转换失败，空列表通过差集后在字典接口失败；执行顺序正确。 |
| 37 | 通过 | 保留低分已知类别计数，delta 为零仍 RECHECK；没有过滤后放行分支。 |
| 38 | 通过 | 同错格式通过一致性层，正确输入/参数重算与错误黄金对拍时拒绝。 |

第38题按题设保持 dtype、形状等格式合法，read_tensor 的格式检查也不会发现数值语义错误。
理解门槛最终通过：首轮32题通过，3个缺口分别补测通过，已保存完整讲解、原题、原答案和两轮判定。
恢复原先授权的分批提交、PR、合并与分支同步流程，不新增代码、不要求再次答题。

### 提交前归档核对

代码按协议、离板检查、EXE 回放、逐层参考四批提交；第五批保存文档、产物和全量理解记录。
检查发现 NumPy 首次失败日志含原始 `AssertionError: ` 尾随空格；已说明跨目录范围后，
仅在根 .gitattributes 增加该日志的 -whitespace 例外，不改写失败现场，其余文件照常检查。
哈希关联产物入库时核对工作文件与暂存 blob 字节一致，避免换行转换破坏引用摘要。
RTL 关联工作区的旧未跟踪日志保留，分支同步使用快进方式，不重写历史。

## 6. 四件套与经验沉淀

① 新增本记录并更新前两轮及 Q01 记录的当前答题状态；不改代码。
② 验证为对照仓库控制流和既有十一组 PASS/退出 0 证据；本步文档变更不新增或重跑实现测试。
③ `git diff --check`：退出 0；新增记录末尾空白/合并标记检查：PASS，退出 0。
④ 未实现/未接入：正式 INT8、CNN RTL、核握手、板端原图取帧、LIVE 分类、工业闭环；
真实精度/PYNQ 环境/板端性能仍未验证。

提问时明确删除范围；判断要区分保留计数与整轮不确定性；双格式一致性只证明相互一致。
