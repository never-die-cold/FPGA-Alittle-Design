# [2026-10-10] 协作记录：协处理器 INT8 参考模型模块（int8_reference / int8_tensor_reference / sim/coprocessor）

> 标签：#coprocessor #量化契约 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`src/coprocessor/int8_reference.py`、`int8_tensor_reference.py`、`sim/coprocessor/`、`sim/scripts/run_coprocessor_python.sh` 随本轮同批提交

## 1. 任务与初始提示词

J02 算法阶段：先做**可复现的标量原语与张量 / per-channel 量化 / 卷积参考（Python）**，逐位对齐 C02 契约，作为后续 RTL 的**黄金参考**。只有标量→张量→卷积逐级通过理解门槛才允许推进。

## 2. 模型第一版方案

- **`int8_reference.py`**（J02-1~J02-3）：对称量化、`round_shift`（**半值远离零 ties-away**）、INT64 requant（INT32×INT32 乘积约 `2^62`，先 INT64 再舍入/饱和）、饱和器、对称 INT8 范围排除 `-128`、scale 的**整数编码**（multiplier/shift，写 manifest/参数包防软件-RTL 各自重编码）。
- **`int8_tensor_reference.py`**（J02-4）：per-channel 量化、仅 `OIHW` 卷积/`OI` 全连接合法（拒绝三维）、保持 shape/C 顺序且不改输入；Conv2d 地址、bias、padding、stride、INT32 溢出闸。
- **入口**：`sim/scripts/run_coprocessor_python.sh`（复用 `vision_gate.sh`）+ `sim/coprocessor/test_int8_{primitives,tensors,conv}.py`。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 边界语义易错：`-128` 排除、`ties-away`、INT32 乘积溢出、`bool` 冒充 0/1、非法 shape 必须拒绝——均以定向负例覆盖。
2. **未决**：正式 PTQ/QAT、整网黄金、RTL/综合/端到端延迟均未开始；当前 PASS 只证明**标量原语/张量/卷积参考**，不证明 RTL。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `round_shift(-5,1)` 期望？ | 半值远离零 | 返回 `-3` | ✅ primitives PASS |
| 2 | INT32 乘积溢出 | 需 INT64 保留再舍入/饱和 | INT64 中转 | ✅ primitives PASS |
| 3 | 三维/非法排布 | 仅 OIHW/OI 合法 | 显式拒绝门 | ✅ tensors PASS |
| 4 | 卷积地址/越界 | INT32 溢出闸 | 溢出即拒绝 | ✅ conv PASS |

## 5. 最终结论

三个 Python 测试 **全 PASS**（`primitives` / `tensors` / `conv`），构成 C02 契约的逐位黄金参考；为后续 MAC/卷积 RTL 提供对拍基准。**仍非 RTL、综合或端到端实测。**

## 6. 经验沉淀

- 量化参考必须**显式声明**：舍入规则（ties-away）、`-128` 排除、饱和、`bool` 拒绝、排布合法性；
- INT32 乘积**必须 INT64 中转**再舍入/饱和，禁止回绕；
- scale 的整数编码不唯一 → 把最终 `multiplier/shift` 写进 manifest，避免软硬件各自重编码。 #skill候选
