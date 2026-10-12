# CNN 协处理器 v0：C02 整数与硬件契约

> 状态：**JL 已于 2026-10-11 定稿冻结，允许进入 J02**；仍不是 RTL、正式 INT8 模型或 M2 验收证据。
> 初稿日期：2026-10-10。适用首网：FastenerCNN，预处理版本
> `scene-gray-border-padding-v1`。
> 本文冻结网络、整数语义、张量排布和资源目标；核/PS 接口见
> [C03 契约](../../docs/coprocessor-integration-v0.md)。正文中的“固定/必须/不得”均为 v0 规范性要求。

## 1. 已有事实与未实现边界

### 1.1 已有可复现依据

- [FP32 逐层参考](../../docs/module3-prototype-reference.md)已验证网络结构、BN 折叠、形状和 MAC。
- [ROI 契约](../../docs/inspection-v0-contract.md)及[离板检查](../../docs/offline-inspection.md)
  记录了与交付原函数的 24 组逐像素对拍；输出为 64×64 `uint8`。
- [训练/量化准备](../../docs/module3-model-training.md)记录的两次 INT8/QAT 演练证明工具链能导出
  权重、scale 和整数累加结果。
- 上述 INT8 演练不是本网络的正式量化参数；FP32 hex 不能送入 INT8 MAC。

### 1.2 当前仍未实现

- 正式 PTQ/QAT、逐层整数黄金和生产权重包；
- MAC、卷积地址生成、缓存、bias、ReLU、requant、GAP、FC RTL；
- 128 MAC @100 MHz 的综合、时序、资源和实测延迟；
- 与核、PS、DMA、固件及真实数据的集成。

## 2. 首网与逐层形状

类别编号固定为 `0=bolt、1=nut、2=washer`。卷积是 OIHW 权重上的互相关，
不翻转卷积核；空间 padding 为 1 个实数零，因激活 zero-point 为 0，整数填充值也为 0。

| 层 | 算子 | 输入 CHW | 输出 CHW/C | 权重 | bias | MAC |
|:---|:---|:---|:---|---:|---:|---:|
| input | `pixels/255` 后量化 | 1×64×64 | 1×64×64 | 0 | 0 | 0 |
| conv1 | 3×3, s2, p1 + ReLU | 1×64×64 | 16×32×32 | 144 | 16 | 147,456 |
| conv2 | 3×3, s1, p1 + ReLU | 16×32×32 | 32×32×32 | 4,608 | 32 | 4,718,592 |
| conv3 | 3×3, s2, p1 + ReLU | 32×32×32 | 32×16×16 | 9,216 | 32 | 2,359,296 |
| conv4 | 3×3, s1, p1 + ReLU | 32×16×16 | 64×16×16 | 18,432 | 64 | 4,718,592 |
| gap | 16×16 空间平均 | 64×16×16 | 64 | 0 | 0 | 0 |
| logits | Linear 64→3，无 ReLU/softmax | 64 | 3 | 192 | 3 | 192 |
| 合计 | | | | **32,592** | **147** | **11,944,128** |

GAP 另有 16,320 次整数加法和 64 次除以 256。首版不支持 dilation、group/depthwise、
pooling、残差、动态形状或批量大于 1 的单次算子调用。

## 3. 量化类型与尺度

### 3.1 类型

| 对象 | 类型与范围 | scale / zero-point |
|:---|:---|:---|
| 输入/中间激活/输出 logits | 有符号 INT8，有效范围 `[-127,127]` | 每张量一个正 scale；zero-point=0 |
| Conv/FC 权重 | 有符号 INT8，固定 `[-127,127]` | 每输出通道一个正 scale；zero-point=0 |
| Conv/FC bias | INT32 | `S_bias[oc] = S_in × S_weight[oc]`，zero-point=0 |
| MAC 累加 | INT32 二补码 | 与 bias 相同 |
| requant multiplier | 正 INT32 | 与右移位数共同近似尺度比 |
| GAP 和性能计数 | INT32/UINT32 | 见对应章节 |

激活排除 `-128`（C02-P3），使“对称”在正负两侧严格一致，也避免绝对值和乘法边界的特殊分支。
所有 scale 必须为有限正数，禁止 NaN、Inf 或 0。

### 3.2 输入量化

预处理输出像素 `p` 为 `uint8[0,255]`，实数输入 `x=p/255`。正式导出工具按下式产生
首层 INT8 输入，禁止把 `uint8` 位模式直接解释为 `int8`：

