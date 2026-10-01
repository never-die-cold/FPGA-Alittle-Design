# 模块二离板推进清单（2026-10-01）

用户授权：模块二除实际板上操作外的工作均可推进，包括原 watercopper 的离板任务。
本清单已核对根 plan.md、核计划、v0 核契约和两分支视觉实现；代码步骤待用户确认。

## 1. 分支与真实起点

已执行 git fetch origin。main、dev/rtl、dev/bench、dev/verify 均为 8408ecc；
dev/vision 为 d5ccd7e，相对 dev/verify 领先 11 个提交、落后 0 个提交。
dev/vision 已在独立工作树中检出，复验前后源码工作区均干净。
后续以 d5ccd7e 为代码起点，接续已有工作，避免重复实现。

- ✅ 本次复验：dev/verify 现有视觉 10/10 tb PASS；dev/vision 13/13 tb PASS。
- ✅ dev/vision 已覆盖：缩放切拍、缩小档、Sobel 接入、输入归一化单元、
  显示/快照双路径、帧边界拓扑锁存、乒乓缓冲正常场景。
- 🟡 已有实现但验证不足：异步配置、缓冲拥塞/覆盖、PS 软件与真实寄存器协同。
- 🟡 历史顶层 OOC 综合 WNS=+2.934 ns @13.468 ns；未复跑，非布局布线结果。
- ⬜ 未实现 / 未接入：彩色原图显示、in_align 与系统顶层的组合接入、
  配置整组原子提交、帧/检查标识贯通、真实定位与逐目标裁剪、CNN 应用衔接。
- ⬜ 未验证：真实 HDMI/采集卡闭环、整机指标；这些保留给板上验收。

## 2. 必须先补的验证缺口

1. tb_top 的 s_axi_aclk 接 clk，不能证明异步 CDC（跨时钟域）安全；框参数
   从 AXI 寄存器直连像素域，帧首锁存不能保证多个寄存器属于同一次配置。
2. tb_cop_buf 三帧像素完全相同，无法识别旧帧/串帧；需覆盖读启动与写完成
   同拍、长时间拒收、写快于读、消费后停写、不同帧内容和复位。
   源码存在读启动/写翻转同拍导致缓冲所有权冲突的候选路径，尚未 tb 复现。
3. run_vision_xsim.sh 用 grep 匹配 PASS/FAIL/fatal 判断退出；FAIL 行也能使
   grep 返回成功，且没有 pipefail。已有 PASS 本次未据此推翻，失败门禁需修复。
4. report_cdc 归档只有报告头；不可将空报告当作安全证明。需检查同步器属性、
   实际跨域端点与复位释放；OOC 综合正裕量不能替代 post-route 时序验收。
5. 当前“显示双路径”仍输出 8 位灰度，与主计划保留彩色相机画面的目标有差距。
   内部单拍 vs/hs 标记也不能直接视为完整 HDMI 输出同步波形。

## 3. 开工顺序与单步上限

每行只交付一个功能点；如估算超限，先细拆再实现。每步讲解、出题、等回答。
源目录范围：src/vision、sim/vision、sim/scripts、data/golden/vision；
软件离板任务可涉及 src/pynq_host、data/scripts。证据在 data/logs/data/evidence。

