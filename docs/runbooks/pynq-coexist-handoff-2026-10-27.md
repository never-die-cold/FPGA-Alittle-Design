# 2026-10-27 PYNQ 共存与 EXE 交接

全局状态以 [plan.md §3.1](../../plan.md#31-当前状态) 为准。基线为 `dev/riscv / bc37c08` 加本轮工作区改动。

10/28 更新：多目标修复版共存位流及 CNN r6 已上板，12 轮/85 个目标的整数输出逐项一致，视频/API 已恢复。新包路径、源码锚点、并发快进引起的 loader 兼容修复及剩余定位/分类问题见[本次实板记录](../../data/logs/2026-10-28-multitarget-board-r6/README.md)。下文旧包与失败构建保留为历史证据。

## 已确认的链路

- 启动竞争：cron vision 与 bootpy base 互相覆盖。新增 `fpga-vision-boot.service` 依赖 bootpy；备份并移除两个自动装载/原型服务任务，保留 IP 配置。正常重启复验成功；不等于所有冷启动/长测通过。
- 共存地址：COP `0x40000000`、MM2S `0x40010000`、GPIO `0x40020000`、视频配置 `0x41000000`、CAP1 `0x42000000`、VDMA `0x43000000`。MMCM 输入约 142.857 MHz，输出 40 MHz。
- `raw_capture` 构建保留彩色视频显示/完整 BGR 原帧捕获。PL 灰度/高斯/缩放分析输出没有消费者而被优化；定位、灰度 ROI 与量化由 PS 执行，不能将其写成 PL 预处理已接入。
- 共存旧包 bit SHA256 `b2690b0aa69df36c1638b5b652ce8bcf0c97f2799d302b332f5bcd432c3313b3`；HWH SHA256 `5b54d888779410bd192cc8f45633c4a4620f489755e8fd801b040215c862aed0`。本次恢复 DCP 后重新计算 WNS +1.184 ns、WHS +0.005 ns，8192 个 IMEM 字逐一匹配。
- 原板端包 `/home/xilinx/cop-pkg-product-20261027-r1`、服务源码 `/home/xilinx/cop-app-product-20261027-r1`。最后 EXE 联调服务 `/home/xilinx/cop-live-exe-20261027-r2` 使用工单 2/4/4；服务没有安装为整机自启动，重启后仍回到视频基线。

## 多目标阻断及修复边界

实板旧包第 0 结果槽为空，其后各槽等于前一个 ROI 的整数参考输出；最后一槽被最后输出覆盖。
原因是 `result_write` 寄存后，槽号同拍提前递增，下一沿结果 RAM 消费脉冲时地址已改变。
增加 `COMMIT_RESULT` 一拍，保持槽号到写入完成；不改变寄存器布局。

```powershell
& E:\Git\bin\bash.exe sim/scripts/run_iverilog.sh cop_multitarget_commit
& E:\Git\bin\bash.exe sim/scripts/run_iverilog.sh cop_axi_cdc_skew
```

三目标用例旧版 FAIL、修复 PASS；原 task_ctrl / AXI CDC / 固件两单检查通过。
`pynq_product_multitarget_20261027_r2` 构建于 19:43 因 capture_input 综合子进程
`Could not open 'C' for writing` / `tclapp::load_apps` 失败，修复包**尚未生成并上板**。
旧共存包仅可用于接口/视频联调，不用于多目标识别验收。

## EXE 联调与待办

采集卡索引要按 `sim/scripts/list_dshow_video.ps1` 中 `USB Video` 现场枚举；本轮为 2。

```powershell
sim/build/vision-client/dist/vision_preview/vision_preview.exe --source 2 --endpoint http://192.168.50.99:8765 --interval 3 --max-age 8 --records-dir data/logs/<新运行目录>/records
python src/vision_client/export_records.py data/logs/<运行目录>/records
```

已确认真实视频、LIVE 接口、工单差额、JSONL 记录。界面操作被物理 Esc 中止，
手动按钮核验与 CSV 导出**未完成**；第二条命令是后续入口，不是已执行结果。
当前判定 RECHECK，识别质量与训练待用户换环境后继续。旧包结果错位修复完成前不得将错误类别当真值。

## 证据与复现

- [并发审计](../../data/logs/2026-10-27-concurrent-agent-audit/README.md)
- [启动/时钟修复](../../data/logs/2026-10-27-startup-clock-repair/README.md)
- [共存与真实帧](../../data/logs/2026-10-27-product-coexist/README.md)
- [提交前定向检查](../../data/logs/2026-10-27-git-integration/README.md)

SD 历史存在 mmc/ADMA/I/O 故障，本轮未复现，尚不能认定卡损坏。
全量回归曾中止，不能称 all PASS；本次按用户快速模式进行相关定向检查。