```text
q_input = sat_i8_sym(round_away_from_zero((p / 255) / S_input))
```

`S_input` 来自正式量化模型/manifest，不由 RTL 猜测。ROI 预处理本身仍按
`scene-gray-border-padding-v1` 执行，量化是其后的独立步骤。

### 3.3 bias 量化

BN 先在 FP32 模型中折叠到 Conv 权重和 bias。每个输出通道：

```text
bias_q[oc] = int32(round_away_from_zero(bias_fp32[oc]
                                        / (S_in * S_weight[oc])))
```

导出器必须拒绝超出 INT32 的 bias，并证明该层所有合法输入下
`bias_q + sum(q_input*q_weight)` 不溢出 INT32。RTL 不允许依赖二补码回绕获得结果，
也不在每次乘加后饱和；合法模型的累加必须精确落在 INT32 范围内。

## 4. 舍入、右移和饱和的逐位定义

### 4.1 舍入到最近、正好一半远离零

全链固定采用 round-to-nearest、ties-away-from-zero（C02-P5）。对有符号整数 `v` 除以 `2^s`：

```text
round_shift(v, 0) = v
mag                = abs(v)
rounded_mag        = (mag + 2^(s-1)) >> s       // s > 0，逻辑右移
round_shift(v, s)  = (v < 0) ? -rounded_mag : rounded_mag
```

因此 `+2.5→+3`、`-2.5→-3`。软件参考应用无界整数或已检查的 INT64；RTL 应先扩展符号，
不得用对负数直接加正偏置再算术右移的近似写法。

### 4.2 requant

导出器为每个输出通道给出 `multiplier[oc]`（1…`2^31-1`）和
`shift[oc]`（0…62），近似 `S_in*S_weight[oc]/S_out`。行为固定为：

```text
product = int64(acc) * int64(multiplier[oc])
scaled  = round_shift(product, shift[oc])
q_out   = sat_i8_sym(scaled)
```

其中：

```text
sat_i8_sym(x) = -127, x < -127
                 127, x >  127
                   x, otherwise
```

multiplier/shift 的搜索算法可演进，但二者的最终整数值必须进入模型 manifest、二进制参数包
和逐层黄金；RTL 只执行上式。乘法中间值必须是有符号 64 位，不得截成 32 位。

### 4.3 Conv、ReLU、GAP 与 FC 顺序

- Conv：`INT32 bias + MAC → INT32 ReLU(max(acc,0)) → per-channel requant → INT8`。
- FC：`INT32 bias + MAC → per-channel requant → INT8 logits`，不做 ReLU/softmax。
- GAP：每通道对 256 个非负 conv4 INT8 值作 INT32 求和，再执行
  `round_shift(sum,8)`；输出沿用 conv4 的激活 scale，结果仍为 INT8。
- 因 multiplier 为正，Conv 的 ReLU 放在 requant 前与饱和后的非负结果一致；契约固定前者，
  便于负累加提前归零。

## 5. 最终类别、整数 score 与低置信

最终类别取三个 INT8 logits 的最大值；相等时取最小类别编号。令 `top1` 和 `top2`
为最大、次大整数 logit：

```text
margin_q  = uint8(top1 - top2)                 // 0..254
score_q15 = floor((margin_q * 32767 + 127) / 254) // 0..32767，正数半值向上
```

`score_q15` 是**归一化整数 logit margin，不是 softmax 概率**。C03 LIVE 服务若采用该方案，
上报 `score=score_q15/32767.0`，并在模型 manifest 中记录语义。低置信由
`margin_q < min_margin_q` 判定；阈值只能由不含 test 集的开发/校准集冻结。

该映射是已冻结的 C02-P7。若后续版本要求概率，软件可由三个反量化 logits 做经校准 softmax，
但不得在未改契约时把 margin 冒充概率，RTL v0 也不增加指数/除法单元。

## 6. 张量与参数排布

### 6.1 黄金参考的规范排布

- 像素：HW 行优先；激活：CHW，C 顺序逐元素；
- Conv 权重：OIHW；FC 权重：OI；bias/scale/multiplier/shift：O；
- hex 每行一个元素，INT8 用两个十六进制字符，INT32 用八个字符，按数值位模式书写；
- 多字节二进制文件采用 little-endian；manifest 必须声明 dtype、shape、layout、字节数和 SHA256。

逐层黄金保存完整张量；“前 64 个值”只能作为人工抽查，不能替代 RTL 逐元素对拍。