| 顺序 | 单步交付物 | 文件范围 | 代码估算 | 验证 |
|:---|:---|:---|:---|:---|
| 1 | 回归入口失败门禁；统一入口增加 vision 模式 | sim/scripts | ≤80 行 | 缺 tb/编译失败/仿真 FAIL 必须非零；正常 13/13 |
| 2 | 不同帧内容的缓冲争用 tb | sim/vision、sim/scripts | ≤95 行 | 同拍启动/提交定向复现；失败也完整存证 |
| 3 | 按上步证据修缓冲所有权 | cop_buf.v、对应 tb | ≤90 行 | 无串帧、可继续消费、全量 PASS |
| 4 | 真异步时钟的配置 tb | sim/vision、sim/scripts | ≤95 行 | 不同频率/相位，帧边界附近更新 |
| 5 | 冻结配置提交/确认与丢帧可见性契约 | design_v0.md、docs | 仅文档 | 对照 PS 软件与 RTL 字段 |
| 6 | 配置发送侧影子寄存器/提交请求 | axi_regs.v、tb | ≤95 行 | 源侧握手；端到端待接收侧 |
| 7 | 像素侧整组锁存/确认 | vision_top.v、tb | ≤95 行 | 异步整组一致性、全量 PASS |
| 8 | 彩色原图显示端口与独立分析路径 | vision_top.v、tb_top.v | ≤95 行 | RGB 逐像素一致，分析 golden 不变 |
| 9 | 输入归一化与双路径组合顶层 | src/vision、sim/vision | ≤95 行 | 先组合/编译；完整视频时序 tb 后续单步补 |
| 10 | 真实尺寸/连续帧压力 tb | sim/vision、golden、scripts | ≤95 行 | 720p→占位 CNN 尺寸、槽复用/消隐预算 |
| 11 | 顶层 post-route 与 CDC 报告门禁 | sim/scripts | ≤95 行 | WNS/WHS、约束覆盖、DRC、BRAM、CDC |
| 12 | PS 配置绑定与 mock 联调 | src/pynq_host、sim | ≤95 行 | 提交/确认/帧号遵循新契约 |

后续离板工作：帧标识贯通、定位黄金参考与逐目标裁剪契约、复现包。
这些按实际接口继续拆成 ≤100 行步骤，不把整帧缩放记为逐目标裁剪完成。
实际上板、相机采样和实机延迟不计入离板完成率；CNN 网络/算子等待模块三契约。

## 4. 证据与提交纪律

原始日志见 data/logs/2026-10-01-vision-offboard/README.md。
代码步骤尚未开始，未创建提交、未合并分支、未改另一工作树的源码。
涉及 RTL 的回归需接统一 run_iverilog.sh 入口，并保留视觉专项入口。
用户确认步骤后开工；未经用户确认理解不提交。

## 5. 完成记录（2026-10-02）

§2/§3 所列缺口已全部处理，证据在 data/logs/2026-10-02-vision-offboard/README.md：

1. 失败门禁 `sim/scripts/vision_gate.sh`（退出码+PASS+无失败文本三条件）接入
   统一 `run_iverilog.sh all` 与视觉/Python/XSim/Vivado 入口，8 例故障注入自检。
2. cop_buf 所有权修复：`writing` 标志 + 回放银行保护；tb_cop_buf_stress 以不同
   帧内容复现同拍启动/提交、拥塞、排空、复位半帧，修复前日志留存为 copbuf-before.log。
3. 整组原子配置：axi_regs AW/W 独立握手 + R11 提交/busy（busy 提交回 SLVERR）+
   R12 已应用编号；config_bridge 请求/确认 toggle 两级同步（ASYNC_REG），稳定总线
   `set_max_delay -datapath_only` 约束；vision_top 帧首整组应用，去帧内二次锁存。
4. 彩色显示直通 display_*（RGB 恒延迟 + display_frame_id），分析路径独立；
   video_pipeline 组合 in_align + seen_frame 门控；vision_axi 处理 Digilent RBG
   字节序与 video_locked 复位。
5. sobel 加一级打拍（gauss+sobel 49→50 拍）。
6. tb_video_real 真实 720p 两帧（1,843,200 显示像素 + 100,352 快照像素逐像素核对）、
   tb_patterns 非恒定图案、tb_vision_axi 字节序/lock-loss。
7. OOC post-route 门禁（CDC 逐条核对、稳定总线 max_delay）：WNS=+0.330/WHS=+0.027，
   复检 +0.629/+0.009；物理 HDMI 工程 bitgen 成功、时序约束全满足、DRC 0 错误；
   XSA 导出失败（批处理模式已知行为）不影响 bitstream，详见日志 README。
8. PS 侧 vision_regs.commit/wait_applied/status + mock 协议测试（提交/确认/busy/
   超时/回绕）；定位黄金参考 reference.py（4 连通分割 + bbox + RECHECK 状态 +
   逐目标 crop_resize，与 scaler 定点口径互验）+ test_localize.py。
9. src/vision_client Windows EXE 原型（PyInstaller 打包、MOCK 标注、UVC 不叠加
   未关联结果）+ 本地 HTTP mock 服务联调。

仍未实现/未接入（留给模块三与上板）：CNN/协处理器接口、逐目标硬件裁剪、
实际定位部署、真实相机采集与端到端指标。
