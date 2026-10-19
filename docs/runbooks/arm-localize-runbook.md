# ARM 文件定位/裁剪便携包

仅依赖 Python 3.10+ 标准库；输入为 GRAY8 JSON 矩阵，不加载 Overlay，不使用摄像头。
数据与结果均明确标为 FILE_REFERENCE；没有类别、工单通过或真实视频关联。

## PC 组包

```bash
python sim/scripts/make_arm_localize_pkg.py
```

输出 `sim/build/arm-localize-package.tar.gz`。包只携带运行器、参考、自检、性能脚本、固定输入和说明。
manifest.json 保存基线 commit 与各文件 SHA256；精确版本以这些哈希为准，不能把未提交代码视为该 commit 原样。

## 板端执行

将 tar.gz 传到板端专用工作目录；解压后执行：

```bash
tar -xzf arm-localize-package.tar.gz
cd arm_localize
python3 -I -B arm_localize_selftest.py
python3 -I -B arm_localize.py two_targets.json result.json --size 64 64 --frame-id 7 --config-id 3
python3 -I -B arm_localize_bench.py --out benchmark --warmup 1 --repeats 5
```

无需 root。自检校验包内文件哈希后才运行定位；缺文件/改文件返回非零。
固定输入 12×8、两个暗目标；自检坐标为 [1,1,2,4] 和 [7,2,9,5]。

## 结果与导出

- result.json 保存 source/reference 哈希、框、小图、参数、环境和计算耗时。
- artifacts 是当前有效文件清单；每目标一份 P5 PGM 和 hex，路径相对 result.json 的父目录。
- PGM 为 `P5\n宽 高\n255\n` + GRAY8 字节；hex 每行一个两位十六进制像素。
- 两种文件均按 y 外层、x 内层（行优先）排列；尺寸、目标/frame/config 编号与文件哈希随清单保存。
- 每次使用独立批次目录。先完成所有导出，再原子替换结果 JSON；旧文件不在新清单中即不可使用。
- RECHECK 或空场景的 artifacts 为空；失败时退出非零，不发布新清单。消费者必须检查退出码及来源。
- 固定图片的 frame/config 编号只是测试标识，不表示已取得硬件帧关联。

## 性能口径

三种合成场景：12×8 两目标、1280×720 空背景、1280×720 六个分散且有灰度变化的目标。
每场景预热 1 次，再采样 5 次；输入、每次 JSON/PGM/hex 和 summary.json 全保留。
locate/crop 为计算阶段，不含文件 I/O；total_call 包含读入、验证、计算、导出及 JSON 发布。
报告 min/median/p95/max；p95 用最近秩，5 次采样的 p95 等于 max，不代表大量样本估计。
合成数据用于一致性/性能基线，不能替代真实紧固件精度、光照与反光测试。
重复执行会保存新的批次目录；保留证据时复制整个 benchmark 目录，不能只拿 summary.json。
