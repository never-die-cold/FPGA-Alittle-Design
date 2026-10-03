# 2026-10-03 协作记录：无摄像头的 ARM 定位/裁剪基线

> 标签：#vision #架构决策 #工具链
> 平台：Codex desktop；相关基线：`8a2384c`，未提交新代码。

## 1. 任务与初始提示词

用户有 PYNQ 板卡、无摄像头，JL 负责 v1；用户确认开始 ARM 文件输入定位/裁剪基线。

## 2. 方案

第 0 步完成设计清单，见 `docs/arm-localize-baseline-plan.md`。
复用已有定位与缩放参考，标准库运行；按文件运行器、图片导出、便携包、板端实测拆步。
代码清单尚待用户确认；随后每步不超过 100 行并通过理解门槛。

## 3. 失败现象

当前终端没有 Python/Bash 的默认搜索路径。
直接执行 MSYS2 Bash 后，原入口因 `dirname` / `bash` 不在搜索路径退出 127，未进入测试。
在 PowerShell 调整 PATH 后同样失败，原始日志保留在本轮 data/logs 目录。

## 4. 纠错轨迹

通过 workspace dependency 工具定位 bundled Python；在 Bash 内显式设置 PATH 和 VISION_PYTHON。
仓库入口 `bash sim/scripts/run_iverilog.sh vision_python` 三项 PASS，退出 0。
原始日志：`data/logs/2026-10-03-arm-localize-baseline/pc-reference-baseline.log`。

## 5. 第 0 步结论与待办（历史快照）

已有 Python 参考与配置/报文回归在 PC 本次复跑通过。
未实现文件运行器/导出/便携包；ARM 实测未验证；实时 PL 图像、CNN 与工业服务未接入。
用户已提供 SSH 地址 `xilinx@169.254.87.99`（别名 `192.168.2.99`）。
受限网络首次尝试未能连接；允许网络访问后 SSH 可达，但免密认证失败，退出 255。
已在被 git 忽略的 `sim/build/arm-localize-ssh/` 生成专用密钥，待用户板端添加公钥。
尚未验证板端架构/Python；代码步骤等待清单确认。

## 6. 经验沉淀

复用已验证参考，先冻结输入/输出与计时口径；PC 测试通过不替代 ARM 性能实测。

## 7. 第 1 步交付（理解确认已通过）

用户回复“已经加上了”，完成专用公钥配置并继续先前开工指令。
SSH 环境为 armv7l / Python 3.10.4；私钥最初归沙箱用户、联网账户无读取权限，
修复 Windows 文件 ACL 后成功；私钥仍位于 git 忽略的 sim/build 目录。

新增运行器 `src/pynq_host/arm_localize.py`（52 行有效代码）、
测试 `sim/vision/test_arm_localize.py`（46 行）、回归循环接入 1 行，共 99 行。
固定输入与 PC/ARM JSON 结果归档 `data/evidence/2026-10-03-arm-localize-baseline/`。
Python 四项回归与跨平台数值对比通过；未修改 RTL，未 commit。

### 讲解稿

1. run() 读取 JSON 灰度矩阵，检查尺寸/标识与像素类型；拒绝输入输出同路径，防止覆盖源文件。
2. 定位与裁剪都调用原参考；bbox 是闭区间端点，因此宽高要加 1。
3. 复检状态保留原始框但 crops 为空；prepare_targets 本身也拒绝复检场景。
4. perf_counter_ns 在两个计算阶段边界采样，差值除 1e6 得毫秒；不把读写盘纳入计算延迟。
5. 输入 SHA256 和参考源码 SHA256 说明算的是哪个数据与算法；runtime 记录实际机器与 Python。
6. 测试验证精确框/像素、文件结果、来源、复检/空场景、非法像素/尺寸和防覆盖。
7. 对比固定数值与哈希，不比较依机器与调度变化的时间/运行环境字段。

### 原始结果与实际限制

`step1-arm-run.log`：PASS: file reference status=LOCATION_ONLY targets=2 crops=2。
`step1-arm-pc-compare.log`：PASS: ARM/PC boxes, crop pixels, parameters and input/reference hashes match。
ARM 12×8 合成图单次定位 1.240646 ms、两个 64×64 小图裁剪 259.325834 ms。
数值一致已验证；正式帧率与代表性输入性能未验证，PGM/hex 与便携包未实现。

### 第 1 步理解题

