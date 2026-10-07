# 模块一收口报告：三级 RV32IM、转发与分支预测
日期：2026-10-07。状态：模块一技术收口复验完成，全量退出码0；理解门槛补测通过。正式入库与远程检查点状态见§7。
任务范围是核及最小 SoC；CNN、视觉定位、工业调度固件与 PS 接口属于后续模块。

## 1. 版本、条件和证据
- v0 固定 `partA-v0^{commit}=962a4f5`；验证时 HEAD `dcb3ef7`，核 RTL 与已验证 `96414be` 无差异。
- 本轮只改验证入口和文档；被测 RTL、tb、镜像哈希见 [manifest](../data/logs/2026-10-07-module1-closure/source-manifest.json)。本文件所在提交发布收口脚本和证据，该记录用于定位实际被测内容。
- Icarus 13.0、RISC-V GCC 14.2.0、Vivado 2026.1；器件 xc7z020clg400-1。套件 commit `6f7f47bdc61c0c51c0cbf75789678a1235eeefc2`。
- v1 四档同 RTL、同 hex、同 tb、同初始化，仅参数不同：nofwd=(0,0)、fwd=(1,0)、bht1=(1,1)、bht2=(1,2)，分别为 (ENABLE_FORWARDING,BHT_MODE)。
- 默认核是 fwd/BHT 关；本轮主交付与已上板档是 fwd+BHT2。IMEM 同步读、DMEM 异步读，各 32KB；三级保持 IF / ID+EX / MEM+WB。
- [本轮全量日志](../data/logs/2026-10-07-module1-closure/all-final.log)、[arch-test](../data/logs/2026-10-07-module1-closure/arch-complete.log)、[XSim](../data/logs/2026-10-07-module1-closure/xsim-pass/summary.txt)、[OOC 审计](../data/logs/2026-10-07-module1-closure/ooc-complete.log)、[上板与原始实现](../data/logs/2026-10-07-partC-postopt/README.md)。

## 2. CoreMark 四档与 v0 外部锚点
固定 2K、32 iterations，seeds=0/0/0x66，RV32IM/ILP32、-O2。窗口是复位释放至首次 **tohost_exit** 写；CPI=cycles/retired。
退休由 MEM+WB valid 计数，M 指令只计一次；气泡、多拍等待均保留。v0 使用旧 instrs 口径（比 v1 retired 多 1），仅作外部参考，不参与同 RTL 参数收益计算。

| 配置 | cycles | retired / instrs | CPI | CoreMark/MHz |
|:---|---:|---:|---:|---:|
| v0 两级外部锚点 | 21,275,738 | 10,106,387 instrs | 2.105177 | 1.506（历史短测） |
| v1_nofwd | 19,057,438 | 10,106,386 | 1.885683 | 1.681271 |
| v1_fwd | 17,114,141 | 10,106,386 | 1.693399 | 1.872039 |
| v1_fwd_bht1 | 16,335,562 | 10,106,386 | 1.616360 | 1.961260 |
| v1_fwd_bht2 | 16,232,079 | 10,106,386 | 1.606121 | 1.973761 |

CoreMark/MHz=32×1e6/(t1−t0)，与 CPI 的全局周期窗口不同；短仿真不足官方 10s，以上为仿真外推值，不是官方认证分数。
四档 tohost=34713、exit=0；CRC= e9f5/e714/1fd7/8e3a/8799；官方短测 errors_raw=1 保留而不作为 CRC 错误。
优化后 XSim 与 Icarus cycles/retired/bubbles/BHT 全部一致。v0 来源：[原始 CoreMark 日志](../data/logs/2026-09-23-coremark/run_v0_32iter.log)。

