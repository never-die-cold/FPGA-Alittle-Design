# vision design_v0 —— HDMI 图像预处理流水线接口设计（前期草案）

> 是什么：模块二（HDMI 直通 + 预处理流水线）的模块划分、接口与验证策略。
> 给谁看：never-die-cold（模块二 RTL，本文维护者）、watercopper（黄金参考与测试数据，第 6 节需求单）、jianglibo（第 7 节模块三衔接）。
> 什么时候读：接口对接与上板联调时；10/5 评审按 §3.3/§4 现行口径升格冻结契约（对齐 design_v1.md 的流程）。
> 状态：**离板实现已收口（2026-10-02），接口待 10/5 评审冻结**。§3.1/§3.3/§4 为已实现口径，§5 未决项仅剩上板类。上游依据：`src/vision/README.md` 模块清单、`docs/proposal_upgrade.md` A 档任务、`docs/track_research.md` §1.4 Ultra-Vision 参考。

## 1. 目标与范围

M2 目标：HDMI 输入 → 预处理链 → HDMI 输出的实时直通演示，含 A1 参数化；A2 直通/帧缓存对比数据按 §2 备注 2 口径保留测量档。

（历史注：原计划 Part B 收口前不写 RTL；实际单元级于 2026-09-28 起超前实现，2026-10-02 离板收口。）

## 2. 数据通路（直通架构，A2 的对照项之二）

```text
dvi2rgb HDMI IN ──pclk──> in_align 输入对齐/24bit RGB ──┬──> 彩色原图恒延迟直通 display_* ──> rgb2dvi ──> HDMI OUT（全分辨率）
                                                        │
                                                        └──> rgb2gray ──> gaussian_3x3 ──> [sobel 可选] ──┬──> [osd] ──> out_*（灰度诊断口，不驱动物理 HDMI）
                                                                                                          └──> [scaler] ──> cop_buf 乒乓帧缓冲 ──> cop_*（快照，喂模块三）
        axi_regs（s_axi_aclk 暂存 R0–R10）──> R11 提交 ──> config_bridge 跨时钟 ──> 帧首整组应用/确认（R12 配置编号）──> 像素域 active_cfg
```

> 注 1：sobel 位置 2026-09-30 决策单 D7 定为缩放前（gaussian 之后）——全分辨率上做边缘，
> 缩放后 224 小图边缘信息已损失；原初稿画在 scaler 后，已按 D7 更新。
> 注 2：拓扑 2026-10-01 定为**双路径**（对齐 2026-09-21 叙事决策「行缓存直通显示 + 片上快照
> 推理」）——scaler 不串在显示路径（224 小图不上屏）；2026-10-02 显示路径升级为**彩色原图
> 恒延迟直通**（display_*），灰度 out_* 口降级为诊断流。
> 注 3：物理前端 2026-10-02 定案——PYNQ-Z2 无 ADV7611，PL 经 dvi2rgb/rgb2dvi 直接收发
> TMDS（Digilent IP 钉版 f4613fff）；`vision_axi.v` 负责 Digilent RBG 字节序与内部 RGB 互转。

- 默认**免帧缓存直通**（对齐 Ultra-Vision 创新点 1 与 A2）：全链在输入像素时钟域逐像素推进，逐像素延迟固定可测。
- A2 对比项保留帧缓存路径（经 PS DDR）作为测量档，不在 M2 主线实现，10/5 后按人力定。
- 每级旁路开关由 `axi_regs` 配置（A1 参数化），开关切换在帧边界生效（消隐期切，避免撕裂）。

## 3. 模块划分与接口初稿

