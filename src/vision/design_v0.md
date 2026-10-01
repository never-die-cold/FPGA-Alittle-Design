# vision design_v0 —— HDMI 图像预处理流水线接口设计（前期草案）

> 是什么：模块二（HDMI 直通 + 预处理流水线）的模块划分、接口与验证策略草案。
> 给谁看：never-die-cold（模块二 RTL，本文维护者）、watercopper（黄金参考与测试数据，第 6 节需求单）、jianglibo（第 7 节模块三衔接）。
> 什么时候读：10/2–10/4 前期评审用；10/5 开工时按评审结论升格为冻结契约（对齐 design_v1.md 的流程）。
> 状态：**草案，未评审未冻结**。所有数值为初稿，评审后固化为契约条款。上游依据：`src/vision/README.md` 模块清单、`docs/proposal_upgrade.md` A 档任务、`docs/track_research.md` §1.4 Ultra-Vision 参考。

## 1. 目标与范围

M2 目标：HDMI 输入 → 预处理链 → HDMI 输出的实时直通演示，含 A1 参数化与 A2 直通/帧缓存对比数据。

Part B 收口前（10/2–10/4）只做文档与测试数据准备，不写 RTL；10/5 起进入实现。

## 2. 数据通路（直通架构，A2 的对照项之二）

```text
ADV7611 HDMI IN ──像素时钟域──> 输入对齐/24bit RGB ──> rgb2gray ──> gaussian_3x3 ──> [sobel 可选] ──┬──> [osd] ──> HDMI OUT（全分辨率直通显示）
                                   |                                                              └──> [scaler] ──> 乒乓行组缓冲 ──> cop_top（快照推理）
                                   └────────────── axi_regs（PS/AXI-Lite 参数：链路开关、系数、目标尺寸、ROI）──────────────┘
```

> 注 1：sobel 位置 2026-09-30 决策单 D7 定为缩放前（gaussian 之后）——全分辨率上做边缘，
> 缩放后 224 小图边缘信息已损失；原初稿画在 scaler 后，已按 D7 更新。
> 注 2：拓扑 2026-10-01 定为**双路径**（对齐 2026-09-21 叙事决策「行缓存直通显示 + 片上快照
> 推理」）——scaler 不串在显示路径（224 小图不上屏），显示恒全分辨率，OSD 框坐标 = 全分辨率；
> 快照分支在 sobel 后分叉喂 cop_top。

- 默认**免帧缓存直通**（对齐 Ultra-Vision 创新点 1 与 A2）：全链在输入像素时钟域逐像素推进，逐像素延迟固定可测。
- A2 对比项保留帧缓存路径（经 PS DDR）作为测量档，不在 M2 主线实现，10/5 后按人力定。
- 每级旁路开关由 `axi_regs` 配置（A1 参数化），开关切换在帧边界生效（消隐期切，避免撕裂）。

## 3. 模块划分与接口初稿

统一像素流约定（初稿，评审定稿）：同 `pclk` 单时钟域；`de`（data enable）+ `hsync/vsync`；像素 `RGB[23:0]`；后级灰度域 `Y[7:0]`。无 ready 反压——直通链逐拍推进，AXI-Lite 配置跨时钟域用 2FF 同步器。