| 收益及分母 | 结果 | 判定 |
|:---|---:|:---|
| 固定 Radix-4，只开转发：nofwd→fwd | 10.20% | ≥8.0% 性能回归门禁通过 |
| 固定转发，只开 BHT2：fwd→bht2 | 5.15% | BHT 净收益 |
| 当前 Radix-4 工作点 nofwd→fwd+BHT2 | 14.83% | 25% 组合尽力目标未达；不阻塞最低验收 |
| 原 Radix-2 nofwd 23,869,806→当前 bht2 | 32.00% | 含快速乘法、转发和 BHT；不可归因给单一功能 |

历史仅转发 8.14%、原 25% 门禁 FAIL、Radix-4 乘法净贡献 21.95% 均保留，见 [历史口径](../data/logs/2026-10-05-partB-radix4-cycle-breakdown/README.md)。不同分母的百分比不能相加。

## 3. 自写 benchmark 与命中率
[bench_v0_1.c](../src/riscv_fw/bench_v0_1.c)、[Makefile](../src/riscv_fw/Makefile)、[反汇编](../src/riscv_fw/bench_v0_1.dis) 已在库：固定种子、整数循环、volatile 数组、位运算和乘法；启动代码 call main。
同镜像、同 tb，四档均 checksum=0x1385cbd1/327535569、exit=0、retired=1205；四档已接入 all。

| 配置 | benchmark cycles | CPI | lookup / hit / miss | 命中率 |
|:---|---:|---:|:---|---:|
| nofwd | 2850 | 2.365145 | 0 / 0 / 0 | 不适用 |
| fwd | 2423 | 2.010788 | 0 / 0 / 0 | 不适用 |
| bht1 | 2380 | 1.975104 | 161 / 93 / 68 | 57.76% |
| bht2 | 2351 | 1.951037 | 161 / 122 / 39 | 75.78% |

CoreMark：BHT1=1,587,055/1,854,101=85.60%；BHT2=1,690,538/1,854,101=91.18%；hit+miss=lookup。
关闭档事件全为 0，不能用它计算“0% 命中率”。自写 benchmark 无预测 control=129；BHT1/2 control−miss=18，均为非 BHT 跳转气泡。
由相同指令流推导条件分支 taken=129−18=111，因此静态不跳的方向命中率为 (161−111)/161=31.06%，显著低于 BHT2 的 75.78%。该值是基于分类计数的推导，非关闭档事件实测。
预测统计只在真实 ex_accept 条件分支计一次；错误路径 store/RF/muldiv 的禁止副作用由 bht_flow 三档与 PC/IF 专项断言证明。

## 4. arch-test 扩展子集与功能边界
入口：`bash sim/scripts/run_arch_test_matrix.sh`；清单为 I:add/addi/and，M:mul/mulh/mulhsu/mulhu/div/divu/rem/remu，各四档，**44/44 签名匹配官方 golden 且档间 SHA256 相同**。
[RISC-V 签名和逐项日志](../data/logs/2026-10-07-module1-closure/arch-complete/) 留在仓库；38 用例 RV32I 固件、访存、RAW/load-use、M 握手和冲刷另由全量专项覆盖。
尝试扩大为 38 I + 8 M 时，官方 beq-01 超出 32KB，链接器报 overflowed by 195388 bytes；[原失败](../data/logs/2026-10-07-module1-closure/arch-final.log) 不删除。不能放大仿真 RAM 来冒充真实核验证。
这是已声明扩展子集的全部验证，**不构成上游全部测试或 RISC-V 合规认证**。非对齐异常、CSR、特权/中断未实现；fence/ecall/ebreak 按 NOP。

## 5. 核 OOC、资源与时序
四档 @10ns 同工具同器件 post-route 记录（含失败）：

| 配置 | WNS @10ns | hold | LUT | FF | BRAM / DSP | @100MHz |
|:---|---:|---:|---:|---:|:---|:---|
| nofwd | +0.051 | +0.081 | 2014 | 509 | 0 / 0 | 通过 |
| fwd | −0.587 | +0.103 | 2150 | 509 | 0 / 0 | 失败 |
| bht1 | −0.419 | +0.088 | 2357 | 573 | 0 / 0 | 失败 |
| bht2 | −0.586 | +0.169 | 2508 | 637 | 0 / 0 | 失败 |