统一像素流约定（初稿，评审定稿）：同 `pclk` 单时钟域；`de`（data enable）+ `hsync/vsync`；像素 `RGB[23:0]`；后级灰度域 `Y[7:0]`。无 ready 反压——直通链逐拍推进；AXI-Lite 配置跨时钟域由 `config_bridge` 请求/确认握手整组传递（2026-10-02，替代初稿 2FF 同步器）。

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
- `axi_regs.v`：AXI-Lite 从机参数寄存器堆（NREG=16，映射见 §3.3：R0 控制开关 / R1–R5 检测框 / R6–R10 ROI / R11 提交-busy / R12 已应用编号 / R13–R15 保留）。要点：**AW 默认 7，须满足 2^AW > NREG*4**——AW=6 时地址空间恰好被寄存器占满，越界判别永远无法触发（tb 实测教训，2026-09-29）；保留区写忽略读 0；wstrb 字节使能；AW/W 通道独立捕获握手（任意顺序、响应反压，2026-10-02）；复位全零（control 默认全关，防 X 传播）。本模块只在 AXI 域；整组配置 CDC 由 vision_top 内 config_bridge 实现。黄金参考无（协议 tb：BFM 确定性拍数驱动 + tb_axi_split 乱序/反压）。
- `config_bridge.v`（2026-10-02 新增）：src/dst 双时钟整组配置握手——src_commit 锁存 hold_data/hold_id 并 toggle request，dst 在帧首应用整组并回送 acknowledge（双方 ASYNC_REG 两级同步）；确认前稳定总线恒定，约束为 `set_max_delay -datapath_only`（见 config_cdc.xdc），不用异步 clock group 掩盖。tb_config_bridge 以不同频率/相位时钟验证原子性、busy 拒绝、复位。
- `reset_sync.v`（2026-10-02 新增）：异步声明、两级同步释放，每个时钟域各一（pixel_reset/axi_reset）。
- `in_align.v`（2026-10-01 新增）：HDMI 输入归一化——解码后并行流（pclk 同步 RGB + de/hs/vs，极性/位置随源；物理前端 = dvi2rgb，板上无 ADV7611）归一到 §3.1 流约定：de/rgb 直通；vs 边沿单拍化；hs 重定时为 de 拉低后第 HS_DLY 拍（默认 3，间隔 ≥3 且距下行首 de ≥1）；vs/hs 撞拍时 hs 让路顺延一拍不丢失。约束：源行消隐 ≥ HS_DLY+2 拍、raw vs 在场消隐内不与 de 重叠。tb_in_align 以丑流（hs 搭行尾 de、宽脉冲 vs、人为撞拍）验证全部间隔规则。
- `cop_buf.v`（2026-10-01 新增，§7 占位实现；2026-10-02 所有权修复）：快照帧乒乓缓冲——scaler 流写入双帧 BRAM（2×DW·DH·8bit），读侧 1 像素/拍整帧原子回放为 vs/hs/de 流；`cop_ready` 是整帧启动许可（帧内不中断）。所有权规则：`writing` 门控写使能（复位后无帧首的半帧不写不发布）；in_vs 覆写待消费帧先撤销 buf_valid 并计 drop_count；正在回放或本拍启动回放的银行禁止成为写银行（读启动与写完成同拍的串帧路径已封死）。回放携带该银行的 frame/config id。**接口为占位**：cop 契约定稿后按 §7 换封装（valid/de vs AXI-Stream），存储体不动。tb_cop_buf（乒乓/门控）+ tb_cop_buf_stress（异帧争用/拥塞/排空/复位半帧）双 tb 覆盖，修复前失败证据 `data/logs/2026-10-02-vision-offboard/copbuf-before.log`。调试实录：末像素兼行尾时 else-if 链漏设 hgap → raddr 越界续发（iverilog 抓到 120px/XSim 行为不同），修正为行尾判据主、帧尾置 finishing。
- `vision_top.v` v0.4（2026-10-02）：**彩色直通 + 灰度分析 + 快照三线拓扑**——display_* 彩色原图恒 1 拍直通（带 display_frame_id，分析开关/缩放/消费反压均不影响）；分析 rgb2gray → [gaussian] → [sobel] → [osd] → out_*（灰度诊断口）；快照 sobel 后分叉 → [scaler] → cop_buf → cop_*（DW×DH，R0 bit1 使能，cop_ready 整帧许可）。**配置整组原子化**：R0–R10 暂存 → R11 提交 → config_bridge 帧首整组应用并回送 R12 配置编号（busy 期间重复提交回 SLVERR）；拓扑开关取自 active_cfg，帧内不再二次锁存（bridge 已按帧锁存）。时钟域：像素流 pclk、配置 s_axi_aclk，各自 reset_sync。**R0 位定义 v0.2：bit0 gauss_en / bit1 scaler_en（快照使能）/ bit2 osd_en / bit3 sobel_en**。tb_top 六帧双通道位精确（gauss+sobel 首像素延迟 50 拍）；tb_top_async 异步配置、tb_top_color 彩色逐像素。video_pipeline 并行边界 OOC post-route WNS **+0.330** @13.468ns（综合档历史值 +2.9 不再引用）。
- `video_pipeline.v`（2026-10-02 新增）：in_align + seen_frame 门控（首个 vs 前不放行分析路径）+ 显示原始同步/RGB 寄存直通 + vision_top 组合的物理前端边界顶层；不含 TMDS 电气收发。
- `vision_axi.v`（2026-10-02 新增）：Vivado AXI-Lite 封装——Digilent RBG↔内部 RGB 双向字节序、AXI 地址折叠与 snapshot_debug 汇聚；`create_hdmi_bd.tcl` 以其挂接 PS7/dvi2rgb/rgb2dvi。**复位拓扑（2026-10-03 上板挂死修复）**：像素域 rst_n 并入 video_locked（断源即复位视频通路）；axi_rst_n 只随 s_axi_aresetn——锁定丢失时 AXI 在途响应必须照常完成、已提交配置保留（恢复后未确认提交在首帧生效），否则 axi_regs 带血复位、PS 总线挂死（实机表现：串口/网口同死）。tb_axi_lock_reset 定向覆盖（基线/写在途/读在途/恢复保持），修复前失败证据 `data/logs/2026-10-03-vision-onboard/axi-lock/axi-lock-before.log`。
- 回归入口：`bash sim/scripts/run_iverilog.sh all`（核 + 门禁自检 + 22 视觉 tb + Python，失败门禁三条件）与 `bash sim/scripts/run_iverilog.sh vision [单项|all]`（视觉专项）。

