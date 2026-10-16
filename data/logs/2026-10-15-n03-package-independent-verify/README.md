# N03 实验包：离板 SHA256 / 配对独立复核（2026-10-15）

基线 `dev/model@891cba2`。本目录由第二个会话（ZCode）对
[2026-10-14 返板执行单](../../../docs/n03-custom-return-runbook-2026-10-14.md) 的**离板部分**做独立复算：
逐文件重算哈希、交叉核对 XSA 内嵌件与 HWH 地址/VDMA 参数。
不修改任何受版本控制文件，不执行板端动作，不改变 `dev/model` 工作区。

归口证据仍为 `../2026-10-14-n03-return-review/`（其记录未被本目录替换）。

## 复核结果（原始输出见本目录）

| 复核项 | 方法与来源 | 结果 |
|---|---|---|
| 三份执行脚本：仓库源 ↔ 留存副本 ↔ `runner-inputs.json` | 重算 SHA256（`sha256-recheck.txt`） | 6/6 OK，字节数一致（9515/5446/6667） |
| `review-input-sha256.json` 12 条（测试、审计工具、`m2_onboard.py`、`vision_regs.py`、两个 ps1；含原 vision 依赖） | 重算 SHA256 | 12/12 OK |
| 候选产物 `capture-1791713720540454.{bit,hwh,xsa}` | 重算 SHA256 | 3/3 OK（4045769 / 557643 / 609696 字节） |
| "XSA 内嵌 bit/hwh 与独立文件一致" | 解包 XSA 取 `capture-*.bit`、`vision.hwh` 后比对 | 一致：`86d2adb0…`、`eaaf68c3…`，与独立文件逐字节相同 |
| 地址映射 `pipe/capture_status/capture_dma` | 解析 HWH `<MEMRANGE>`（`hwh-xsa-crosscheck.txt`） | 0x40000000 / 0x42000000 / 0x43000000，与 `candidate-artifacts.json` 一致 |
| VDMA 参数（MM2S/S2MM/FSTORES/TDATA/DATAWIDTH/FSYNC） | 解析 HWH `<PARAMETER>` | 0/1/4/24/64/2，与记录逐项一致 |

合计 **21 条哈希记录 + 1 组内嵌件比对 + 7 项 IP 配置** 全部匹配，`MISMATCH` 计数为 0。

## 附：98 项构建输入审计重跑

用仓库自带工具对 `data/evidence/2026-10-12-c01-exact-build-inputs/manifest.json` 重跑一次
（`build-inputs-recheck.txt` / `.json`，真实退出码 0）：

```text
PASS: retained C01 input integrity; 98 files; current changed= 2 missing= 0 exact CRLF recovered= 0
```

与 `../2026-10-14-n03-return-review/build-inputs.json` 逐项比对：
`manifest_sha256`（`49853238…`）、`retained_inputs_verified=98`、`current_matches=96`、
`current_changed=2`、`current_missing=0`、`exact_crlf_recovered=0`，以及 96/2/0 三个清单内容 **全部相同**；
两项漂移仍是 `sim/scripts/build_capture_hdmi.tcl` 与 `sim/scripts/run_c01_capture.ps1`（包装脚本），
与执行单 §1 的描述一致，10-14 之后无新增漂移。

该工具自身给出的边界：`input integrity/drift only; not bit-to-source or board acceptance`。

## 附：驱动 ↔ 位流 地址/寄存器兼容（可离板核对的部分）

原始对照见 `driver-address-crosscheck.txt`。执行单 §1 把"候选驱动与位流/地址/复位兼容评审"列为返板进入条件，
其中地址一层可以离板核对：

| 项 | 脚本侧 | 候选位流/契约侧 | 结论 |
|---|---|---|---|
| pipe 基址 | `c01_status_onboard.py` 探测 0x40000000 | HWH `pipe` 0x40000000–0x4000FFFF；契约同 | 一致 |
| 状态基址 | 0x42000000（status/ddr 两脚本） | HWH `capture_status` 0x42000000–0x4200FFFF | 一致 |
| DMA 基址 | 0x43000000 | HWH `capture_dma` 0x43000000–0x4300FFFF | 一致 |
| IP 类型/参数 | VDMA S2MM 用法（CR/SR/PARK/VSIZE/HSIZE/FRMDLY_STRIDE/START_ADDRESS = 0x30/0x34/0x28/0xA0/0xA4/0xA8/0xAC） | HWH `axi_vdma:6.3`，仅 S2MM、TDATA 24、FSTORES 4、FSYNC 2 | 一致 |
| 状态 ID/几何 | 三脚本均校验 (0x0,0x14,0x18)==(0x43415031,1280,720) | 契约 0x00=CAP1、0x14/0x18=1280/720 | 一致 |
| 状态计数偏移 | 0x04/0x08/0x0c/0x10/0x1c/0x20 | [状态契约](../../../docs/c01-capture-status-contract.md) 同表 | 一致 |

