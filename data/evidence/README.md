# data/evidence —— 证据区索引

> 给谁看：查“某个结论的输入、哈希、bit 溯源、黄金参考”的人。
> 规则：一个证据主题一个目录；目录名 `YYYY-MM-DD-topic`；每个目录必须有 `README.md`。
> 模板：[`_template/README.md`](_template/README.md)。新增目录后运行 `python sim/scripts/index_runs.py --write` 刷新本索引。

## 证据类型

- **源码/构建输入快照**：用于证明某次 bitstream 或测试由哪些文件产生；必须有 `manifest.json`（路径、sha256、来源 commit/包）。
- **黄金参考**：测试答案/参考向量；必须写生成入口和算法边界。
- **溯源材料**：XSA、HWH、日志、哈希、照片；不反序列化、不执行。
- **外包交付**：原字节保留；接收清单见 `data/evidence/2026-10-10-fastener-handoff/`。

## 硬规则

1. 已归档证据不删不改；需要重跑时新建目录，旧目录保留。
2. 每个目录的 `README.md` 写清：来源、日期、commit/包版本、校验方式、能证明什么、不能证明什么。
3. 大文件优先存哈希/下载脚本；确需入库的二进制要写明理由。
4. 缺 README 的目录标记 `PROVENANCE GAP`；补说明时不得把“有文件”写成“已验收”。

<!-- RUN-INDEX:START -->
## 目录索引（9 个证据主题，自动生成）

| 目录 | 日期 | 文件数 | 大小 | 说明 |
|:---|:---:|---:|---:|:---|
| `2026-10-28-web-hud-shots` | 2026-10-28 | 10 | 3.5 MB | 网页端 HUD 评审截图存档 |
| `2026-10-28-cnn-r6` | 2026-10-28 | 13 | 265 KB | CNN r6：清晰竖立螺母开发候选 |
| `2026-10-13-ddr-experiment-inputs` | 2026-10-13 | 8 | 43 KB | 2026-10-13-ddr-experiment-inputs |
| `2026-10-12-c01-exact-build-inputs` | 2026-10-12 | 101 | 2.6 MB | C01构建输入的精确字节恢复（2026-10-12） |
| `2026-10-10-onboard-bit-provenance` | 2026-10-10 | 2 | 490 KB | 上板位流字节对应（2026-10-10） |
| `2026-10-10-offline-inspection` | 2026-10-10 | 16 | 354 KB | FILE_REPLAY 示例证据 |
| `2026-10-10-model-reference` | 2026-10-10 | 75 | 3.4 MB | 交付原型 FP32 软件参考包 |
| `2026-10-10-fastener-handoff` | 2026-10-10 | 3 | 17 KB | 2026-10-10-fastener-handoff |
| `2026-10-03-arm-localize-baseline` | 2026-10-03 | 2 | 1 KB | 2026-10-03-arm-localize-baseline（最小留存） |
<!-- RUN-INDEX:END -->

## 相关入口

- 运行日志索引：[`data/logs/README.md`](../logs/README.md)
- 指标汇总：[`data/metrics.csv`](../metrics.csv)
- 目录地图：[`docs/project-map.md`](../../docs/project-map.md)
