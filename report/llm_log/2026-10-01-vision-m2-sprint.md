# [2026-10-01] 协作记录：M2 冲刺——scaler 切拍达标 720p60 + sobel 接入 + in_align 归一化 + 74.25MHz 随访

> 标签：#vision #时序优化 #架构决策
> 平台：ZCode ｜ 模型：GLM-5.3-Flash
> 相关 commit：`13ace18`（scaler 切拍）/ `bf9aee1`（sobel 接入）/ `20c0912`（in_align）/ 本条随检查点 D 提交（real75 随访 + 文档同步）
> 工作区：独立 worktree `E:\Projects\FPGA-Alittle-Design-vision`（分支 dev/vision），主工作区并行会话在 dev/verify 未受影响

## 1. 任务与初始提示词

> "契约卡的开工日期完全可以前推，我们的项目做的越快越好" + "开工，分大步长来干吧" + "理解题我最后一块做，我先越权全部跑完"

背景：10/5 评审日期闸门被用户主动解除；D1 已拍板 720p60 为正式目标（决策单 `docs/vision-m2-review-1005.md`）。

## 2. 完成事项（按检查点）

1. **scaler 插值链切拍（`13ace18`）**：错半拍预寻址——ph0 发当前像素 x1 地址、ph1 发下一像素 x0 地址，x 方向插值 ph1 拍寄存、发射拍只剩 y 插值。**发射时刻与输出标记一拍不变**（区别于 9/30 三次失败尝试的关键：不挪标记，只重排读调度）。行边界捕获用 pend 槽号；冷启动修复（复位/in_vs 时 x_acc 置 INIT_X）。实测 10/10 位精确 + real 档 OOC WNS −0.534 ≈ 94.9 MHz。
2. **sobel 接入 vision_top（`bf9aee1`）**：D7 缩放前拓扑，R0 bit3 生效，tb_top 扩 6 帧 1024 px 位精确。
3. **in_align 输入归一化（`20c0912`）**：ADV7611 解码流 → §3.1 流约定（hs/vs 重定时、撞拍让路），tb_in_align 丑流验证，回归 11/11。
4. **74.25 MHz 随访（real75 档）**：gaussian +0.306、sobel +0.219、scaler ≈+2.9——三模块 720p60 OOC 全部正裕量，无需对 gaussian/sobel 切拍。

## 3. 调试实录

### 3.1 sobel 被 mux 绕过（bf9aee1）

- 现象：tb_top 帧 5（gauss|sobel）FAIL，DUT 输出恰为高斯黄金值。
- 定位：分级同拍 dump（`r0`/`t_sobel`/`e_de`/`e_y`/`m1_y`/`out_y`）——`t_sobel=1` 且 `e_de=1 e_y=be` 的同一拍 `out_y=93=m1_y`：输出 mux 走的不是 m1b。根因：**mux2 的 else 分支漏改**（仍指 m1），插入 sobel 级时只改了 scaler 输入。
- 修复：mux2 else → m1b（4 行）。教训：**插入流水级时，下游所有旁路 mux 的 else 分支必须同步改**。

### 3.2 in_align tb 两处误报（20c0912）

- 检查器首版把「帧中每行的 hs」误判违规（把 hs-before-first-de 检查写成了 hs-after-first-de）——tb 口径错，非 RTL 错；改为与 tb_scaler 同口径（首个 de 前须有 vs）。
- 撞拍帧 vs 计数期望写 3 实为 4（帧 B 含帧首 + 注入共 2 个 vs）。`hs_cnt=24`（8×3）本身即证明撞拍 hs 被顺延而非丢弃——无让路逻辑会是 23。

## 4. 经验沉淀

- 触发条件：流水线中插入新处理级 / 同步 BRAM 读调度的重排 #skill候选
- 排查步骤：
  1. 「DUT 输出 = 上游某级黄金值」类 FAIL：先怀疑旁路 mux 走错分支，dump 同拍的级间信号（本级有效标记 + 输入/输出数据 + 选择信号）即可一拍定位
  2. BRAM 同步读的重排：先画「地址发出拍 → 数据有效拍 → 消费拍」三拍表再动 RTL；发射时刻不变的重排（只动读调度与寄存位置）风险远小于挪输出标记
  3. 时序验收线换算：目标频率 F 对 10ns 约束的 WNS 门槛 = 1000/F − 10（74.25 MHz ⟺ −3.47）
- 适用范围：任意 FPGA 流水线项目成立

## 5. 理解门槛豁免留痕（gufa/understand-gate）

用户 2026-10-01 明示「理解题我最后一块做，我先越权全部跑完」——按 gufa-programming 失效条件第 3/4 条执行快速推进，**逐段讲解随各 commit message 落档，3 道理解题（rd_addr 空闲分支、cap pend 感知、x_acc 复位值）收尾补做**，题目与答案将追加至本文件「理解门槛」章节。

## 6. 补记（2026-10-01 晚，PR #48 后续）

- **push + PR**：dev/vision 推远端，PR #48 开出（base main），按约定不合自行 merge。
- **A5 真发现**：tb_top 延迟断言首跑 FAIL 揭示窗口级帧首像素延迟 =「1 行结构滞后 + 常数拍」（3×3 窗口需下一行流入才能算当前行），与 §3.2 稳态标记滞后（每级 3 拍）是两个口径——§4 已修正，metrics.csv 图像预处理延迟行由占位填实。
- **XSim 对拍闭环**：Part B §6 口径执行，全套同判据 PASS；踩坑：xvlog 默认入库 `work` 而非 `worklib`（xelab 顶层须写 `work.tb_x`）；按可复现红线落脚本 `run_vision_xsim.sh`。
- **寄存器映射表 v1.0 草案**入 design_v0 §3.3（R0 位定义 v0.2 / R1-R10 框参数 / R11-15 保留）。
- **分工变更**：用户明示「watercopper 的我也能做」——测试数据项由 never-die-cold 兜底：
  - ✅ scaler 缩小档 golden（32x16→8x4，`scaler_ds/`，行槽复用路径首次覆盖，iverilog+XSim 双口径 PASS，回归升至 12 tb）
  - ✅ 真实图替换通路 `data/scripts/img2hex.py`（PIL，任意图→指定尺寸 BT.601 灰度 hex）；真实照片待拍
  - ✅ 波形专项两项经核实已有等价覆盖（tb_top 帧锁存 + 逐帧精确计数），需求单标注闭环
- 回归现状：iverilog 12/12 PASS（`vision-all-12tb.log`）；XSim 同判据。
