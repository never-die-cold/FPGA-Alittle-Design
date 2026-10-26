# 2026-10-26 构建线（Agent A）证据

- 日期/执行者：2026-10-26，构建线 Agent A（与上板 Agent B 并行）。
- 分支/基线：dev/riscv；HEAD 为本地 A 线提交（见 git log）。
- 边界：本目录只记录构建/打包/测试证据，不替代 B 的板级实测，不写 BOARD PASS。

## 1. 当前主产物：含 DMA start 边沿修复的 edge-fix bit

第二轮整机构建在 22:28 PASS（Vivado 2026.1）：

    VIVADO=2026.1
    WNS_NS=3.062
    DSP=136
    BRAM36=69.0
    LATCHES=0
    IMEM_FIRST_WORD=00008117
    IMEM_INIT_NONZERO=1
    READMEM_WARNINGS=0
    CDC_RULE_COUNTS=CDC-15=73,CDC-3=12,CDC-6=7
    CDC_ALLOWLIST_ENTRIES=5
    DRC_BLOCKING=0

产物（build/run/pynq_cop_40mhz/）：

| 文件 | 字节 | SHA256 |
|---|---:|---|
| pynq_cop_40mhz.bit | 4045773 | 9341F7FA008C4A853767B2850701758E0534C923AED955B4B3B3F7E750BC4160 |
| pynq_cop_40mhz.hwh | 324441 | DB5B53B9D1B85E8F28DD83880C0015E3D55AE492BE114809C853955891432506 |
| pynq_cop_40mhz.xsa | 1390329 | E4FE5D35973699F62EE483188E7DFE4264D04E271602910728B29130D7A4AB77 |

本 bit 的 RTL 已包含 dma_start_ps_q 上升沿检测（见 §3）。

## 2. 前一代 IMEM 门禁 bit（566b，fallback）

- 21:50 构建 PASS：WNS 2.771、DSP 136、BRAM36 69、IMEM_FIRST_WORD=00008117、READMEM_WARNINGS=0。
- bit 566B512ABD63140FC9137E3C49C3D2A74B46520CF323139E914672AA35379032
- hwh D069DB4FA760CCB0E49A0CCC566311829FCD9421E0CDDDBEA8C626E4EE65C6BB
- xsa 382EF5ED1D5A0FEF27E62F7C8A65EF8C33D672C2E2E422F426C25D245483EBE6
- 该 bit 不含 DMA 边沿修复，B 曾用 fast-run 绕过；保留作 fallback。

## 3. DMA start 边沿修复 RTL/TB

- src/riscv/pynq_cop_top.v：PS 域 dma_start_ps_q 上升沿检测，一次高电平只发一次请求。
- sim/coprocessor/tb_pynq_cop_top.v：保持 start 高电平 400 个 ps_clk 断言只有 1 次 cop_dma_start；
  拉低后再脉冲断言第 2 次；隔离 Icarus 13 实测 PASS。
- 该修复已进入 §1 的 edge-fix bit；566b 不含。

## 4. 构建环境修复

第一次 edge 构建在 IMEM precheck 失败：Vivado 子进程继承 PYTHONHOME（Vivado tps 的 python-3.13），
系统 Python 3.12 加载 3.13 re 模块触发 SRE module mismatch。

- 原始失败日志：edge-build-fail-1.log。
- 修复：build/build_pynq_cop_gate.tcl 的 find_gate_python 在 exec 前
  unset -nocomplain ::env(PYTHONHOME) / ::env(PYTHONPATH)。
- 修复后 22:28 构建 PASS。

## 5. 上板包与 SHA 复核

| 包 | 目录 | 用例 | 内容文件数 | SHA 复核 |
|---|---|---|---:|---|
| edge 诊断 | build/board-package-edge-fix | pattern,zero | 12 | 12/12 OK |
| edge 训练 | build/board-package-edge-fix-trained | roi_001,frame | 12 | 12/12 OK |
| 566b 诊断 | build/board-package-j02 | pattern,zero | 12 | 12/12 OK |
| 566b 训练 | build/board-package-trained | roi_001,frame | 12 | 12/12 OK |
| A 诊断 | build/board-packages/diagnostic | pattern,zero | 11 | 11/11 OK |
| A 训练 | build/board-packages/trained | roi_001 | 10 | 10/10 OK |

- edge 两包均含 payload/tools/cop_payload_loader.py、cop_fclk.py、cop_board_fast_run.py。
- EXPECTED：pattern 0/0/0 logits 1,-3,1；zero 2/2/258 logits 2,-3,4；
  roi_001 2/53/6837 logits -12,-30,41；frame 0/29/3741 logits 34,-41,5。
- 复核脚本：verify_packages.py。

## 6. A5 软件测试

- test_cop_payload_loader.py：PASS（DMA16、clock->PL reload->FCLKRESET1、未重配/静默固件 fail-closed）。
- test_cop_driver.py：修正并行改动遗留的 main() 旧函数名后 PASS
  （PynqDmaPlane 地址/长度/越权负例、PynqMmio 基址规则、NO_ACK/HW_TIMEOUT/stale/CRC）。

## 7. 板卡 B 线状态

- B 在旧 IMEM 修复 bit 59c2c918... 上 fast-run 取得 zero/pattern 6/6 matches_expected=true；
  证据 data/logs/2026-10-26-board/zero-fast.json、pattern-fast.json、repeat/*。
- 随后 B 尝试 SLCR FPGA_RST_CTRL 复位 cop 域导致板卡挂死；已断电重启，22:00 串口恢复
  （serial-probe-3.txt，192.168.50.99/COM12 在位）。
- edge-fix bit 9341... 尚未上板；trained 尚未上板；B 需在恢复后上传 edge 包并复跑。

## 8. 未完成 / 边界

- edge-fix bit 的板上 zero/pattern/trained 未实测；BOARD 仍 UNVERIFIED。
- 固件仍是单作业，每个 case 需重新 Overlay；连续作业未实现。
- 全链相机→板→EXE、正式 INT8 模型/精度、M2/M3/M4 验收未完成。
- 566b/edge 包均在 build/（git ignore）；包内 SHA 已复核，但包本身不入库。

## 9. 复现入口

- 构建：build/build_pynq_cop_gate.tcl（find_gate_python 已 unset PYTHONHOME/PYTHONPATH）。
- TB：Icarus 13，tb_pynq_cop_top + src/riscv/*.v + src/coprocessor/*.v。
- 打包：sim/scripts/build_board_package.py（含 cop_fclk 复制）。
- 上板：见 B-QUICKSTART.md 与 HANDOFF-A-to-B.md。