### 3.2 级间标记约定 v0.2（tb_fullchain 通过后确立，10/5 评审确认）

- 每级自产输出标记 `out_vs/out_hs`，与 `out_de` 同拍传播给下级（`rgb2gray` 延迟 1 拍；`gaussian` 3 拍；`sobel` 4 拍——2026-10-02 算术和打拍后），vision_top 级联时无需额外标记管理。
- **直通行尾 hs 门控**：输出行 l 的行尾 hs = 输入行 l+1 的 hs；输入行 0 的 hs 不对应任何输出行，必须屏蔽——否则下游行计数错位（tb_fullchain 调试实录，2026-09-29）。
- **冲刷行标记**：gaussian/sobel 末行冲刷在 vblank 内自产合成 hs（`flush_start` 后延迟 3 拍输出，末像素后 1 拍）；冲刷 eff_de **推迟 2 拍启动**（flush_start 后 +3 拍起输出），与直通行尾 hs 保持间隔，避免下游同拍收到 de+hs 导致行错位（同日调试实录）。
- 下游（scaler 类行槽消费者）约定：hs 提交一行；已提交行数用寄存器 sticky（组合 hs 判据在挂起期不可见）；行坐标跨像素流水时末像素插值完成后才允许更新行坐标（pending 提交，见 scaler.v 注释）。
- 单元级参数 WIDTH=16/HEIGHT=8 为紧凑测试格式；接真实视频时参数放大即可，无需改 RTL 逻辑。

### 3.3 寄存器映射表 v1.1（2026-10-02 原子配置修订，10/5 评审冻结；坐标系 = 全分辨率显示图）

