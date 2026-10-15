# 2026-10-13 协作记录：C01 捕获后端适配（W04）——一轮一租约与"fake 驱动真驱动"

> 标签：#vision #架构决策 #工具链
> 平台：ZCode（DeepSeek Flash） ｜ 相关 commit：`1e0eb3f`
> 上下文：NC 交接 `docs/c01-ddr-frame-ownership-v0.md`（单帧驱动已实现+七组离板测试；"WC 实现适配，NC 实测"；§6 交接门要求 WC 给出完成/槽绑定/保护/屏障/cache 依据与仓库替身入口）。

## 1. 任务与初始提示词

「读所有权交接文档，实现服务侧适配与离板替身入口，并给 §3 八步操作序→实现位置的评审注记；
未由离板验证的硬件断言要显式标明，实机确认前不得宣称。」

## 2. 模型第一版方案

- `src/pynq_host/c01_backend.py`：`C01Captures` 把 `SingleFrameCapture`（NC 的单次所有权对象）
  接进 `vision_live_service`——**一轮 = 一个新单次租约**（factory 现场构造）；独立副本立即编码
  PNG 原子落盘；`prototype` **结构性 = False**（真实硬件后端；FILE 后端恒 True 的另一半）。
- 服务：`do_POST` 捕获 `RuntimeError → 503`（失败轮不写 `packet.json`，无正常结果）。
- 离板替身：`test_c01_backend.py` 用最小 VDMA/CAP1/分配器/代次 fake **驱动真实驱动**，
  服务级覆盖 §5 矩阵离板行。
- 评审注记（文档 §7）：§3 八步→实现位置映射 + 硬件断言边界清单。

## 3. 失败现象

1. 设计替身测试的 LOCATION_ONLY 引擎时发现 `complete_decision(decision=None)` 会
   `None.get(...)` **崩溃**（此前引擎恒有 verdict，该路径从未被走过）。
2. 裸跑 `py sim/vision/test_c01_backend.py` → `No module named numpy`（未带依赖路径）。
3. 设计取舍点：C01（真捕获）若配替身引擎，报文 `prototype=false` 但判定是合成的——
   需要把"来源"暴露在产物（`engine.json`/`result.json` provenance）而不是悄悄改旗。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 阅读驱动源码发现 LOCATION_ONLY 路径 | 防御性缺口：非 dict 判定被当 dict 用 | `complete_decision` 首行 `if not isinstance(decision, dict): return decision` | ✅ 且新增测试直接走该路径 |
| 2 | ModuleNotFoundError: numpy | 测试自举：按已建模式挂接仓库依赖目录 | 加 `sys.path` 引导（与 test_service_engine 同式） | ✅ 一次通过 |
| 3 | 代次变化用例 | 驱动契约：未确认停止 → quarantine、不归还原生缓冲 | 测试断言 `frees` 不增长 + `QUARANTINE` 恰一条 + 假环境复位后安全释放 | ✅ |

## 5. 最终结论

W04 适配落地：一轮一租约、失败 503 无产物、代次变化拒发并隔离；§7 明确"写事务完成/槽绑定"
仍待 NC 实机——JL 确认集成位流/地址/复位后 NC 方可排 custom N03。视觉栈 17/17、真引擎测试过。

## 6. 经验沉淀

- 触发条件：把"他人的驱动/硬件对象"接进自己的服务层；离板验证硬件相关路径；覆盖旧测试盲区。
- 排查步骤：先读对方驱动契约（单次使用/隔离/唯一在途）→ 在服务层做"结构性"保证而非运行时过滤
  → 替身只测接线、不复刻实现 → 明确列出"离板测不到、实机才认"的断言清单。
- 适用范围：换题目/换板卡仍成立（"fake 驱动真驱动"、租约生命周期、失败不产正常结果）。
- #skill候选：**"fake 驱动真驱动：测接线不复刻实现"**（可并入 big-rewrite-playbook 或独立成条）；
  **"未验证硬件断言显式清单"**（交付评审门）。
