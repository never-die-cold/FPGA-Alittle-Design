# 改进建议快速批次：执行与证据（2026-10-15）

基线 `dev/model@891cba2`，未 commit/push，未生成或下载板端位流。
用户要求“根据以上改进建议开工”，第 1 步理解三题通过后又明确要求
“启用快速模式，少回答，多做，最后统一回答”。因此本批次按古法编程技能的
快速模式豁免取消逐步出题和 100 行节流；验证与可复现性要求保留。
另一会话也在同一工作区修改 C01；其单帧驱动替身、板端入口测试及独立复核记录均保留。

## 本批次实现

| 项目 | 改动 | 验证边界 |
| --- | --- | --- |
| CNN 几何/watchdog | 无符号 8 位尺寸；启动锁存最后允许周期 | 528 组几何、每控制器 82 组精确周期 |
| CNN 面积 | 16 路 requant 改为 2 路流水分时，尾通道错误屏蔽保持 | 8075 requant 黄金及完整 Conv/FC/网络 |
| CNN 调度 | 参数每输出块读一次；每 3 个 CE 拍读一组，MAC 返回独立累加 | 保持每组 INT32 溢出拒绝；CE/abort/timeout/reset 恢复 |
| JALR | 独立 rs1+原始 I 立即数加法器，再清 bit 0 | 36,880 ID+EX 用例；SoC 综合布局布线 |
| cop_buf | 读列计数替代 `% DW` | 8×4、非 2 幂 3×3/7×3 压力测试 |
| 定位 | 双倍半整数中值、INT32 平方距离，标量阈值边界校正 | 与旧 float64 norm 逐像素一致，含 nextafter 阈值 |
| EXE | HTTP/重握手由单工作线程执行，GUI 采纳队列快照 | 延迟 HTTP 时主循环可继续；手动请求不丢、过期撤框 |
| LIVE 服务 | 原型自动轮次内存检查；手动/诊断及非原型轮次归档；复用分类器 | 真实模型黄金、手动产物、两次自动结果一致、模型只加载一次 |
| C01 Park | 新增显式 opt-in 候选，槽 1→0→1 后运行中复制 | 替身验证；真实 IP 事件与槽/写事务绑定仍未证明 |
| 仓库卫生 | 根生成报告移入此目录；根路径忽略规则 | 原报告 SHA256 保留，未改证据内容 |

`src/coprocessor/conv_engine.v` 保持一拍同步读接口、地址布局、整数舍入、错误及完成语义。
读请求仍只有一个同步返回槽，MAC 内部允许多个已发射组；没有声称每拍发射或实现 6～8 倍加速。
新增 `watchdog` 专项及非 2 幂缓冲、C01 Park 替身均通过现有根回归入口接入。

## CNN 实测

同一 Vivado 2026.1、xc7z020clg400-1、10 ns 时钟与 1 ns I/O 延迟约束。

| 指标 | 10/13 原版 | 本批次 |
| --- | ---: | ---: |
| 整网周期（含每 7 拍停 1 拍） | 1,123,109 | 472,593 |
| 两组网络逐元素匹配 | 各 73,795 元素 | 各 73,795 元素 |
| 参数读/网络 | 每像素重复读取 | 10 组 |
| DSP | 192 | 136 |
| LUT | 10,100 | 4,540 |
| FF | 6,940 | 4,037 |
| BRAM | 0 | 0 |
| WNS / ns | +0.058 | +0.317 |
| WHS / ns | +0.049 | +0.123 |
| 严重 DRC | 0 | 0 |

仿真周期约缩短 57.9%，同向量约 2.38 倍；DSP 减少 56，控制器占器件 61.8%，剩余 38.2%。
综合门禁已从 220 收紧为 176。控制器 OOC 不包括实体存储、DMA、视频或完整 SoC；
不能据此宣称整机所有资源通过 20% 余量门禁，也不能宣称板端延迟或 ARM 加速倍数。
WNS 没有达到另一 agent 预估的 +1.5 ns；以实际报告为准。
当前最差路径为 `q_send` 经共享通道选择到 requant DSP 乘法级，见最终 OOC `worst_paths.rpt`；
后续若再提升频率，可评估重量化操作数寄存及其新增周期，本次未继续改动已通过的流水接口。