1. bbox=[1,1,2,4] 的原始框宽高是多少？如果用 x1-x0、y1-y0 而不加 1，会怎样？
2. 如果取消“输入与输出必须不同路径”的检查并指定同一路径，下次输入会发生什么？
3. PC 与 ARM 为什么比较像素/哈希，却不要求 timing_ms 与 runtime 完全相等？如果强制相等会怎样？

判定：三题通过。用户完整答案与上下文纠正在下文保存。

### 用户完整答案

#### 1. `bbox=[1,1,2,4]` 的宽高

如果这里 `bbox` 表示像素坐标下的 `[x0, y0, x1, y1]`，并且采用“像素包含端点”的约定：

- 宽：`x1 - x0 + 1 = 2 - 1 + 1 = 2`
- 高：`y1 - y0 + 1 = 4 - 1 + 1 = 4`

所以原始框是 **2 × 4**。

如果直接用：

- `x1 - x0 = 2 - 1 = 1`
- `y1 - y0 = 4 - 1 = 3`

会得到 **1 × 3**，宽高各少 1 像素。后果是框被缩小，面积从 `2*4=8` 变成 `1*3=3`，在裁剪、缩放、IoU、NMS、锚框匹配等任务中会漏掉边界像素，小目标尤其严重，极端情况下相邻坐标会得到 0 宽或 0 高。

但注意：如果坐标是连续几何坐标而不是像素端点坐标，则 `x1-x0`、`y1-y0` 才是正确宽高，不应加 1。关键看坐标约定。

#### 2. 输入与输出指定同一路径，下次输入会怎样？

如果取消“输入与输出必须不同路径”的检查，并让程序读写同一路径，通常会发生：

1. 第一次运行：程序读取原输入，处理后写回同一路径，**原文件被覆盖**。
2. 第二次运行：所谓“输入”已经是上一次的输出，不再是原始输入。
3. 如果处理是幂等的，比如固定尺寸缩放、灰度化，可能结果变化不大或相同。
4. 如果处理非幂等，比如锐化、模糊、旋转、加水印、增强、加噪、有损压缩，结果会**累积叠加**，图像越来越偏离原图。
5. 如果程序流式读写同一文件，还可能出现读到一半被写坏、文件截断、数据错乱。
6. 原图若没有备份，将无法恢复。

所以取消这个检查后，最大风险是：**输入被输出污染，下一次处理的是上次结果，而不是原始数据。** 正确做法是写临时文件，再原子替换，或强制输入输出不同路径。

#### 3. 为什么比较像素/哈希，却不要求 `timing_ms` 与 `runtime` 完全相等？

因为二者验证的目标不同：

- **像素/哈希**：验证功能正确性，即 PC 和 ARM 跑出来的结果是不是同一张图/同一份数据。
- **`timing_ms` / `runtime`**：验证性能，受硬件和环境影响极大。

PC 与 ARM 即使跑同一算法，也会有大量差异：

- CPU 架构不同：x86_64 vs ARM64
- SIMD 指令不同：AVX/SSE vs NEON/SVE
- 主频、核心数、大小核调度不同
- 缓存、内存带宽不同
- 操作系统、编译器、数学库版本不同
- 浮点舍入、FMA、并行归约顺序可能不同
- 后台负载、温度降频、IO、进程启动时间不同

所以 `timing_ms` 和 `runtime` 不可能也不应该要求完全相等。通常只要求：

- 像素完全一致，或在容差内一致；
- 哈希一致，或量化/规范化后一致；
- 时间在同一数量级，或不超过基线阈值，或用中位数、分位数、相对比例比较。

如果强制 `timing_ms` 与 `runtime` 完全相等，会导致：

- 测试极其脆弱，频繁误报；
- 跨平台 CI 几乎不可用；
- 为了“凑时间”可能加 sleep，反而失去性能测试意义；
- 无法区分真实性能退化和调度噪声；
- 可能鼓励作弊式实现。

结论：**正确性看像素/哈希，性能看统计阈值；跨平台不应强制时间完全相等。**

### 判定与上下文纠正

1. 正确：本项目像素 bbox 固定闭区间；用户能区分另一种连续坐标约定。
2. 正确理解防覆盖目的；本运行器具体输出 JSON 没有顶层 pixels，二次读取会缺字段失败，非图像变换累积。
3. 正确理解跨平台功能与性能判据分离；实际板端为 32 位 armv7l，本算法采用整数定点，要求像素精确相等。
三题通过，随后进入第 2 步。

## 8. 用户流程豁免与批量交付

