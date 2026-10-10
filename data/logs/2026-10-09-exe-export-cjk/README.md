# 2026-10-09 EXE 自主推进批次：CSV 记录导出 + 中文渲染能力（M3 预置）

用户指示（2026-10-09）："你一路推进，把能做到的都做了"（硬件实测不可行、NC 不在）。
本批交付两件不依赖板卡/NC 的前置能力（M4 记录导出项 + M3 中文显示预置）。

## 1. CSV 记录导出（M4「记录导出」项）

- `src/vision_client/export_records.py`：`py export_records.py <记录目录> [--out PATH]`
  → `records.csv`。设计要点：**UTF-8-BOM**（Excel 双击打开中文不乱码）；targets 列保留
  JSON（含 bbox）；记录文件缺失时报错退出（不静默产出空表）。
- 测试 `sim/vision/test_vision_export.py`（已接入 `run_vision_python.sh`，全量 8 项）：
  表头/行数/关键字段/targets 单元格/**BOM 字节断言**/缺文件报错。
- 真实样本：`data/logs/2026-10-09-exe-hud-v4/manual-dpi-run/records.csv`（6 条实机记录导出）。

## 2. 中文渲染（M3 类别名/工单判定预置）

- 字体：Noto Sans SC 变量字体**子集化**——字符集 = ASCII + GB2312 全集（6763 字）+ 常用
  符号，**17.3MB → 4.0MB**；生成脚本 `src/vision_client/assets/fonts/make_cjk_subset.py`
  （可复现：jsDelivr 取全量源 → fontTools pyftsubset；缺字补 EXTRA 重跑）；OFL 许可证随包。
- 引擎 `hud_text.TextEngine`：按文本内容自动选字体（含 CJK 码点 → Noto SC，含混合文本
  "螺栓 ×3"；纯拉丁 → Inter）。
- 打包验证：selftest 断言"CJK 字体在包内 + 中文可渲染"；`_internal/assets/fonts/` 入包核对。
- 渲染样本：`cjk_sample.png`（类别名/工单判定/等待状态/混合文本，无缺字）。

## 验证

- 打包三关 PASS（build_exe_cjk.log；selftest 含中文断言）
- 全量 Python 回归 **8/8 PASS**（test_*.log）
- 导出功能冒烟：对实机 6 条记录导出 CSV，字段与 targets 内容抽查正确

## 边界

MOCK 数据；中文文案的上屏位置（列表卡类别名 / 判定徽标）留待 M3 接真实结果时启用。