原始 `cnn-all.txt` / `.exit.txt` 为完整算子与两组网络回归，退出 0。
`cnn-ooc.txt` 对应 `../cnn-ooc-1cefffc05185438195b8803d87fc11df/`（旧 220 门限）；
`cnn-ooc-gate176.txt` 对应 `../cnn-ooc-a96a8b86f6264e50af90da61e3dc3aa9/`（最终 176 门限）。
每个 OOC 目录包含精确源码/Tcl/包装脚本快照、manifest、退出码及原始时序/资源/DRC。

## SoC 与软件

`rtl-focused.txt` / `.exit.txt`：ID+EX 36,880 例，cop_buf 三组参数压力用例，退出 0。
`soc-build.txt` / `.exit.txt`：40 MHz bht2 SoC、默认 Verilog 解析综合与布局布线，退出 0。
WNS +6.613 ns；LUT 6,846、FF 859、BRAM36 tile 8、DSP 0。
约束与输入 SHA256 见 `soc-inputs.json`，冻结 RTL 位于 `inputs/riscv/`；报告在
`../2026-10-13-soc-reset-ce/vivado/fast_jalr_20261015/`。
此前同入口复位/CE 优化报告为 +6.447 ns；本次只做 40 MHz，不能推出更高主频或板端已更新。

`localize.txt`、`rounds.txt`、`service.txt` 与 `software-exits.json`：三个专项均退出 0。
`inspection-all.txt` / `.exit.txt`：14 组重依赖离板检查均通过，退出 0；最后一组用真实 FP32 模型
验证自动内存结果与手动归档结果一致且分类器只加载一次。FILE 后端仍为 `prototype=true`。
核对 C04 Q3 后将跳过图片归档明确限定为 prototype；`service-engine-final.txt` / `.exit.txt`
复验最终代码，退出 0。完整视觉 Python 最终复验见 `vision-python-final.txt` / `.exit.txt`。
视觉 Python 最终共 19 组，通过且退出 0，其中包含另一会话新增的 C01 顺序/入口替身。
`client-build.txt` / `.exit.txt`：现有固定依赖下重建 Windows EXE，退出 0；打包运行、
HTTP 手动/自动轮次及截图、EXE×LIVE FILE 服务联合、FILE REPLAY 全部门禁通过。
完整分发目录为 `sim/build/vision-client/dist/vision_preview/`，须连同 `_internal` 使用，
包内文件哈希见 `client-package-manifest.json`；未实测真实相机或板端吞吐率。
`park-candidate.txt` / `.exit.txt`：初版 Park 替身通过；后加暖机粘滞及复制期间粘滞故障纳入最终总回归。

## 最终全量状态

`rtl-all.txt` 为 `bash sim/scripts/run_iverilog.sh all` 的完整原始输出，
`rtl-all.exit.txt` 为 **0**：核、CNN、视觉 RTL 和视觉 Python 全量 PASS，日志含 133 行 PASS。
其中四档 benchmark/CoreMark 周期均与第 1 步及既有基线逐拍一致：

| 配置 | benchmark 周期 | CoreMark 周期 |
| --- | ---: | ---: |
| 无转发 / BHT 关 | 2,850 | 19,057,438 |
| 转发 / BHT 关 | 2,423 | 17,114,141 |
| 转发 / BHT1 | 2,380 | 16,335,562 |
| 转发 / BHT2 | 2,351 | 16,232,079 |

日志中的既有 timescale/数组敏感列表警告、网络故障注入 WARN 不表示门禁失败。
`git-diff-check.txt` / `.exit.txt`：退出 0；源文件、SoC/OOC 输入及归档、模型/夹具/固件
共 89 项哈希检查无差异，见 `source-stability-check.json` / `.exit.txt`。
44 个最终源码/测试/入口文件与 `verification-inputs.json` 一致，其中 3 个 C01 测试标记为
`parallel_session_dependency`，随共享回归入口归档以保证基线回放完整；未覆盖另一会话改动。
结构化结果见 `results.json`。没有 git commit/push 或板端验收。

