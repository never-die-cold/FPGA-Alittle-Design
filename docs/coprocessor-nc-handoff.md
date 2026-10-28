# CNN 协处理器 NC 交接


> 2026-10-28 注：文中 `build/board-package-*`、`build/run/` 本地产物现位于 `others/build/`。
> 交付边界：**JL 交付 ≠ 板级验收**。JL 负责 RTL、Windows Vivado 产物与可追溯包；
> NC 负责下载和现场稳定性；WC 负责软件接入、独立软件看门狗及消费式 W1C 流程。

> **2026-10-27 当前优先状态**：CDC 控制同步与多目标结果提交 RTL 已合并，历史包
> `f856d5861db0`、`759744b99891`、`5653d5911b76` 全部作废。当前唯一有效首包是
> `cop-board-gate-2fc2bdd4a8f8`；它只含 A 变体，B 视频变体不得混入。

## 2026-10-26 现场更新：edge-fix bit 与板卡阻塞

> 本节更新于 2026-10-26 22:43，优先于下方旧状态表；旧表保留历史。

| 项 | 结论 | 证据 |
|:---|:---|:---|
| edge-fix 综合实现 | PASS | bit 9341F7FA...；WNS +3.062 ns、DSP 136、BRAM36 69、DRC 0、IMEM_FIRST_WORD=00008117 |
| edge-fix 包 | PASS | build/board-package-edge-fix（pattern,zero）、build/board-package-edge-fix-trained（roi_001,frame）；SHA 12/12 |
| 板上诊断网 | 旧 bit PASS | 旧 IMEM bit 59c2c918... 上 zero/pattern 6/6；不是 edge-fix bit |
| edge-fix 板上 | UNVERIFIED | edge-fix bit/trained 尚未上板；板卡 SD/mmc 故障待恢复 |
| 连续作业 | 未实现 | 固件单作业，每 case 需重新 Overlay |

冷启动顺序（2026-10-26 修正）：

1. 冷板无 PL 时不要先跑 cop_fclk.py（PYNQ Clocks 会报 No Devices Found）。
2. 先由用户/队友 JTAG 烧 edge-fix bit，让 PL/PYNQ device 出现。
3. 再跑 loader clock：

~~~bash
sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_payload_loader.py clock --package . --reads 20 --smoke-timeout 2
~~~

4. 然后 normal loader 跑 zero/pattern，再跑 roi_001/frame。

期望：zero 2/2/258 logits 2,-3,4；pattern 0/0/0 logits 1,-3,1；
roi_001 2/53/6837 logits -12,-30,41；frame 0/29/3741 logits 34,-41,5。
MODEL_ID：诊断 0x4A303250，训练 0x4A303251。

板卡当前阻塞：mmc0/SDHCI I/O 错误、串口命令超时、冷启动 No Devices；
现场操作见 data/logs/2026-10-26-board/USER-ACTIONS.md；
构建/包/测试证据见 data/logs/2026-10-26-build/README.md；
B 交接见 data/logs/2026-10-26-build/B-QUICKSTART.md 与 HANDOFF-A-to-B.md。

边界：BOARD 仍 UNVERIFIED；全链相机→板→EXE、正式 INT8/精度、M2/M3/M4 未完成。

## 当前真实状态

| 状态 | 结论 | 证据 / 缺口 |
|:---|:---|:---|
| 仿真跑通 | **PASS** | 行为级全回归；BRAM 模式 pattern/zero 各 73,795 元素逐项一致；延迟边界 PASS |
| 综合实现通过 | **PASS（A 变体）** | WNS +2.078 ns、DSP 136/220、BRAM36 69/140、latch/DRC=0；IMEM/CDC 门禁通过 |
| 板上跑通 | **UNVERIFIED** | 新 bit 尚待 NC 在 40 MHz 下验证 STATUS、FW_DECISION/ACCEPTED 与真实 DMA/result |

诊断网络不是正式训练模型，`score_q15` 是整数分数而非概率。PROVISIONAL payload 地址适配
与整机顶层已仿真。JL 门禁通过不等于板级验收；NC 须使用唯一有效 A 包完成下载、读回与
现场稳定验证，不得用旧 bitstream 或 B 视频实验产物冒充本次产物。