| 模块 | 输入 | 输出 | 初稿要点 |
|:---|:---|:---|:---|
| `rgb2gray.v` | `rgb[23:0]`, `de` | `y[7:0]`, `de` | BT.601 定点：`Y = (77R + 150G + 29B) >> 8`（系数和=256，无饱和问题）；1 级流水 |
| `line_buffer.v` | 写口 `wdata[7:0]/wen/waddr` | 读口 `rdata[7:0]`（延迟 1 拍） | 每行 BRAM：宽度=最大行宽（初稿 1920，按分辨率评审降为 1280）；2 片例化构成 3 行窗口 |
| `gaussian_3x3.v` | 3×3 窗口 `y[7:0]`×9, `de` | `yg[7:0]`, `de` | 核 `[1 2 1;2 4 2;1 2 1]/16`，乘法全移位加，`>>4`；行首/帧首边界复制像素填充 |
| `scaler.v` | `yg[7:0]`, `de` | `ys[7:0]`, `de`，`out_x/out_y` | 双线性；整数:分数坐标增量存 `axi_regs`（避免除法器）；目标尺寸 = 模块三网络输入（待定，见 §7） |
| `sobel.v`（可选） | 3×3 窗口 | `edge[7:0]` | M2 若紧张则降级为 stretch；接口先预留 |
| `osd_overlay.v` | 处理后像素 + 检测框坐标 | 合成像素 | A4 动效：框坐标/颜色寄存器化；与 pynq_host 联调 |
| `axi_regs.v` | AXI-Lite | 链路参数寄存器堆 | 寄存器映射评审时定稿（表随契约出） |
| `vision_top.v` | 上述全部 | — | 例化与级间旁路 mux；对外 HDMI 接口取决于第 5 节选型 |

## 3.1 实现口径 v0.1（2026-09-29 首批三模块落地时确立，10/5 评审确认）

单元级流约定（HDMI 解码上游负责归一化到本约定）：

- 单时钟域（pclk），posedge 采样；`de=1` 表示当前像素有效。
- `vs`：帧首单拍标记（清 x/y 计数），与 `hs` 不同拍。
- `hs`：行尾单拍标记（清 x、y+1），与该行最后一个 `de` 间隔 ≥3 拍、与下一行首个 `de` 间隔 ≥1 拍。
- 帧尾 vblank ≥ WIDTH+8 拍（真实 HDMI vblank 远大于此），供 `gaussian_3x3` 末行冲刷。

已实现口径：