### 6.2 硬件激活排布 `C8HW8`

片上中间激活按 8 通道打包：`[channel_block][y][x][lane]`，其中
`channel = 8*channel_block + lane`。线性元素地址为：

```text
index = (((channel_block * H + y) * W + x) * 8 + lane)
```

不足 8 通道的 lane 填整数 0。为避免把 4,096 B 单通道 ROI 膨胀为 32,768 B，v0 DMA
固定传输规范 HW INT8；输入装载器保存 4,096 B，读取时把像素送 lane0，并为 lane1–7
直接生成 0。conv1 之后的中间激活才实际按 C8 排布存储。

### 6.3 8×16 MAC 权重排布

阵列每拍消费 8 个输入通道、计算 16 个输出通道。Conv 权重打包顺序固定为：

```text
[out_block16][ky][kx][in_block8][out_lane16][in_lane8]
```

FC 等价为 `ky=kx=0`。不存在的输入/输出通道权重填 0。每个最内层块为
16×8=128 字节，`in_lane` 变化最快，精确线性下标为：

```text
index = (((((out_block*KH + ky)*KW + kx)*in_blocks + in_block)*16
          + out_lane)*8 + in_lane)
```

各层权重、bias、multiplier、shift 均从 64 字节边界开始；实际 offset/length 写入
manifest，不由 RTL 依赖隐含拼接。

生产权重由运行时 DMA 装载；`$readmemh` 只用于仓库内 tb/诊断，不作为板端正式装载通路。

## 7. 缓存、资源和周期预算

### 7.1 容量预算

| 项目 | v0 契约容量 | BRAM36 粗预算 |
|:---|---:|---:|
| 激活 ping 缓冲（最大 conv2） | 32,768 B | 8 |
| 激活 pong 缓冲（最大 conv1/conv4） | 16,384 B | 4 |
| 填充后的五层 INT8 权重 | 34,432 B | 9 |
| bias/multiplier/shift/描述符 | 约 1.5 KiB | 1 |
| 单 ROI 输入双缓冲 | 8,192 B | 2 |
| 小计，不含 FIFO/CDC/debug | 约 93 KiB | **约 24** |

BRAM36 以 4,096 个 8 位有效数据估算；最终数量以综合推断为准。中间特征图默认只驻留 BRAM，
不逐层回写 DDR；debug dump 是显式模式，不能成为正常性能路径。

### 7.2 计算周期预算

| 层 | 8×16 阵列调度拍数 |
|:---|---:|
| conv1 | 9,216 |
| conv2 | 36,864 |
| conv3 | 18,432 |
| conv4 | 36,864 |
| FC | 8 |
| Conv+FC 合计 | **101,384** |

纯 MAC 理想下界为 `ceil(11,944,128/128)=93,314` 拍；调度值因首层输入通道补齐等原因更高。
GAP 另需至少约 2,048 个 8-lane 累加拍，输出后处理、BRAM 冲突、流水灌空和 DMA 另计。
所以 100 MHz 下只能写“计算调度约 1.014 ms/ROI，端到端待实现测量”，不得把
0.933 ms 理想下界写成实测延迟。

MAC 阵列起步固定为 8×16=128，基线按一 MAC/DSP 预算 128 DSP。x7z020 总量 220，
视觉链既有报告为 0 DSP；RISC-V、requant 和地址逻辑的实际 DSP/LUT 占用仍须集成综合后扣除。

## 8. 正式模型包与黄金包最低内容

J02 诊断包和 J06 正式模型/黄金包至少包含：

1. `manifest.json`：显式分配的 `model_id:uint32`、preprocess ID、类别、逐层 shape/layout/dtype、全部 scale、
   multiplier、shift、margin 阈值、offset/length 和工具版本；
2. 单一参数 payload：按 64 B 对齐打包全部 INT8 权重、INT32 bias、INT32 multiplier、
   UINT8 shift 及对齐填充；`WEIGHT_BYTES/WEIGHT_CRC32` 覆盖整个 payload，并同时记录 SHA256；
3. 至少覆盖零、正负、半舍入、INT8 饱和、INT32 边界附近、GAP 和 argmax 平票的单算子向量；
4. 固定诊断 ROI 的每层完整 INT8 黄金和最终结果；
5. 导出、复算、篡改拒绝的一键仓库脚本与原始退出码。