| 寄存器 | 位域 | 语义 |
|:---|:---|:---|
| R0 | `[0]` gauss_en / `[1]` scaler_en（**快照分支使能**，不影响彩色显示）/ `[2]` osd_en / `[3]` sobel_en / `[31:4]` 保留 | 链路开关；写入进暂存区，R11 提交后**帧首整组生效** |
| R1 | `[15:0]` box_x0 | 检测框左上 x（1px 描边框，重叠 box 优先，灰度诊断口） |
| R2 | `[15:0]` box_y0 | 检测框左上 y |
| R3 | `[15:0]` box_x1 | 检测框右下 x |
| R4 | `[15:0]` box_y1 | 检测框右下 y |
| R5 | `[7:0]` box_color | 检测框颜色（灰度值） |
| R6–R9 | `[15:0]` | roi_x0 / roi_y0 / roi_x1 / roi_y1 |
| R10 | `[7:0]` roi_color | ROI 框颜色 |
| R11 | `[0]` 提交位 / 读回 busy | 写 1 提交 R0–R10 整组快照；busy 期间重复提交回 SLVERR；读取 `[0]`=busy |
| R12 | `[31:0]` applied_config_id | 只读：最后已确认生效的配置编号，复位 0，成功提交递增（回绕） |
| R13–R15 | — | 保留：写忽略、读 0 |

- 配置时序语义（2026-10-02 离板修订，详见 §4）：暂存区写入不立即生效；软件须 commit 并等待
  R12 递增确认，无视频帧时 busy 保持、须超时报错（`VisionRegs.commit()/wait_applied()`）。
- M3 预留：CNN 推理结果回写 box 坐标（R1–R5）即完成 A3/A4 闭环，映射无需变更。

## 4. 关键定点参数（初稿）

### 离板修订：配置整组提交（2026-10-02）

`vision_top` 使用原子配置模式：R0–R10 为 AXI 域暂存寄存器，写入不立即生效。
R11（0x2C）低字节 bit0 写 1 提交整个快照；读取 bit0 为 busy。
busy 时重复提交返回 SLVERR，不覆盖在途快照；暂存区仍允许编辑下一组配置。
R12（0x30）只读，返回最后已确认生效的配置编号，复位为 0，成功提交递增。
像素域在输入帧首整体应用快照，回送确认；无新帧时 busy 保持，软件须超时报错。
R13–R15 仍保留。独立 axi_regs 默认旧模式，保留区行为兼容；顶层开启原子模式。
跨域使用请求/确认 toggle 的两级同步器（ASYNC_REG），数据总线在确认前保持。
该稳定总线需约束及 CDC 审查，不能用异步 clock group 掩盖数据不一致。

缓冲采用整帧接收许可，帧内不中断：cop_ready 是启动许可，不是逐像素 ready。
拥塞允许覆盖未消费帧，禁止覆盖正在回放的帧；读启动本拍也算已占用。
当前整帧缩放/缓冲不代表逐目标裁剪、CNN、HDMI 物理接口或工业检查已实现。



| 参数 | 初稿值 | 备注 |
|:---|:---|:---|
| 灰度系数 | 77/150/29（>>8） | BT.601；评审可换 BT.709（46/157/53） |
| 高斯核 | 1/16 定点 | 移位实现，误差 ≤1 LSB |
| 缩放算法 | 双线性 | 最近邻作为 debug 档 |
| 行宽 | 1280（720p）候选 | 与分辨率选型联动 |
| 每级延迟 | 1–4 拍/级 | **稳态标记滞后**（§3.2 口径）；帧首像素延迟另计：窗口级（gaussian/sobel）有 **1 行结构滞后**（3×3 窗口需下一行流入才能算当前行，双行缓存设计使然）——tb_top A5 实测 gray=1 / gauss=行周期+4 / gauss+sobel=2×行周期+8（2026-10-02 sobel 打拍后校正） |

## 5. 开放问题（10/5 评审前必须定，阻塞 vision_top）