- `rgb2gray.v`：BT.601 定点 `Y=(77R+150G+29B)>>8`，1 拍延迟，黄金参考 `data/golden/vision/rgb2gray/`。
- `line_buffer.v`：参数化单行 RAM（WIDTH/DW），同步读；同拍同址**先读后写**（返回旧值）——gaussian 依赖此语义读取"正在被写入的 buffer"的旧行。
- `gaussian_3x3.v`：双行缓存按行号奇偶轮替，输出行落后输入 1 行；末行在 vblank 冲刷补出（底邻居钳位为自身）；列方向三级读链给出 {左,中,右}，左右边界用中列钳位；全移位加无乘除法。黄金参考 `data/golden/vision/gaussian3x3/`。
- `sobel.v`：窗口装配/冲刷与 gaussian 同构；Gx/Gy L1 幅值 `|Gx|+|Gy|` 8 位饱和。黄金参考 `data/golden/vision/sobel/`。
- `scaler.v`：16.16 定点双线性（坐标 `(2d+1)S/(2D)-0.5` clamp，fx/fy 高 8 位，两级 8bit lerp）；NLINES 行槽滑动缓存 + 2 拍/像素**错半拍预寻址列读**（ph0 发 x1 地址、ph1 发下一像素 x0 地址，x 插值 ph1 拍寄存、发射拍仅 y 插值，2026-09-30 切拍后口径）；发射与源写入解耦（未就绪挂起、hs 续发）。约束：NLINES 为 2 的幂，行步进 ≤ NLINES-2；吞吐 1 像素/2 拍（缩小档充足）。real 档 OOC WNS −0.534@10ns（≈94.9 MHz，720p60 达标）。黄金参考 `data/golden/vision/scaler/`。
- `tb_chain.v` / `tb_fullchain.v`：两级与三级（rgb2gray→gaussian→scaler）级联冒烟；末端对拍 `data/golden/vision/fullchain/expected_fullchain.hex`，中间级同时对拍单级 golden。
- `osd_overlay.v`：灰度流直通 + 两个 1px 描边框（box 检测框 / roi），命中像素以各自颜色替换、重叠 box 优先；**参数在帧首 vs 锁存**——帧内改参数不影响当前帧（A4 动效换帧生效语义），tb 以双帧 golden 验证锁存。黄金参考 `data/golden/vision/osd/`。
- `axi_regs.v`：AXI-Lite 从机参数寄存器堆（NREG=16，映射 v0.1 见模块头注释：R0 控制开关 / R1–R5 检测框 / R6–R10 ROI / R11–R15 保留）。要点：**AW 默认 7，须满足 2^AW > NREG*4**——AW=6 时地址空间恰好被寄存器占满，越界判别永远无法触发（tb 实测教训，2026-09-29）；保留区写忽略读 0；wstrb 字节使能；读写通道序列化握手；复位全零（control 默认全关，防 X 传播）。单元级单时钟域，PS↔PL 跨时钟由 vision_top 评审定。黄金参考无（协议 tb：BFM 确定性拍数驱动）。
- `in_align.v`（2026-10-01 新增）：HDMI 输入归一化——ADV7611 解码流（pclk 同步并行 RGB + de/hs/vs，极性/位置随源）归一到 §3.1 流约定：de/rgb 直通；vs 边沿单拍化；hs 重定时为 de 拉低后第 HS_DLY 拍（默认 3，间隔 ≥3 且距下行首 de ≥1）；vs/hs 撞拍时 hs 让路顺延一拍不丢失。约束：源行消隐 ≥ HS_DLY+2 拍、raw vs 在场消隐内不与 de 重叠。tb_in_align 以丑流（hs 搭行尾 de、宽脉冲 vs、人为撞拍）验证全部间隔规则。
- `vision_top.v` v0.3（2026-10-01）：**双路径拓扑**——显示 rgb2gray（恒接）→ [gaussian] → [sobel] → [osd] → out_*（全分辨率）；快照分支 sobel 后分叉 → [scaler] → cop_*（DW×DH，R0 bit1 使能，M3 接乒乓行组缓冲）。全部旁路 mux 帧首 in_vs 锁存。**R0 位定义 v0.2：bit0 gauss_en / bit1 scaler_en（快照使能）/ bit2 osd_en / bit3 sobel_en**（sobel 串接于高斯 mux 后，可与 bit0 自由组合；bit0=0&bit3=1 即对 raw gray 做边缘）。时钟域：像素流 pclk、axi_regs s_axi_aclk（PS AXI_GP），R0 开关位 2FF 同步进 pclk，box/roi 多字节参数按 D10 帧首锁存口径。tb_top 六帧双通道 768+512 px 位精确。
- 回归入口：`bash sim/scripts/run_vision_iverilog.sh [rgb2gray|linebuf|gaussian|scaler|sobel|chain|fullchain|osd|axi|all]`（模块二独立 harness，不进模块一 `all`，tb 在 `sim/vision/`）。

### 3.2 级间标记约定 v0.2（tb_fullchain 通过后确立，10/5 评审确认）

- 每级自产输出标记 `out_vs/out_hs`，与 `out_de` 同拍传播给下级（`rgb2gray` 延迟 1 拍；`gaussian/sobel` 延迟 3 拍），vision_top 级联时无需额外标记管理。
- **直通行尾 hs 门控**：输出行 l 的行尾 hs = 输入行 l+1 的 hs；输入行 0 的 hs 不对应任何输出行，必须屏蔽——否则下游行计数错位（tb_fullchain 调试实录，2026-09-29）。
- **冲刷行标记**：gaussian/sobel 末行冲刷在 vblank 内自产合成 hs（`flush_start` 后延迟 3 拍输出，末像素后 1 拍）；冲刷 eff_de **推迟 2 拍启动**（flush_start 后 +3 拍起输出），与直通行尾 hs 保持间隔，避免下游同拍收到 de+hs 导致行错位（同日调试实录）。
- 下游（scaler 类行槽消费者）约定：hs 提交一行；已提交行数用寄存器 sticky（组合 hs 判据在挂起期不可见）；行坐标跨像素流水时末像素插值完成后才允许更新行坐标（pending 提交，见 scaler.v 注释）。
- 单元级参数 WIDTH=16/HEIGHT=8 为紧凑测试格式；接真实视频时参数放大即可，无需改 RTL 逻辑。