继续操作前先按 [`coprocessor-board-clock-runbook.md`](coprocessor-board-clock-runbook.md)
确认 FCLK1 实测 40 MHz；payload/GPIO/DMA 序列见
[`coprocessor-payload-loader.md`](coprocessor-payload-loader.md)。JTAG 只配置 PL，不应用 PS7 时钟。

## 生成与核验交付包

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh \
    build/run/<A_BUILD_NAME>/pynq_cop_40mhz.bit \
    build/run/<A_BUILD_NAME>/pynq_cop_40mhz.hwh \
    build/run/<A_BUILD_NAME>/pynq_cop_40mhz.xsa \
    build/reports/<A_BUILD_NAME>/gate_summary.txt
```

脚本会重跑 K3、生成 `dist/cop-board-gate-<commit>/` 与 `.tar.gz`，包含 `VERSION`、
`FILES.txt`、逐文件 `SHA256SUMS`、`EXPECTED_OUTPUTS.tsv`、golden、仿真日志和源码/脚本。
四个产物参数只能在整机 Tcl 门禁 PASS 后同时提供；本包应显示
`VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM`，而 `BOARD=UNVERIFIED_NEEDS_NC`。
NC 解包后先执行 `sha256sum -c SHA256SUMS`，不得手工修改 VERSION。

当前 A 包 `dist/cop-board-gate-2fc2bdd4a8f8.tar.gz` 的 SHA256 是
`e2eb5bd340f01c9cbfb2930a55d8ec36cbbdcdd6f0923636ed1e812b8b862127`；包内 bit/hwh/xsa
依次为 `f325a0dc4c2cb143e24ef13df6608e206af5c58f0354b3deec6f039d5875f71f`、
`480d04a3d9abee59e81892378c2457dfe92ea0cf6fc0822d4467b2121dbab358`、
`9e0a56276e89e2a94e3155eea7e267c97b97014ed74c8874524d03eaa462534c`。

以下仅为合并前历史产物 SHA256：bit 为 `1232769fdeabe59c962dae62a75bc1a5ebca07b1985898b6961fd574878f05db`，
hwh 为 `dce025d3db119824126d4af6915983971ca9eaf98ccdbf726f2d66a9c7c73070`，xsa 为
`255794ec8f07488dbe8b5feec3a6b1a3e8048f9a689777333fa0b639f0c23d28`。

| 包 | 台账状态 |
|:---|:---|
| `cop-board-gate-2fc2bdd4a8f8` | **唯一有效 A 首包**；BOARD/BOARD_CLOCK/LOADER 仍待 NC 验证 |
| `5653d5911b76` / `759744b99891` / `f856d5861db0` | **本轮明确作废**，不得上传或板验 |
| `d66916c49b80` / `21c4e751bbe8` | **历史已作废**，不得上传或板验 |
| `b821aa1d0c1f` / `c4839f39be2d` | **已作废**的 UNVERIFIED 中间包，不得交付 |

## 下载、启动与复位

1. 仅接收 JL 明确标记为 40 MHz 门禁通过、且 SHA256 与包一致的 `.bit`；板卡断开外部视频源，
   保存当前可用 bitstream 的路径，连接单块 PYNQ-Z2 与 JTAG。
2. Windows 执行：

   ```bat
   board\scripts\program_soc.bat dist\cop-board-gate-<commit>\payload\pynq_cop_40mhz.bit
   ```

3. 看到 `PROGRAM PASSED` 后按 BTN0 复位再释放；等待 MMCM 锁定与软件启动。下载成功本身不算验收。
4. WC 按 `coprocessor-wc-interface.md` 提交：先确认无 UNCONSUMED，写 CMD，等 sticky ACCEPTED
   或软件超时，再等唯一终态或软件超时；不得等待 READY。
5. DONE 时读 `RESULT_*` 和 `RESULT_SEQ`，校验序号并成功落盘后才写 CONSUME；ERROR 时先读
   `ERROR_CODE` 再 CONSUME。落盘失败禁止清灯。

## 应看到什么

- `EXPECTED_OUTPUTS.tsv` 的诊断锚点：pattern 为 class 0、margin 0、score_q15 0、logits
  `1,-3,1`；zero 为 class 2、margin 2、score_q15 258、logits `2,-3,4`。两者 low_conf=1。
- 每笔被受理命令出现 ACCEPTED；随后 DONE/ERROR/TIMEOUT 恰有一个；空闲时 READY=`!BUSY`。
- DONE 的 RESULT_SEQ 比提交前加 1；CONSUME 后 DONE/ERROR/TIMEOUT、RESULT_VALID、ACCEPTED、
  ERROR_CODE 同时清零，RESULT_SEQ 保持。

## 失败恢复与现场记录

软件 NO_ACK/HW_TIMEOUT 时停止新 START，保留状态快照；已有终态或结果落盘失败时不要 CONSUME。
先采集 STATUS、ERROR_CODE、RESULT_SEQ、版本、bitstream SHA256 与复现步骤，再按 BTN0 复位。
复位仍失败则重新下载已知可用 bitstream；无法恢复时保持 `ENABLE_COP=0` 的可用基线，禁止反复
覆盖现场证据。NC 将温度、电源、连续运行次数、首次失败时间和恢复结果写入新的板级日志。

## 已知限制与 OPEN

- OPEN-K2-1（**已关闭**）：`build/reports/pynq_cop_40mhz/utilization_impl.rpt` 记录
  Block RAM Tile 69/140，Windows 整机门禁已完成布局布线。
- OPEN-FW-1：Windows 已生成包含重建 `cop_job.hex` 的 bitstream；BRAM 初值在实板启动仍待 NC 验证。
- OPEN-ENV-1：`all` 已支持 riscv32/riscv64 前缀回落和无工具链 SKIP，仍需在干净环境复测依赖边界。
- OPEN-DOC-1（已修复）：`cop_job.hex` 曾陈旧且无引用；现由 Makefile `all` 重建，并由 `firmware_e2e` 加载。
- OPEN-BT-4：板顶候选的 16 ROI 槽已仿真，但任意 `TARGET_DESC_ADDR` 描述表尚未接入；
  当前只支持 `target_id == roi_index` 恒等映射。影响面是非恒等目标编号下的
  ROI/结果关联可能错配，因而阻断完整契约与发布验收，但不影响当前恒等映射诊断。
- manifest v1→影子物理 bank 与生产 PL 顶层已仿真；正式 RELEASE 参数和板验未完成。
- `compute` 与 `storage` OOC 历史结论保留；本次整机门禁已独立 PASS，不能反推板级通过。
- 本轮已有门禁通过的协处理器 bitstream，但尚无实板证据；板上状态保持 UNVERIFIED。
- OPEN-BOARD-CLK-1（顺序根因已复现）：改成 40 MHz 会使旧 cop 域失效；必须重配 PL、等待稳定并
  脉冲 FCLKRESETN1。`0x0` 表示域未就绪/无效，不能作为超频结论；板级功能仍未验收。
- OPEN-IMEM-1（综合证据已关闭/板上待验证）：Windows 已确认首字 `00008117`、INIT 非全零且
  readmem warning 为 0；NC 仍须验证新 bit 上 FW_DECISION/ACCEPTED 活性。
- OPEN-LOADER-1（离板已修/板上待验证）：BD 与 HWH 均确认 `C_SG_LENGTH_WIDTH=16`，loader 保持
  36,032 B 单次传输；新 bit/hwh 已过整机门禁，NC 尚未实测 payload 装载。
- OPEN-LOADER-2（离板已修/板上待验证）：`cop_job` 已驻留等 CFG/MODEL/ROI，firmware_e2e 延迟配置
  用例 PASS，干净门禁位流已包含重建固件；NC 尚未验证板上等待路径。PS 仍不得越权写 START。

## 本次例外与收尾理解题

本轮按 JL 指令覆盖 `AGENTS.md/workflow.md` 的逐步问答门槛：K1–K5 连续执行，不在中途等待；
仍保持小提交、逐步 TB、全回归和本地不 push。收尾一次性检查三题：

1. 为什么 READY 不能作为提交成功或等待条件，而 ACCEPTED 可以？
2. 为什么结果落盘失败时禁止写 CONSUME，RESULT_SEQ 又为什么不能被 CONSUME 清除？
3. 为什么 K3 BRAM 逐元素 PASS 与两个 OOC 报告仍不能宣称板上跑通？