用户原话：“这样子分步来走现在太慢且耗token，我想要一步到位，你先全部做完，然后把所有的三个问题集中起来我一块回答”。
按此明确指令，本轮剩余图片导出、便携包和性能实测连续完成，豁免单步行数与中间理解等待。
最后集中三题；提交仍待理解确认，不自动 commit。

图片采用 P5 二进制灰度与逐像素两位 hex，行优先，清单绑定目标/frame/config、尺寸和哈希。
导出写入独立批次目录；全部成功后原子发布 JSON，失败保留旧清单，消费者必须检查退出码。
已验证缺文件/篡改门禁、隔离包执行、非恒定像素顺序、复检后旧文件不被清单引用、导出失败不发布。
性能包含 tiny、720p_empty、720p_six，预热 1 次、测 5 次，保存每次原始输入/输出与统计。

首轮 PC 性能调用因 Python 3.13 mkdtemp 返回绝对路径、调用 output 为相对路径而失败。
修复为入口 resolve()，补充相对路径运行测试；最终 PC/ARM 使用同一修复版本便携包。
板端时钟与 PC 文件时间不一致导致首包 tar 时间警告；包文件元数据归零，避免依赖设备墙钟。
两次尝试的原始日志保留，最终交付只引用最终复验版本。

进一步在最终 CLI 复跑检出相同的相对路径问题：export_crops 的临时目录返回绝对路径。
运行器与导出函数也统一 resolve，补齐仓库及便携包相对路径 CLI 测试。
重新组包、重跑最终 PC/ARM 三场景，板端目录 final_v3，确保交付包与证据一致。

## 9. 最终交付、集中讲解与三题

文件运行器、图片/hex 导出、独立包及性能脚本全部完成；没有 RTL 改动，未提交代码。
五项 Python 回归 PASS；包在 PC/ARM 隔离运行和哈希校验 PASS。
最终三场景各预热 1 次、采样 5 次，15 个 PC/ARM 样本的框、像素、PGM/hex 字节、输入/参考哈希一致。
最终包 manifest 与板端归档 manifest 相同；详情见 docs/arm-localize-results.md。
板端为 Linux/armv7l/Python 3.10.4；720p 六目标 total_call 中位数 7894.934665 ms。
板端墙钟未同步，耗时采用单调钟，合成输入不代表真实相机精度或实时处理能力。

完整集中讲解保存为 docs/arm-localize-walkthrough.md，涵盖文件/图像顺序、原子清单、包版本与性能口径。
集中三题如下，等待用户一次作答：

1. PGM/hex 像素数量不变，但 hex 改成列优先、硬件仍按行优先读，会出现什么？
2. 新结果 RECHECK 而旧目录仍留图，为什么必须看当前 artifacts 和退出码，不能直接用旧图？
3. ARM 软件与未来协处理器对比时，locate/crop 和 total_call 能混着比较吗？如何保持输入、算法和计时边界一致？

实时 HDMI/PL 图像、正式模型、CNN 和工业检查服务未实现/未接入；后续不在本轮基线范围。
用户回答前不执行 git commit。

## 10. 最终理解门槛：用户完整答案

用户随后要求：“然后你细分多个commit提交，因为这次的文件变更有些大”。
以下保留用户答案原文；其中需收紧的细节见本节末尾判定。

### 1. hex 列优先写出、硬件行优先读取：像素数相同也会全错位

写出侧 `src/pynq_host/arm_localize.py:27-30` 先把 `pixels` 按 y 外层、x 内层展平（行优先），hex 再逐字节一行写出。若改成列优先，文件字节数和行数完全不变——**任何“数量/尺寸”校验都发现不了**，但字节序变成了转置置换：

- **宽高相等时（64×64 裁剪图是常态）**：硬件按行优先读入后得到的是原图的严格转置，x、y 全部对调。目标在 (50,10) 会出现在 (10,50)，bbox、连通域形状全错，而且转置后仍是“一张正常的图”，肉眼和结构性检查都不报错——是最隐蔽的一类静默失败。
- **宽高不等时（如测试里的 2×2、4×3）**：字节索引 k 的语义在两边不一致（文件里是 第 k//H 行第 k%H 列，硬件当成 第 k//W 行第 k%W 列），得到的是扭曲错排图，同样数量对、内容全错。
- **特例更危险**：像 `test_arm_localize.py:18` 那种常值行 `[[20]*4]*3`，转置后完全相同，框对得上也查不出序错误。所以测试专门加了非对称 2×2 图（值 0/64/128/255 全不同）钉死顺序——`test_arm_localize.py:32-35` 断言 hex 必须是 `00\n40\n80\nff\n`，列优先会写成 `00\n80\n40\nff\n`，立即 FAIL。