## 复现命令

```text
bash sim/scripts/run_iverilog.sh all
bash sim/scripts/run_iverilog.sh coprocessor watchdog
bash sim/scripts/run_inspection_python.sh
powershell.exe -NoProfile -File sim/scripts/run_cnn_ooc.ps1
vivado -mode batch -source sim/scripts/build_soc_ab.tcl -tclargs fast_jalr_reproduce src/riscv 40 bht2
```

Windows 实测 Bash 为 `C:/msys64/usr/bin/bash.exe`，先导出
`PATH=/ucrt64/bin:/usr/bin:$PATH`；Python 为现有 Python 3.12.10，NumPy 2.5.1、OpenCV 5.0.0，
通过 `VISION_PYTHON` 与 `COPROCESSOR_PYTHON` 指定。Icarus Verilog 13.0 stable。
模型使用现有 `models/cnn-border-fill-best.pt`，未训练或替换权重。
模型、合成夹具与两份 benchmark/CoreMark 固件哈希见 `payload-inputs.json`；
真实引擎的结果、模型元数据、代码哈希和运行时版本另存 `service-engine-result.json`。
所有日志、输入、tb 和脚本均在仓库内；局部 `.gitattributes` 保留原始输出及快照字节。
`verification-inputs.json` 和 `inputs/` 保存本批次源码/测试/入口的 SHA256 与完整文件，
`changes.patch` 是所列路径的 tracked diff，新增文件另在 `inputs/` 中保存。
在基线副本重放时，按 manifest 将 `inputs/<path>` 覆盖回对应仓库相对路径，再运行上述入口；
共享回归所需的另一会话新 C01 测试也已完整包含。
原根报告归档为 `legacy-tight-setup-hold-pins.txt`，SHA256 为
`a3639f4217ca3e50a493ef3d3c9ab9555a2e9fa826185319b172087fb667390e`。

## 明确未实现 / 尚未验证

- **未实现同步 BRAM DMEM**：v1 契约 §8 及 C03 规定 MEM 地址驱动同拍异步读，核外口没有
  提前地址、read-enable 或等待握手。直接把 `dmem.rdata` 改时序块会使 WB 读取上一条地址；
  提前读取方案需要核/SoC/MMIO 路径一起设计与验证，不能作为本次等价面积优化静默接入。
- **未实现 CDC/reset 改写、未清零原有 CDC 报告**：config_bridge 是稳定总线加 toggle/ack，
  与逐位同步或只改两个 ASYNC_REG 寄存器不同。必须保持配置跨帧提交、AXI 配置在视频失锁时保留、
  pclk 停止时异步复位等契约；本次未重出 C01 位流，不能宣称消除原报告 8 Critical/35 Warning。
- **未缩小 224×224 视觉快照**：C03 的逐目标 64×64 ROI 由 PS 定位后裁剪产生，和整帧快照用途不同。
- **未实现 CNN 实体 BRAM/窄参数装载口、MMIO/DMA/cop_top、核工业固件或整机硬件 LIVE**。
  另一建议的 RAMB18E1 512×64 SDP 配置不可用；后续须按真实原语位宽/端口数做银行布局及集成时序。
- **C01 Park 仅候选**：实际 IRQ、当前槽、完整帧及 DDR 写响应的绑定、BGR/无混帧/长测和正式 N03
  仍待 JL/WC 审查与 NC 实机。默认 single 驱动保持；不得全局忽略 DMAIntErr 或宣称返板一次通过。
- 没有实测 ARM 端延迟、真实 UVC 30 FPS、整机吞吐率、数据集精度或 M2/M3 验收结果。

细节与快速模式豁免见[协作记录](../../../report/llm_log/2026-10-15-improvements-fast.md)。