### 3.3 寄存器映射表 v1.0（2026-10-01 草案，10/5 评审冻结；坐标系 = 全分辨率显示图）

| 寄存器 | 位域 | 语义 |
|:---|:---|:---|
| R0 | `[0]` gauss_en / `[1]` scaler_en（**快照分支使能**，不 affect 显示）/ `[2]` osd_en / `[3]` sobel_en / `[31:4]` 保留 | 链路开关；2FF 同步进 pclk 后**帧首 in_vs 锁存**，帧内改不影响当前帧 |
| R1 | `[15:0]` box_x0 | 检测框左上 x（1px 描边框，重叠 box 优先） |
| R2 | `[15:0]` box_y0 | 检测框左上 y |
| R3 | `[15:0]` box_x1 | 检测框右下 x |
| R4 | `[15:0]` box_y1 | 检测框右下 y |
| R5 | `[7:0]` box_color | 检测框颜色（灰度值） |
| R6–R9 | `[15:0]` | roi_x0 / roi_y0 / roi_x1 / roi_y1 |
| R10 | `[7:0]` roi_color | ROI 框颜色 |
| R11–R15 | — | 保留：写忽略、读 0（`RESV_BASE=11`） |

- 多字节参数（R1–R10）跨时钟（s_axi_aclk → pclk）按 D10 口径：帧首锁存 + 帧边界生效吸收位偏差。
- M3 预留：CNN 推理结果回写 box 坐标（R1–R5）即完成 A3/A4 闭环，映射无需变更。

## 4. 关键定点参数（初稿）



| 参数 | 初稿值 | 备注 |
|:---|:---|:---|
| 灰度系数 | 77/150/29（>>8） | BT.601；评审可换 BT.709（46/157/53） |
| 高斯核 | 1/16 定点 | 移位实现，误差 ≤1 LSB |
| 缩放算法 | 双线性 | 最近邻作为 debug 档 |
| 行宽 | 1280（720p）候选 | 与分辨率选型联动 |
| 每级延迟 | 1–3 拍/级 | **稳态标记滞后**（§3.2 口径）；帧首像素延迟另计：窗口级（gaussian/sobel）有 **1 行结构滞后**（3×3 窗口需下一行流入才能算当前行，双行缓存设计使然）——tb_top A5 实测 gray=1 / gauss=行周期+4 / gauss+sobel=2×行周期+7（2026-10-01 校正） |

## 5. 开放问题（10/5 评审前必须定，阻塞 vision_top）

0. **scaler 时钟达标路径（2026-09-30 实测新增，同日②已实施）**：real 档 OOC（1280 行宽、NLINES=8/16 均测）WNS −7.4~−7.5 @10ns ≈57 MHz，不满足 720p60 的 74.25 MHz。worst path = 槽读数据 → 两级 8bit lerp → 输出寄存（20 级逻辑，主凶是 lerp 乘法综合成的 9 级 CARRY4 进位链，槽 mux 占比小——NLINES 16→8 实测无效）。可选：① **720p30 演示**（37.5 MHz 像素钟，现状即达标，零工作量）；② 插值链切一级流水（预寻址重排读时序；早期 x-lerp 提前拍三次尝试因行边界相位连环失配撤销）；③ 乘法改差值形式 / DSP 引导（收益不确定）。
   **✅ ② 已实施（2026-09-30，用户拍板 720p60 为正式目标）**：错半拍预寻址——ph0 发 x1 列地址、ph1 发下一像素 x0 地址，x 方向插值于 ph1 拍寄存，发射拍只剩 y 插值；**发射时刻与输出标记一拍不变**（行边界捕获用 pend 槽号、复位/帧边界 x_acc 置 INIT_X 保冷启动）。实测：iverilog 10/10 位精确（tb_scaler/fullchain/top 逐像素 0 错）；real 档 OOC **WNS −0.534 @10ns ≈ 94.9 MHz**，验收线 −3.47（=74.25 MHz）大幅达标。新 worst path = BRAM→槽 mux→x 插值→寄存（ph1 拍）。证据 `data/logs/2026-09-30-scaler-retiming/`。