也就是说，这类错误只能靠**内容级**手段抓：导出文件的 SHA256（artifacts 里逐文件记录）、PC/ARM 字节全等比对（`compare_arm_localize_bench.py:33-37`）、以及固定顺序测试。只校验像素数量等于 W×H 会放行。

### 2. RECHECK 时为什么必须看当前 artifacts + 退出码，不能用旧图

代码是按“清单即结果”设计的，三点环环相扣：

- **每轮独立目录、旧目录刻意不清理**。`arm_localize.py:24` 每次 `mkdtemp` 新建批次目录；旧批次保留作历史证据（walkthrough 第 26 行明确“旧目录可作为历史证据保留，但不能当作当前结果”）。所以目录里“有图”不代表“图属于本次”。
- **RECHECK 时本次清单就是空的**。`arm_localize.py:58` 只有 `LOCATION_ONLY` 才生成 crops，RECHECK_* 状态 `crops=[]` → 当前 JSON 的 `artifacts=[]`。`test_arm_localize.py:40-47` 对 `RECHECK_TARGET_LIMIT`、`RECHECK_BORDER` 都断言了这一点；36-39 行还证明换了参数重跑后旧图仍留在盘上但不在新清单里。直接扫目录挑图，拿到的就是上一次运行、另一组参数下的产物，来源无法追溯（没有本次输入/参考的 SHA256 关联）。
- **失败时不发布新清单，旧 JSON 会留在原地**。`main` 出错返回 1（`arm_localize.py:91-93`），异常发生在原子替换之前，输出路径上那份 JSON 是**上一轮成功运行**留下的。`test_arm_localize.py:61-76` 专门验证：非法输入和注入的导出失败后，`result.json` 字节原封不动。不查退出码，就无法分辨盘上 JSON 是“本次写的”还是“上次的遗物”。中途失败还可能留下未被任何清单引用的批次文件（walkthrough 第 28 行）。

正确消费协议只有一条：退出码为 0 → 读当前 JSON → **只用 `artifacts[]` 里列出的文件**（按需核对 sha256）。旧目录一律不进本次结论。

### 3. locate/crop 与 total_call 不可混比：边界不同，比值会被系统性歪曲

计时边界在代码里是明确切开的：`arm_localize.py:55-59` 的 `locate`/`crop` 只包住 `reference.locate` 和 `prepare_targets`（输入读取、JSON 解析在 `start` 之前；导出图片和发布 JSON 在 `finished` 之后）；`arm_localize_bench.py:60-67` 的 `total_call` 才是整个 `run()` 的墙钟，含输入读取、参数校验、PGM/hex 导出和 JSON 发布。拿实测数字看差距有多大——720p 六目标 ARM 侧 locate+crop ≈ 5552 ms，total_call ≈ 7895 ms，**差出的 ~2.3 s（约 42%）全是宿主机 I/O/导出开销**。

不能混比的原因：未来协处理器替代的只是计算核，ARM 的文件读写、校验、导出这些 Python 开销既不会被 PL 消掉，也不属于加速器的工作量。拿协处理器的纯计算时间去比 ARM 的 total_call，会虚报约 1.4 倍加速比；反过来拿端到端时间去比协处理器计算时间，又会虚贬。混用后不同人对不上同一个数。

保证公平的做法（现有基建已埋好一半）：

1. **边界同名同义、分开报告**：locate/crop 只和协处理器的纯计算比；total_call 只和协处理器“含 DMA 读 720p 帧 + 写回裁剪结果”的端到端比。报告里写明各自包含什么、排除什么（进程启动、组包、SSH、显示、相机延迟两边都不计，见 results 文档“计时与限制”）。
2. **输入逐字节相同**：固定合成三场景，PC/ARM 每个样本都校验输入 SHA256（`compare_arm_localize_bench.py:26-27`）。
3. **算法与参数版本一致**：`reference_sha256` 强制相等（:15），warmup/repeats、场景列表、threshold/min_area/max_targets 等字段逐一断言相等（:16-19、:28）。
4. **先验结果正确再谈时间**：PGM/hex 字节全等 + 哈希比对（:30-37）；计时和 runtime 从不作相等判据（脚本头注释）。跑得快但结果错没有意义。
5. **钟源与方法统一并声明**：统一 `perf_counter_ns` 单调钟（板端墙钟未同步），预热 1 次、采样 5 次、p95 用最近秩且注明“五样本 p95=max，不代表长期稳定性”。