边界：只核到"基址、ID/几何、寄存器偏移、IP 类型与参数"这一层；
位流侧复位语义、跨域行为与实机可达性仍需 WC/JL 评审与板端验证，本目录不代签该评审。

## 附：板端入口静态检查（不接板）

| 检查 | 命令 | 结果 |
|---|---|---|
| 串口下发载荷是否超限 | `run_n03_board_capture.ps1 -LogPath … -CheckOnly` | **PASS: serial wire bytes=2688 limit=3000; no serial opened**，真实退出码 0，未开串口 |
| 载荷与入口哈希 | `sha256sum` | `n03_board_capture.py`=`46bb3c0d…`；`run_n03_board_capture.ps1`=`5742f812…`（`board-entry.sha256`） |

调用注意（来自脚本静态阅读，供返板执行时避坑）：

- 板端捕获脚本是"压缩后经串口下发"的路径，靠 3000 字节线长上限；每次改动 `n03_board_capture.py`
  都应先跑一次 `-CheckOnly`，否则会在真机上才发现超限。
- `run_c01_capture.ps1` 是**重建**包装：`-Stage bitstream` 会新建 `c01-hdmi-<新tag>` 目录并产出新的
  bit/hwh（`EVIDENCE_DIR=` 为准）。N03 实验必须用已冻结候选
  `capture-1791713720540454.{bit,hwh}`（见 `candidate-artifacts.json`），**不要**用该包装重建的产物替代；
  这正是执行单"不据此代签 bit-to-source"所指的重建/冻结边界。
- `run_c01_status.ps1` 要求远端目录匹配 `^/home/xilinx/vision_m2/c01-[0-9a-f]{32}$`，
  即返板时必须上传到新的独立目录，不能复用旧失败目录。

## 边界（未做、也不能由本目录代替）

- 未上传板端、未在新目录重新核对 SHA、未执行 `c01_ddr_onboard.py`：属返板后 NC 现场动作。
- 未做候选驱动与位流/地址/复位的兼容评审（WC/JL 责任，执行单 §1 的进入条件）。
- 未重跑 98 项构建输入审计与既有专项；其结论仍以 `../2026-10-14-n03-return-review/` 为准。
- 哈希一致只证明"取到了预期的字节"，不构成 bit-to-source 等价或板上可运行性的结论。

## 结论

按执行单第 2 步第 2 项，**本地侧"三份执行源码 + 候选 bit/hwh 配对"的 SHA256 核对已完成且全部通过**；
板端上传后的二次核对与 N01 基线（boot_id、PL 路径、原 vision smoke）仍待 NC 返板执行。

## 追加复核（2026-10-15 22:4x）：入口被并行会话修改后的哈希口径

并行快速改进会话修改了 `sim/scripts/c01_ddr_onboard.py`（+11 行，新增 `C01_CAPTURE_MODE` 开关），
重跑同一套核对（`sha256-recheck-after-entry-drift.txt`）结果：**24 项中 1 项失配**。

| 对象 | 结论 |
|---|---|
| `sim/scripts/c01_ddr_onboard.py`（仓库工作区） | **MISMATCH**：`54dd5d64…` ≠ 记录 `e822a708…` |
| `…-inputs/inputs/c01_ddr_onboard.py`（10-14 归档快照） | **OK**：仍是 `e822a708…`，已评审字节完整保留 |
| 其余 22 项（另两件套、留存副本、候选 bit/hwh/xsa） | 全部 OK |

对返板的含义：若要按 10-14 已评审字节执行 N03，必须取归档快照中的入口（`inputs/c01_ddr_onboard.py`），
不能直接用当前工作区版本；若要改用当前版本，则需重新记录哈希并重做驱动/位流兼容评审。
本目录此前"三件套逐字节未变"的结论**仅在其记录时点成立**，现已被该漂移取代。

## 追加复核（2026-10-15 23:0x）：构建输入出现新增漂移

并行快速改进会话修改了 `src/vision/cop_buf.v`（把 `raddr % DW` 取模改为列计数器 `rd_col`，+6/−4），
该文件属于候选位流的 98 项构建输入之一。重跑审计（`build-inputs-recheck-after-sweep.txt`）：

| 指标 | 10-14 记录 | 现在 |
|---|---|---|
| `current_changed` | 2（两个包装脚本） | **3**：新增 `src/vision/cop_buf.v` |
| `current_matches` | 96 | 95 |
| missing / CRLF 恢复 | 0 / 0 | 0 / 0 |

含义：**当前工作区已不再是候选位流的已评审输入集**。若按当前工作区重建，产出的 bit/hwh 与
`capture-1791713720540454.*` 不是同一份；返板包要么继续用 10-14 冻结快照（含 `build_capture_hdmi.tcl`
等 2 项包装漂移已记录在案），要么在改后重建位流并重做位流/地址/复位兼容评审与哈希记录。