BHT2 **独立以 11.520ns 约束综合布线**：86.806MHz 实点通过，WNS=+0.538、hold=+0.167、LUT=2443/FF=637/BRAM=0/DSP=0；优化前同点 −0.334 的失败保留。
默认 fwd 与 BHT1 从各自 10ns **固定布线检查点**重新约束至 11.520ns，STA WNS=+0.933/+1.101、hold=+0.103/+0.088；没有重新综合布线，方法与 BHT2 独立实现点分别标明。
OOC 审计补齐 min/max、DRC、check_timing、clocks 与工具版本；严重 DRC=0，无无时钟寄存器、未约束内部端点或组合环路。OOC 外部 I/O 无延迟约束，不能替代 SoC 全路径验收。
v0 tag 同脚本 @10ns WNS=−1.935、LUT=1606/FF=401，83.8MHz 是 Slack 外推；[10/03 复现](../data/logs/2026-10-03-picorv32-compare/README.md) 同值。86.8MHz 是本轮明确冻结的约束门禁，不是 v0 已实测通过的频率。
目前主档最高已通过约束点是 86.806MHz；91.1MHz 等外推值不算实点通过，也不宣称已找出绝对 Fmax。100/125MHz 为后续非阻塞提频目标。
同 10ns 资源点的 CoreMark/MHz/LUT：nofwd 0.000834792；fwd 0.000870716；bht1 0.000832100；bht2 0.000786986。这是每 MHz 的面积归一值，不是实板 CoreMark/LUT。
PicoRV32 regular/large OOC 已于 10/03 入档，数值仍需标注 Slack 外推；未重跑其基准，不拿不同基准 CPI 作同负载加速比。

## 6. 最小 SoC 真实上板与后续接口
本轮复用 10/07 优化后真实板前记录，**未再次下载或代替人工观察**：
- 被测 c2bb910 + 声明补丁（随后入库 96414be），Vivado 2026.1、PYNQ-Z2、核 40MHz、BHT2，hello_v0。
- SoC WNS=+3.618、WHS=+0.035、严重 DRC=0、未约束内部端点=0；LUT=6768、FF=859、BRAM=8、DSP=0。
- 位流 SHA256=B06F08289D8F461DE051A89095E4E22ACB290455632D162CA14BA869F407EC93。
- never-die-cold 板前观察：下载后 LED=1101 静止；BTN0 按下0000，松开0001。软复位不清 DMEM，第二次运行读取旧 tohost，属于契约。
- 核 OOC 86.806MHz 与 SoC/上板40MHz 分开；SoC 125MHz 的历史 WNS=−8.044 FAIL 保留。

**未实现 / 未接入**：PS↔核 AXI/中断、CNN 自定义指令或 MMIO、统一地址表、工业检查固件；均是后续应用工作包，不作为模块一已完成能力。未实现 CSR/特权/异常模型，未做官方长时间 CoreMark 或上游完整 ISA 认证。

## 7. 交付与复现
[一键复现清单与 #skill候选](../docs/module1-reproduction.md) 包含全量、arch、XSim、OOC 和汇总入口；[data/metrics.csv](../data/metrics.csv) 保留旧指标并追加本轮结果。
本轮用户已授权一次写完、理解题集中末尾；[完整理解问答](llm_log/2026-10-07-module1-closure.md) 已归档，补测通过。#20/#21 于提交前读取仍 open，旧 25%/100MHz 硬条款与仓库已确认修订不同；[远程收尾记录](../docs/module1-issue-closeout.md) 在证据发布后更新，不能提前宣称远程检查点已关闭。

本轮最终汇总：
`PASS: 44 arch signatures; eight workload runs; four XSim matches; five OOC audits; two fixed-route gates`。
`iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v` 退出0；源码稳定性哈希核对通过。原始退出码、汇总JSON及最终diff检查留在本轮证据目录。