一句话总结：三题其实是同一条纪律——**结果以“当前清单 + 退出码”为准，不认盘上残影；顺序以内容哈希为准，不认数量巧合；性能以对齐的计时边界为准，不跨边界比快**。

### 判定：三题通过，授权拆分提交

用户能够解释行列顺序、复检/失败消费协议及计算/总调用计时边界；最终理解门槛通过。
以下为精度澄清，不改变通过判定：

- 2×2 是方形；列优先索引 k 对应原图 x=k//H、y=k%H，行优先读取位置为 x=k%W、y=k//W。
- 自己生成并自己核对的 SHA256 只能验证文件完整性；语义顺序仍需要已知正确内容或可信参考对比。两个平台共用同一错误也可能一起通过，非对称固定测试用于补足这一点。
- 总调用与计算阶段差额还含参数/像素验证、序列化等，不能全部归为 I/O；各阶段中位数之和也未必等于逐样本计算之和的中位数。
- 文件读取/发布流程与仅含 DMA 的流程不自动构成同边界端到端比较；需对齐实际运算、数据入口出口和宿主操作，再分别报告。
- CNN 与定位/裁剪不是同一计算任务；未来只加速 CNN 时，不能以当前定位/裁剪时间作为 CNN 加速比分母。

提交设计：运行器与导出 → 性能脚本与比较 → 便携部署与隔离测试 → 文档、完整原始证据及理解记录。
每个代码 commit 注明 AI prompt 要点；不修改已验收包内源文件，不推送远端。

## 11. 完整集中讲解稿（最终归档副本）

# ARM 文件定位基线：集中讲解与理解题

日期：2026-10-03。用户明确要求剩余工作一次完成，三题集中作答；最终三题已通过，并授权拆分提交。

## 从文件到结果

`arm_localize.py` 将输入/输出解析为绝对路径，避免不同 Python 版本的目录行为差异。
拒绝输入输出同路径，检查 GRAY8 整数矩阵、尺寸及标识，然后调用已有定位参考。
参考用阈值寻找亮背景上的暗区域，再用 4 连通确定面积和原图坐标下的闭区间 bbox。
达到最小面积的区域进入目标列表；触边/目标过多保留复检状态，不生成分类小图。
定位与裁剪代码均为原参考；64×64 为本次测试尺寸，没有冻结正式网络契约。

## PGM、hex 与结果清单

裁剪是原参考的中心对齐定点双线性。每目标同时保存 JSON 像素、P5 PGM 和 hex。
PGM 头说明宽高与 255 最大值；后面一个像素一个字节。
hex 每行一个两位十六进制像素，可供后续测试/权重输入约定参考，不代表已经接上 RTL。
两者均先遍历 y，再遍历 x，即逐行从左到右。
artifacts 保存每个目标的 frame/config/target 标识、bbox、尺寸、路径与文件 SHA256。
输入与参考实现 SHA256 保存在结果顶层，使数据和算法版本可追溯。

## 为什么保留独立批次目录

每次运行创建独立目录，先写完所有图片，再将 JSON 原子替换为本次结果。
消费者只能使用当前 JSON 的 artifacts，不能扫描目录挑“最新图片”。
空场景或 RECHECK 的清单为空；旧目录可作为历史证据保留，但不能当作当前结果。
输入非法或导出失败时返回非零，不发布新清单；上一份成功 JSON 仍可能存在，必须检查退出码。
中途失败可能留下未引用的批次文件；它们不属于已发布结果。
所有 PC 中间文件与测试依据都在仓库目录内；没有使用工作区外临时文件验证。

## 便携包与回归

`make_arm_localize_pkg.py` 用显式白名单组包：运行器、原参考、自检、性能脚本、固定图和说明。
manifest 保存基线 commit 和逐文件哈希；私钥及环境依赖不入包。
`arm_localize_selftest.py` 先校验完整文件清单和哈希，再核对固定框、像素及导出。
用 Python `-I` 隔离执行验证无需完整仓库、用户 PYTHONPATH、OpenCV、torch 或 PYNQ。
专项测试接入 `run_iverilog.sh vision_python` 和 all；验证非法输入、像素顺序、旧文件隔离、
失败不发布、缺/改文件门禁以及仓库/便携包的相对路径 CLI。
本轮没有 RTL 改动，执行的是五项 Python 回归和板端软件验证。