0. **scaler 时钟达标路径（2026-09-30 实测新增，同日②已实施）**：real 档 OOC（1280 行宽、NLINES=8/16 均测）WNS −7.4~−7.5 @10ns ≈57 MHz，不满足 720p60 的 74.25 MHz。worst path = 槽读数据 → 两级 8bit lerp → 输出寄存（20 级逻辑，主凶是 lerp 乘法综合成的 9 级 CARRY4 进位链，槽 mux 占比小——NLINES 16→8 实测无效）。可选：① **720p30 演示**（37.5 MHz 像素钟，现状即达标，零工作量）；② 插值链切一级流水（预寻址重排读时序；早期 x-lerp 提前拍三次尝试因行边界相位连环失配撤销）；③ 乘法改差值形式 / DSP 引导（收益不确定）。
   **✅ ② 已实施（2026-09-30，用户拍板 720p60 为正式目标）**：错半拍预寻址——ph0 发 x1 列地址、ph1 发下一像素 x0 地址，x 方向插值于 ph1 拍寄存，发射拍只剩 y 插值；**发射时刻与输出标记一拍不变**（行边界捕获用 pend 槽号、复位/帧边界 x_acc 置 INIT_X 保冷启动）。实测：iverilog 10/10 位精确（tb_scaler/fullchain/top 逐像素 0 错）；real 档 OOC **WNS −0.534 @10ns ≈ 94.9 MHz**，验收线 −3.47（=74.25 MHz）大幅达标。新 worst path = BRAM→槽 mux→x 插值→寄存（ph1 拍）。证据 `data/logs/2026-09-30-scaler-retiming/`。

1. **HDMI 输入通路选型**：~~ADV7611 需 I2C 初始化与 EDID~~ ✅ 2026-10-02 定案：PYNQ-Z2 无 ADV7611（原依据有误，board/hardware.md 已修正），PL 经 dvi2rgb 直接收 TMDS，DDC/EDID 在 PL；Digilent IP 钉版 f4613fff，物理工程已布线出 bit。
2. **分辨率与色彩空间**：✅ 720p60 RGB444（dvi2rgb vid_pData 并行 RGB，rgb2gray 前无需色度变换级）。
3. **输出通路**：✅ rgb2dvi（PixelClk 经 MMCM 生成 TMDS 串行钟），显示路径同格式直通；M2 不设输出时序发生器（2026-10-01 阶段结论见下）。
   > 2026-10-01 阶段结论（M2 范围）：显示路径 = 全分辨率直通（v0.3 双路径），输入输出同为
   > 720p 格式，各级自产标记恒定延迟传递——**M2 不设输出时序发生器**，PL 侧直接以处理流的
   > vs/hs/de 驱动板上输出芯片并行总线；上板若实测源时序非标（in≠out 需重生成时序）再补
   > free-run 时序发生器档。TMDS 串化问题待原理图复核（D4）。
4. **模块三网络输入尺寸**（联动 §7）。
5. 上板分工：板务归 watercopper（根目录 [项目主计划](../../plan.md) §2），I2C 初始化脚本与 EDID 由谁维护需对齐。

## 6. 验证策略与黄金参考需求单（给 watercopper）

> 2026-10-01 分工变更：never-die-cold 兜底测试数据项（用户确认"watercopper 的我也能做"），以下为闭环状态。

- 逐模块 tb：Python 黄金参考生成输入 hex 与期望 hex，tb 逐像素比对（`data/golden/` 归档生成脚本与数据）。✅ 持续执行
- 黄金参考需求：`rgb2gray`、`gaussian_3x3`（含边界填充）、`scaler`（两组尺寸档）各一份 Python 脚本 + 测试图（≥3 张：含斜线/棋盘/人脸纹理），输出 `data/golden/vision/<module>/`。
  - ✅ scaler 两组尺寸档：放大档 16x8→32x16（既有）+ **缩小档 32x16→8x4**（`scaler_ds/`，行槽复用路径首次覆盖，iverilog+XSim 双口径 PASS）
  - 🟡 真实测试图：替换通路已就绪（`data/scripts/img2hex.py`，任意图→指定尺寸 BT.601 灰度 hex）；真实照片待拍（自拍斜线/棋盘/人脸纹理各一，img2hex 入库即可）
