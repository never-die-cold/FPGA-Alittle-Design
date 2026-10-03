# ARM 文件输入定位/裁剪：证据索引

日期：2026-10-03；开发起点 `8a2384c`。本节单次结果为第 1 步历史证据，最终验收见下节。
复现入口与板端命令见 `docs/arm-localize-baseline-plan.md`。

- two_targets.json：固定 12×8 GRAY8 合成图，两个暗目标与一个面积不足的孤立噪点。
- pc-result.json：Windows PC 输出；arm-result.json：PYNQ ARM 原始输出。
- 目标 bbox 闭区间为 [1,1,2,4] / [7,2,9,5]，面积 8 / 12。
- 输出尺寸均 64×64，全像素为对应目标的 20 / 30；输入与参考实现 SHA256 一致。
- ARM 运行环境为 Linux / armv7l / Python 3.10.4。
- ARM 单次定位 1.240646 ms、裁剪 259.325834 ms；不含文件 I/O，未作统计性能验收。
- 日志在 `data/logs/2026-10-03-arm-localize-baseline/step1-*.log`。

本证据仅支持合成固定图片软件参考的跨平台一致性；不代表实际紧固件识别、
真实相机、实时 HDMI/PL 输入或工业检查闭环已经完成。

## 最终交付（原第 1 步文件保留为历史记录）

- arm-localize-package.tar.gz / final-package-manifest.json：最终部署包与精确源文件哈希。
- final-pc-result.json：最终 PC 固定图结果，包含图片/hex 清单。
- arm-board-final/arm_localize/：最终板端完整目录、代码清单、固定结果及 benchmark。
- pc-benchmark/summary.json：最终 PC 采样索引；只使用其引用会话，旧会话为尝试记录。
- arm-board-final/arm_localize/benchmark/summary.json：ARM 预热 1 次、每场景 5 次的索引。
- arm-results-final.tar.gz：最终板端归档。arm-board/ 与 arm-results.tar.gz 是前轮记录。
- 三场景 15 组最终样本的框、像素、PGM/hex 字节与哈希逐项一致。
- 性能与边界见 docs/arm-localize-results.md；全量样本留在仓库，没有使用工作区外临时文件验证。