## 性能与跨平台一致性

性能脚本生成 tiny、720p_empty、720p_six 三种固定合成场景；各预热一次、测五次。
locate/crop 为对应计算阶段，total_call 还含输入读取、参数/像素验证、导出与 JSON 发布。
进程启动、组包、SSH 传输、图案生成、显示和相机延迟均不计入 total_call。
五次样本的 p95 用最近秩法，等于 max；不是大量样本下的分位数估计。
原始输入、每次结果和文件保留，15 组 PC/ARM 样本按数值、文件字节和哈希比较。
耗时与 runtime 不作相等判据；ARMv7l 与 Windows PC 的性能分别报告。
板端墙钟尚未同步，报告日期采用用户会话日期，耗时采用 perf_counter_ns 单调钟。
纯 Python 实测只能作为软件参考基线；没有实现实时相机、PL 图像读取、CNN 或工单服务。

## 集中三题

1. PGM/hex 都保存同样的像素数。若把 hex 改为按列优先写，而硬件仍按行优先读，会出现什么？
2. 新一轮结果为 RECHECK，旧批次目录还留着图片。为什么必须看当前 artifacts 和进程退出码，不能直接使用旧图？
3. 比较 ARM 软件与未来协处理器时，locate/crop 与 total_call 能混着比较吗？你会怎样保证输入、算法与计时边界一致？

最终回答与判定完整归档于 report/llm_log/2026-10-03-arm-localize-baseline.md。三题通过，按用户要求拆分提交。

## 12. 拆分提交与提交前复验

- 17002c7：文件定位运行器、原子 PGM/hex 导出、固定输入及功能测试；208 行新增，1 行删除。
- f6c61db：合成场景性能采样和 PC/ARM 精确内容比较；145 行新增。
- ca3245f：标准库便携组包、完整性自检、隔离测试、操作说明及回归接入；195 行新增，1 行删除。
- 最后一组提交包含本轮文档、完整原始日志和证据，包含有明确标识的历史尝试；其 commit ID 由 Git 历史记录，避免文档自引用哈希。

再次执行仓库入口 bash sim/scripts/run_iverilog.sh vision_python，退出码 0：

    PASS: PS configuration staging/commit/ack/busy/timeout/epoch wrap mock protocol
    PASS: localization empty/multiple/non-grid/noise/limit/border + per-target crop/resize/frame metadata
    PASS: M2 HTTP mock config/status/location + frame/config/session/stale/error contract
    PASS: file localization exact boxes/crops, metadata, empty/recheck and invalid input
    PASS: PGM/hex exact row order, hashes, target association and stale manifest isolation
    PASS: ARM portable package（路径见原始日志）
    PASS: isolated portable package, missing/tampered file gate and retained benchmark samples

上述第一条仅为摘要；原始文字与完整组包路径以 commit-python-regression.log 为准。
再次执行 compare_arm_localize_bench.py 比较 pc-benchmark 与最终 arm-board-final 的 benchmark，退出码 0：

    PASS: PC/ARM benchmark 3 cases, 15 samples, exact boxes/pixels/PGM/hex/hashes

原始输出保存于 data/logs/2026-10-03-arm-localize-baseline/commit-python-regression.log 与 commit-benchmark-compare.log。
每组执行 git diff --cached --check；最终另核对工作区与暂存区。源文件与验收包版本保持逐文件哈希一致。
证据归档时发现部分 Python 临时批次目录只允许创建账户读取；为这些仓库内目录补充本机 Git 账户的读取权限，重新暂存全部文件。
证据目录新增局部 .gitattributes：原始证据不转换换行，PGM/压缩包标记二进制，防止像素及 JSON/manifest 哈希在检出时改变。
暂存后用 git checkout-index 将本轮证据检出至 sim/build/commit-evidence-check，再运行已入库的比较脚本及板端归档自检：

    PASS: PC/ARM benchmark 3 cases, 15 samples, exact boxes/pixels/PGM/hex/hashes
    PASS: portable package hashes, exact localization/crops and PGM/hex

对应原始输出为 commit-index-evidence-compare.log 与 commit-index-package-selftest.log；manifest、便携包、板端完整压缩归档 SHA256 与最终报告全部相同。
检查 git diff --cached --check 通过；CRLF 原始证据用局部 cr-at-eol 检查，保留其它默认空白检查。
用户只要求 commit；本轮不推送远端。未实现/未接入清单仍为实时图像读取、正式分类模型、CNN 和工业检查服务。