`model_id` 只是受版本管理的快速选择编号，不是完整模型身份；manifest/payload 的完整 SHA256
才是交付身份依据，CRC32 只用于板端 payload 装载检查。preprocess ID 与 MODEL_ID/SHA256
在 manifest 和 PS 服务中绑定，不新增 v0 MMIO 寄存器；`SOURCE_CONFIG_ID` 仍表示本轮 ROI/定位配置。

J02 可使用明确标注的非正式诊断参数验证结构和逐位语义，不得冒充真实精度或正式模型证据；
只有经过 J05 真实数据评估并在 J06 发布的包才称为正式模型包。

真实精度报告另需真实、有标注、按实物/会话隔离的数据；数值诊断输入不能冒充准确率数据集。

## 9. JL 已冻结的 C02 决策

| ID | 决策项 | 已选 v0 基线 / 未采用备选 | 影响 | 证据 / 风险 |
|:---|:---|:---|:---|:---|
| C02-P1 | 首网与 ROI | 推荐本文件 §2 的 FastenerCNN + `scene-gray-border-padding-v1`；备选须另起模型版本 | 决定全部 shape、MAC、训练与黄金 | FP32 原型结构/预处理已有离板证据；真实工位精度未验 |
| C02-P2 | 权重量化 | 推荐 per-channel 对称 `[-127,127]`；回退 per-tensor 对称 | per-channel 参数多，但通常减小通道间误差 | 现有 Brevitas 演练主要证明 per-tensor 链路；正式精度对比未做 |
| C02-P3 | 激活量化 | 推荐 per-tensor、zero-point=0、有效范围 `[-127,127]`；备选允许 `-128` | 决定输入/激活饱和器和边界向量 | 对称范围简化负数边界；可能少一个负值码 |
| C02-P4 | 累加与 bias | 推荐 INT32、bias 先加、不逐项饱和、导出器拒绝溢出模型 | 决定 MAC 位宽和软件等价性 | 当前网络理论乘加量可控；正式 bias/scale 未生成，仍须逐层范围证明 |
| C02-P5 | 舍入 | 推荐全链 nearest、ties-away-from-zero；备选 ties-to-even | 影响 bias、requant、GAP 的半值结果 | away-from-zero 易写成整数规则；负数 RTL 写法若偷加偏置容易出错 |
| C02-P6 | requant | 推荐 INT32 multiplier、INT64 有符号乘积、右移后饱和；备选需给同等逐位定义 | 决定 DSP/LUT、延迟与黄金格式 | 满足任务候选；INT64 乘法映射和时序尚未综合 |
| C02-P7 | score/低置信 | 推荐归一化 top1-top2 `score_q15`，明确非概率；备选由 PS 对反量化 logits 做校准概率 | 影响 LIVE score、阈值与固件 | 模型无 softmax 硬件；margin 阈值尚无真实开发集校准 |
| C02-P8 | 数据排布 | 推荐外部 ROI=4,096 B HW、中间激活 C8、权重 O16×I8；备选全 CHW | 决定导出器、DMA、BRAM 地址生成和利用率 | C8 对 8 输入 lane 直接；首层若外部 C8 会多搬 8 倍数据 |
| C02-P9 | 权重装载 | 推荐生产运行时 DMA，`$readmemh` 仅 tb；备选固定位流初始化 | 决定位流是否能复用模型 | DMA 增控制验证；固化权重会使模型升级必须重出位流 |
| C02-P10 | 缓存策略 | 推荐全权重常驻、单 ROI 双缓冲、激活 ping-pong；备选分层流入权重 | 推荐起始预算约 24 BRAM36 | x7z020 容量充足只是估算；端口冲突和实际 BRAM 推断未验证 |
| C02-P11 | MAC 与频率目标 | 推荐 8×16=128、目标 100 MHz；备选 8×8=64 降资源/时序风险 | 影响 DSP、单 ROI 延迟和 10 目标预算 | 视觉链报告 0 DSP、器件 220 DSP；128 MAC/100 MHz 从未综合验证 |

上表各行的“推荐”项均已成为 v0 实现基线；备选只作取舍记录，不得在未升约版本时实现。

## 10. 冻结后的实现门禁

- 先实现 J02 整数参考并产生边界黄金，再开始算子 RTL；
- 每个 RTL 算子必须有仓库内 tb、独立 `run_iverilog.sh` 模式和 `all` 回归；
- 比较必须逐元素，不能只比 argmax；
- 综合路径只用 Verilog-2001，禁止 `.*`、`logic`、`always_ff`；
- 128 MAC @100 MHz 只有在综合/实现 WNS、资源和对应源码证据入档后才算验证通过。