- 波形专项：帧边界切换参数不撕裂；`de` 无效期各级无输出副作用。✅ 已有等价覆盖——前者 = tb_top 帧锁存验证（帧内改 R0 当前帧不变），后者 = 逐帧**精确**像素计数（任何 de 无效期副作用都会使计数或 golden 比对 FAIL）
- A5 指标采集：逐像素延迟（理论值 vs 波形实测）、端到端帧延迟、资源（LUT/BRAM/DSP）。
  - ✅ 逐像素延迟：tb_top 断言实测（窗口级 1 行结构滞后模型，metrics.csv 已填）
  - ⬜ 端到端帧延迟：需上板（OSD 帧计数/GPIO 打点，board/hardware.md §3.4 口径）
  - ✅ 资源：OOC utilization rpt 两批（unit/real/real75）
- XSim 对拍口径沿用 Part B（`docs/partB-verify-plan.md` §6）：iverilog 全 PASS 后 XSim 复跑同判据。**✅ 已执行（2026-10-01 12/12；2026-10-02 全部 22 tb）**：一键入口 `bash sim/scripts/run_vision_xsim.sh all`，证据 `data/logs/2026-10-02-vision-offboard/xsim-recheck.log`。

## 7. 与模块三的衔接（给 jianglibo 的对齐点）

- `scaler` 输出尺寸 = CNN 输入尺寸；输出侧先落**乒乓行组缓冲**（BRAM）再喂 `cop_top`，接口形态（简单 valid/de vs AXI-Stream）等 `src/coprocessor/` 契约定稿后回写本文。
  **2026-10-01 预实现**：`cop_buf.v`（乒乓帧缓冲 + cop_ready 反压）已落地并通过双口径 tb——契约冻结时若接口形态不同，仅需改 cop_buf 读侧封装（存储与写侧不动）；M3 可参照 tb_cop_buf 的 vs/hs/de 消费时序设计。
- A3 软/硬推理切换：PS 软件版与协处理器版同屏对比，依赖模块三暴露"推理完成"信号到 OSD 显示延迟数值。
- 权重加载：训练侧产出 hex 的位宽/排布必须与 `cop_top` 权重存储一致——见 `docs/module3-model-training.md`，训练侧在拿到协处理器契约前先按"INT8、权重排布可参数化"准备。

## 8. 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版草案：模块划分/接口初稿/定点参数/验证策略/开放问题，供 10/5 前评审 | never-die-cold（模块二 RTL） |
| 2026-09-30 | §5.0 ② scaler 插值链切拍实施（错半拍预寻址，WNS −0.534≈94.9 MHz 达标 720p60）；§3.1 scaler 口径同步 | never-die-cold（模块二 RTL） |
| 2026-10-01 | sobel 接入 vision_top（D7 缩放前，R0 位定义 v0.2）；新增 in_align 输入归一化模块；OOC 新增 real75（74.25 MHz）随访档 | never-die-cold（模块二 RTL） |
| 2026-10-01 | vision_top v0.3 双路径拓扑（显示全分辨率直通 + scaler 快照分支，§2 图更正）；双时钟域 s_axi_aclk/pclk + R0 位 2FF 同步（D10 落地） | never-die-cold（模块二 RTL） |
| 2026-10-02 | 离板收口修订：§2 拓扑图改彩色直通三线 + dvi2rgb/rgb2dvi 前端；§3.1 新增 config_bridge/reset_sync/video_pipeline/vision_axi 口径、cop_buf 所有权修复、vision_top v0.4；§3.3 寄存器映射升 v1.1（R11 提交/R12 配置编号，废 D10 2FF/帧首锁存口径）；§5 开放问题 1–3 定案（板上无 ADV7611） | never-die-cold（模块二 RTL，ZCode/GLM 协助整理） |
