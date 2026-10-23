# 2026-10-23 协处理器 board bring-up：BLOCKED（交接包/板卡缺失）

> **2026-10-23 更新**：JL 已在 `23e8aef`/`21c4e75` 修复跨平台门禁并重打
> `cop-board-gate-21c4e751bbe8`；源码已合并到 `dev/exe`。本机仍**没有 tar 包与板卡**，
> 因此本记录仍是 BLOCKED；复验见
> [2026-10-23-cross-platform-fix-verify](../2026-10-23-cross-platform-fix-verify/README.md)。

> 状态：**NOT RUN**。本记录只证明“尝试过、缺什么”，不包含任何板级结果；
> 不伪造 STATUS/ERROR_CODE/RESULT_SEQ/class/margin/score/logits/温度/运行次数。

## 1. JL 交接信息（按用户转述）

- 包：`dist/cop-board-gate-21c4e751bbe8.tar.gz`，1,254,148 B；同名 `.sha256` 侧车。
- 位流 SHA256：`7e1e34304ef71efdfe86ec3e6dbeead6ab419c741806a3334a71474746aa0b6c`。
- 解包后 `sha256sum -c SHA256SUMS` 应 106/106 OK。
- 对照：`EXPECTED_OUTPUTS.tsv`（pattern class0/margin0/score0；zero class2/margin2/score258）。
- 边界：`BOARD=UNVERIFIED`；PROVISIONAL 诊断模型，不是发布模型。
- 本仓库可见的 `origin/dev/riscv` 最新为 `7c6cc40`；包名中的 `21c4e751bbe8`
  不在本地/已拉取的远端 refs 中，包的源提交未能核对。

## 2. 2026-10-23 实际检查（原样结果）

| 检查 | 结果 |
|---|---|
| 包路径 `sim/build/exe-wt/dist/cop-board-gate-21c4e751bbe8.tar.gz` | **不存在** |
| 同名 `.sha256` | **不存在** |
| 主工作区/两个 worktree 的 `dist/` | 不存在该包 |
| 用户 Desktop/Documents/Downloads、ZCode/临时目录 | 未找到该包或同名 tarball |
| D:/E: 根目录深度 3 | 未找到 |
| 远端分支 `dev/exe/dev/riscv/dev/vision/main` | 无该包；`dev/riscv=7c6cc40` |
| Vivado | 已安装：`D:\vivado\2026.1\Vivado\bin\vivado.bat` |
| `board/scripts/program_soc.bat` 默认 VIVADO | `D:\Vivado_downloads\2026.1\...`（与实机路径不一致，需 `set VIVADO=...`） |
| 板卡网络 | 无 192.168.50.x 接口；`ping 192.168.50.99` 失败；仅 Wi-Fi 10.54.149.251 |
| JTAG/USB | 未检测到 Xilinx/Digilent 设备；无 `hw_server`；仅有蓝牙 COM3/COM5 |

因此：**包哈希未验、106 文件未验、未解包、未烧写、未只读预检、未提交任务、未读结果。**

## 3. 记录表（本次全部 NOT RUN）

| 项 | 值 |
|---|---|
| 日期 | 2026-10-23 |
| 操作者 | WC |
| Vivado 版本 | 2026.1（已安装，未调用） |
| bit SHA256 | 交接值 `7e1e3430…aa0b6c`，未在本机复核 |
| STATUS / ERROR_CODE / RESULT_SEQ | NOT RUN |
| pattern class/margin/score/logits | NOT RUN |
| zero class/margin/score/logits | NOT RUN |
| 与 EXPECTED_OUTPUTS 一致 | NOT RUN |
| 温度 / 连续运行次数 / 首次失败原文 | NOT RUN（无板） |

## 4. 恢复条件

1. 把 `cop-board-gate-21c4e751bbe8.tar.gz` 与 `.sha256` 放到
   `D:\Desktop\contests\2026fpga\FPGA-Alittle-Design\sim\build\exe-wt\dist\`
   （或给出可访问的绝对路径/URL）。
2. 连接并上电板卡：USB JTAG（出现 Xilinx/Digilent 设备）或以太网
   `192.168.50.99` 可 SSH；确认板卡空闲、允许烧写。
3. 提供 Address Editor 分配的 PS AXI base（用于只读预检）。
4. 若要跑完整推理（而不是只读预检），还需要 J08 数据面/`PynqDmaPlane` 或包内
   等效的 payload/ROI 装载工具；当前 WC 的 `PynqDmaPlane` 仍是
   `NotImplementedError`，只有控制面/预检就绪。

恢复后执行顺序：

```bat
sha256sum -c cop-board-gate-21c4e751bbe8.tar.gz.sha256
tar -xzf cop-board-gate-21c4e751bbe8.tar.gz
cd cop-board-gate-21c4e751bbe8 && sha256sum -c SHA256SUMS
set VIVADO=D:\vivado\2026.1\Vivado\bin\vivado.bat
board\scripts\program_soc.bat dist\cop-board-gate-21c4e751bbe8\payload\pynq_cop_40mhz.bit
```

然后按 `docs/coprocessor-nc-handoff.md`：只读预检 → 确认无 UNCONSUMED →
提交 → 等 ACCEPTED → 等唯一终态 → 读 RESULT_SEQ/RESULT_* → 落盘后 CONSUME；
记录 STATUS/ERROR_CODE/RESULT_SEQ/class/margin/score/logits/温度/连续次数/首错原文。

## 5. 边界

- 这不是板级失败，也不是板级通过；是**环境未就绪**（包与板卡均缺失）。
- `BOARD` 仍为 `UNVERIFIED`；PROVISIONAL 诊断模型不是发布模型；下载成功也不等于验收。
- 未修改任何 RTL/固件/位流；未执行烧写。
