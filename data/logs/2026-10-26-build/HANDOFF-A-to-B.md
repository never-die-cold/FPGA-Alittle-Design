# A→B 上板交接（2026-10-26 22:30）

## 优先包

- 诊断：E:/Projects/FPGA-Alittle-Design/build/board-package-edge-fix
  - VERSION=cop-board-edge-fix-8884046；用例 pattern,zero
- 训练：E:/Projects/FPGA-Alittle-Design/build/board-package-edge-fix-trained
  - VERSION=cop-board-edge-fix-trained-8884046；用例 roi_001,frame

bit/hwh/xsa：
- bit 9341F7FA008C4A853767B2850701758E0534C923AED955B4B3B3F7E750BC4160
- hwh DB5B53B9D1B85E8F28DD83880C0015E3D55AE492BE114809C853955891432506
- xsa E4FE5D35973699F62EE483188E7DFE4264D04E271602910728B29130D7A4AB77

门禁：WNS +3.062 ns、DSP 136、BRAM36 69、DRC 0、CDC allowlist 命中；
IMEM_FIRST_WORD=00008117、READMEM_WARNINGS=0。

## 与旧包的区别

- 本 bit 含 dma_start_ps_q 上升沿检测；正常 loader 应不再因 start 高电平重复触发。
- 旧 566b 包（build/board-package-j02、build/board-package-trained）保留 fallback，但最终
  证据优先用 edge-fix bit 9341...。
- 固件仍是单作业，每个 case 需重新 Overlay；连续作业未实现。
- 包内已含 cop_fclk.py、cop_payload_loader.py、cop_board_fast_run.py；SHA256SUMS 12/12。

## B 的执行顺序

1. 校验包内 SHA256SUMS；上传 edge 诊断包到板上新目录，不覆盖旧包。
2. set FCLK1=40 -> 用户/队友 JTAG 烧 9341... -> loader clock --reads 20 --smoke-timeout 2。
3. 正常 loader 跑 zero/pattern；若仍异常再用 fast-run。
4. 训练包跑 roi_001/frame；期望 logits -12,-30,41 与 34,-41,5；MODEL_ID=0x4A303251。
5. 结果写 data/logs/2026-10-26-board/；把包/bit SHA 与 JSON 回给 A。

## 期望结果

- zero: class 2, margin 2, score 258, logits 2,-3,4, low_conf 1
- pattern: class 0, margin 0, score 0, logits 1,-3,1, low_conf 1
- roi_001: class 2, margin 53, score 6837, logits -12,-30,41, low_conf 0
- frame: class 0, margin 29, score 3741, logits 34,-41,5, low_conf 0
- 全部要求 matches_expected=true
