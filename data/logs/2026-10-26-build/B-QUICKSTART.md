# Agent B 快速执行卡（2026-10-26 22:30）

## 优先包：edge-fix（含 DMA start 边沿修复）

- 诊断：build/board-package-edge-fix（pattern, zero）
- 训练：build/board-package-edge-fix-trained（roi_001, frame）
- bit 9341F7FA008C4A853767B2850701758E0534C923AED955B4B3B3F7E750BC4160
- hwh DB5B53B9D1B85E8F28DD83880C0015E3D55AE492BE114809C853955891432506
- xsa E4FE5D35973699F62EE483188E7DFE4264D04E271602910728B29130D7A4AB77
- 包内 SHA256SUMS 12/12；tools 含 cop_payload_loader.py、cop_fclk.py、cop_board_fast_run.py。

## B4 时钟（JTAG 前）

    sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_fclk.py set --clk 1 --mhz 40

期望 after_mhz=40.0、in_spec=true。JTAG 烧写由用户/队友执行；B 不启动 Vivado。

## B4 烧写后活性

    sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_payload_loader.py clock --package . --reads 20 --smoke-timeout 2

期望 measured_fclk1_mhz=40.000000，20 次首读全 0x00000001，固件活性 PASS。

## B5 诊断：优先正常 loader

    sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_payload_loader.py run --package . --case zero --measurement zero.json --timeout 10
    sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_payload_loader.py run --package . --case pattern --measurement pattern.json --timeout 10

期望 matches_expected=true；zero 2/2/258 logits 2,-3,4；pattern 0/0/0 logits 1,-3,1。
本 bit 已含边沿修复，正常 loader 应不再重复触发；若仍异常，再用包内 cop_board_fast_run.py。

## B6 训练

    sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_payload_loader.py run --package . --case roi_001 --measurement roi_001.json --timeout 10

期望 class 2 / margin 53 / score 6837 / logits -12,-30,41；MODEL_ID=0x4A303251；
29e2f4 是原始字高→低显示，不是 loader 列表顺序。frame 用例：0/29/3741 logits 34,-41,5。

## 单作业限制

固件仍是单作业；每个 case 需重新 Overlay，不要连续不重载跑第二笔。SLCR FPGA_RST_CTRL 复位
曾把板卡挂死，不要重复。

## 失败快照

- DMA 卡：STATUS/DMA_BYTES/DMASR/DMACR/GPIO2；核对板上 bit SHA。
- NO_ACK：记录 PL 配置到 CFG/DMA 的时间；查固件 guard。
- 结果不符：先核对包 SHA、EXPECTED 行、MODEL_ID；不要放宽黄金。
- 旧 566b 包保留 fallback，但最终证据优先用 edge-fix bit 9341...。
