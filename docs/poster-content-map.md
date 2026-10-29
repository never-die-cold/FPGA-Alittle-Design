# 成果海报文案溯源表

> 成品：`/mnt/c/Users/jianglibo/Desktop/嵌入式海报-FINAL.pptx`。事实基线为
> `origin/dev/riscv@0430257`；海报只陈述仿真与整机综合实现成果，不外推板级结果。

| 海报区域 | 最终文案 / 数据 | 仓库来源 |
|:---|:---|:---|
| 主标题 | 完成全整数 CNN 协处理器；128 MAC/周期；40 MHz 整机实现 | `src/coprocessor/design_v0.md:181-190,237-238`；`docs/coprocessor-build-variants.md:18-24` |
| 平台说明 | PYNQ-Z2 / Zynq-7020；自研 RISC-V 核；CNN 协处理器 | `docs/coprocessor-nc-handoff.md:97-105`；`docs/contracts/coprocessor-integration-v0.md:34-51` |
| 成果概览 | RISC-V 固件负责调度、并行目标和结果汇总；协处理器执行 Conv→GAP→FC；PS 负责配置、装载和保存结果 | `docs/contracts/coprocessor-integration-v0.md:34-51` |
| 三类结果 | 螺栓 / 螺母 / 垫圈 | `docs/contracts/coprocessor-integration-v0.md:119-120,240-244` |
| 架构框图 | PS → DMA → BRAM → CNN 协处理器；RISC-V 核经 AXI-Lite 调度，输出类别与整数分数 | `docs/contracts/coprocessor-integration-v0.md:34-51,200-212` |
| 四步流程 | 装载输入；固件调度；整数推理；汇总结果 | `docs/contracts/coprocessor-integration-v0.md:34-51,204-210` |
| 阵列指标 | 8×16 并行阵列，128 MAC/周期 | `src/coprocessor/design_v0.md:181-190,237-238` |
| 一致性指标 | 两组输入各 73,795 个元素在真实 BRAM 时序下逐项一致 | `docs/coprocessor-nc-handoff.md:47-50` |
| 整机指标 | 40 MHz；时序余量 +2.078 ns；DSP 136/220；BRAM36 69/140；锁存器 0；DRC 0 | `docs/coprocessor-build-variants.md:18-24` |
| 全整数计算链 | 权重逐通道对称 INT8；激活逐张量对称 INT8、零点为 0；INT32 累加；整数乘、舍入、右移和饱和完成重量化 | `src/coprocessor/design_v0.md:47-60,123-131` |
| 交付清单 | FPGA 位流文件、硬件描述文件、硬件平台文件、全整数参考模型、可复现构建脚本、校验清单与黄金数据 | `docs/coprocessor-nc-handoff.md:61-82` |
| 验证闭环 | 整数参考模型 → 逐层黄金结果 → RTL 逐元素对拍 → 整机构建与校验 | `docs/contracts/coprocessor-integration-v0.md:307-316` |
| 固件镜像 | 构建前后校验固件镜像存在、非空且首字匹配 | `docs/coprocessor-imem-init-gate.md:40-51,76-78` |
| 成果口径 | 已完成仿真验证与 40 MHz 整机综合实现；海报不包含板级实测、正式训练模型发布或视频整机验证结论 | `docs/coprocessor-nc-handoff.md:45-55` |

## 图片与版式处理

- 模板中的 63 张蛋白质相关图片已全部删除，没有使用网络图片或生成图片。
- 系统架构、指标卡和交付清单均由模板同色系形状与文字组成。
- 页面数量、90×120 cm 比例、页眉分区和绿色主题保持不变。
