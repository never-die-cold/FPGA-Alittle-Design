# 仓库整理基线（2026-10-19）

> 本文件记录 `chore/repo-cleanup` 分支开工前的只读盘点。后续整理步骤逐条对照本基线验收。
> 基线提交：`d87c9cc`（dev/model）；基线 tag：`pre-cleanup-2026-10-19`。

## 1. Git 状态

- 分支：`dev/model` → 新建 `chore/repo-cleanup`
- 工作区：干净（`git status --porcelain=v1` 无输出）
- 提交数：417
- 跟踪文件：5,638
- pack：91.75 MiB（`git count-objects -vH`）
- 本地额外分支：`dev/bench`、`dev/verify`（均与 main 同步，0 ahead）
- tag：`partA-v0`、`archive/pi-hdmi-diagnostics-2026-10-08`

## 2. 工作区磁盘

| 目录 | 文件数 | 字节 |
|:---|---:|---:|
| sim | 20,857 | 3,413,097,507 |
| data | 4,974 | 223,785,397 |
| .git | 484 | 108,016,484 |
| build | 204 | 45,448,933 |
| docs | 123 | 18,376,158 |
| src | 183 | 6,399,245 |
| models | 3 | 8,290,668 |
| .Xil | 6 | 2,608,293 |
| results | 22 | 1,092,706 |

其中 `sim/build` 2.10 GB / 17,452 文件，`sim/arch_test/suite` 1.29 GB / 2,638 文件。

## 3. 跟踪数据

- `data/`：4,912 文件 / 172,488,605 字节
  - `data/logs`：3,947 文件 / 117,820,007 字节
  - `data/evidence`：928 文件 / 54,589,065 字节
  - `data/golden`：29 文件 / 42,795 字节
  - `data/scripts`：6 文件 / 17,605 字节
- 扩展名占用（前 10）：PNG 47.0 MB、JSON 43.1 MB、txt 18.7 MB、log 14.2 MB、rpt 9.9 MB、hex 5.9 MB、ttf 5.0 MB、patch 3.9 MB、zip 3.4 MB、pdf 2.7 MB。

## 4. 文档与索引

- 跟踪 Markdown：444 篇。
- `docs/`：118 个文件 / 18,277,799 字节；其中 `docs/file-guide` 33 个文件，23 个为生成物（13.7 MB）。
- `docs/file-guide` 快照：`c3b6a1e`，覆盖 4,604 个项目文件；当前跟踪文件 5,638，索引已落后 1,034 个。
- `report/llm_log`：155 个文件 / 762,180 字节。
- 相对链接检查：444 篇 Markdown、15,758 条相对链接、189 条缺失；排除 `data/logs`、`data/evidence` 历史快照后 295 篇、15,384 条、25 条缺失。

## 5. 运行记录覆盖

- `data/logs`：113 个顶层目录，88 个有 `README.md`，25 个没有。
- `data/evidence`：15 个顶层目录，7 个有 `README.md`，8 个没有。
- 缺少 README 的日志目录：
  `2026-09-28-partA-closure`、`2026-09-30-m3-train-drill`、`2026-09-30-scaler-retiming`、`2026-10-01-vision-m2-sprint`、`2026-10-03-arm-localize-baseline`、`2026-10-03-m3-brevitas-drill`、`2026-10-04-partB-v1`、`2026-10-07-hdmi-diagnostic`、`2026-10-11-c01-capture-probe`、`2026-10-11-c01-hdmi-1791709865447608`、`2026-10-11-c01-hdmi-1791710034565325`、`2026-10-11-c01-hdmi-1791710185764742`、`2026-10-11-c01-hdmi-1791711069004993`、`2026-10-11-c01-hdmi-1791711577420841`、`2026-10-11-c01-hdmi-1791713720540454`、`2026-10-15-onboard-n02-n03`、`c01-capture-19af0b2c829447b89d442a6f4f09f8f3`、`c01-capture-e2a602d6e0da49a2b6da072abca47c70`、`cnn-ooc-106904d01e0045089b9d1688ddce6e85`、`cnn-ooc-1cefffc05185438195b8803d87fc11df`、`cnn-ooc-4065cdcc415b43fbbc713dbeeceddbfb`、`cnn-ooc-5c9bc74c61e7445ca8c56b2f49389102`、`cnn-ooc-a96a8b86f6264e50af90da61e3dc3aa9`、`cnn-ooc-da63cadcd3db4a9e9f826cf2e4949e68`、`local-vivado-originals`。
- 缺少 README 的证据目录：
  `2026-10-10-fastener-handoff`、`2026-10-13-cnn-address-ooc-inputs`、`2026-10-13-cnn-ooc-inputs`、`2026-10-13-cnn-pipeline-ooc-inputs`、`2026-10-13-ddr-experiment-inputs`、`2026-10-13-soc-reset-ce`、`cnn-ddr-offline-0635d33e8e274f88a88cd2a6a90464b2`、`cnn-ddr-offline-cdfbf6823fe24cfe8015449a9b0da708`。

## 6. 重复与快照

- 619 组相同 blob，工作区重复内容约 41 MB。
- 最大重复：4 份 3.7 MB `input.json`、2 份 4.08 MB `NotoSansSC-Subset.ttf`、3 份 HDMI IP PDF/DOCX/XCI。
- `data/logs` 下源码/输入快照 924 个文件：
  - 564 个与当前非 data 文件相同（约 7 MB）；
  - 270 个只与其他快照相同（约 5 MB）；
  - 90 个唯一（约 570 KB）。

## 7. Worktree

| 路径 | 大小 | 状态 |
|:---|---:|:---|
| `E:/Projects/FPGA-Alittle-Design-rtl` | 255 MB | 4 个未跟踪日志 |
| `E:/Projects/FPGA-Alittle-Design-vision` | 574 MB | 干净 |
| `C:/Users/ASUS/.codex/worktrees/non-algorithm-system/FPGA-Alittle-Design` | 63 MB | 干净 |
| `E:/Projects/FPGA-Alittle-Design/sim/build/git-delivery/dev-exe-sync` | 188 MB | 未完成 merge，9 个文件与当前 HEAD 不同 |

## 8. 盘点命令

```powershell
git status --porcelain=v1
git ls-files | Measure-Object -Line
git count-objects -vH
git worktree list
Get-ChildItem -Directory -Force | ForEach-Object {
  $m = Get-ChildItem -LiteralPath $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
       Measure-Object -Property Length -Sum
  '{0}|{1}|{2}' -f $_.Name, $m.Count, $m.Sum
}
```

## 9. 整理过程记录

- 2026-10-19：P0 开工；建 `chore/repo-cleanup` 分支与 `pre-cleanup-2026-10-19` tag；本文件入库。