1. **HDMI 输入通路选型**：ADV7611 需 I2C 初始化与 EDID（Ultra-Vision 经验）；用 Vivado 自带 DVI/HDMI IP 还是移植开源解码器；pclk 频率（720p60≈74.25 MHz / 1080p60≈148.5 MHz）。
2. **分辨率与色彩空间**：720p60 RGB444（推荐首发）还是 1080p；ADV7611 输出 RGB444 还是 YCbCr422（若是 422，rgb2gray 前需加色度变换级）。
3. **输出通路**：HDMI OUT 编码方案与像素复拍（148.5 MHz 下 10:1 TMDS 是否可行，x7z020 资源评估）。
   > 2026-10-01 阶段结论（M2 范围）：显示路径 = 全分辨率直通（v0.3 双路径），输入输出同为
   > 720p 格式，各级自产标记恒定延迟传递——**M2 不设输出时序发生器**，PL 侧直接以处理流的
   > vs/hs/de 驱动板上输出芯片并行总线；上板若实测源时序非标（in≠out 需重生成时序）再补
   > free-run 时序发生器档。TMDS 串化问题待原理图复核（D4）。
4. **模块三网络输入尺寸**（联动 §7）。
5. 上板分工：板务归 watercopper（根目录 [项目主计划](../../plan.md) §2），I2C 初始化脚本与 EDID 由谁维护需对齐。

## 6. 验证策略与黄金参考需求单（给 watercopper）

- 逐模块 tb：Python 黄金参考生成输入 hex 与期望 hex，tb 逐像素比对（`data/golden/` 归档生成脚本与数据）。
- 黄金参考需求：`rgb2gray`、`gaussian_3x3`（含边界填充）、`scaler`（两组尺寸档）各一份 Python 脚本 + 测试图（≥3 张：含斜线/棋盘/人脸纹理），输出 `data/golden/vision/<module>/`。
- 波形专项：帧边界切换参数不撕裂；`de` 无效期各级无输出副作用。
- A5 指标采集：逐像素延迟（理论值 vs 波形实测）、端到端帧延迟、资源（LUT/BRAM/DSP）。
- XSim 对拍口径沿用 Part B（`docs/partB-verify-plan.md` §6）：iverilog 全 PASS 后 XSim 复跑同判据。

## 7. 与模块三的衔接（给 jianglibo 的对齐点）

- `scaler` 输出尺寸 = CNN 输入尺寸；输出侧先落**乒乓行组缓冲**（BRAM）再喂 `cop_top`，接口形态（简单 valid/de vs AXI-Stream）等 `src/coprocessor/` 契约定稿后回写本文。
- A3 软/硬推理切换：PS 软件版与协处理器版同屏对比，依赖模块三暴露"推理完成"信号到 OSD 显示延迟数值。
- 权重加载：训练侧产出 hex 的位宽/排布必须与 `cop_top` 权重存储一致——见 `docs/module3-model-training.md`，训练侧在拿到协处理器契约前先按"INT8、权重排布可参数化"准备。

## 8. 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版草案：模块划分/接口初稿/定点参数/验证策略/开放问题，供 10/5 前评审 | never-die-cold（模块二 RTL） |
| 2026-09-30 | §5.0 ② scaler 插值链切拍实施（错半拍预寻址，WNS −0.534≈94.9 MHz 达标 720p60）；§3.1 scaler 口径同步 | never-die-cold（模块二 RTL） |
| 2026-10-01 | sobel 接入 vision_top（D7 缩放前，R0 位定义 v0.2）；新增 in_align 输入归一化模块；OOC 新增 real75（74.25 MHz）随访档 | never-die-cold（模块二 RTL） |
| 2026-10-01 | vision_top v0.3 双路径拓扑（显示全分辨率直通 + scaler 快照分支，§2 图更正）；双时钟域 s_axi_aclk/pclk + R0 位 2FF 同步（D10 落地） | never-die-cold（模块二 RTL） |
