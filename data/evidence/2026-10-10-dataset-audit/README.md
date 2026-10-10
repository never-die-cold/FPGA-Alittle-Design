# 数据集审计：测试夹具证据

基线 dev/model @ b51d46b。fixture 内为 4 张均匀 uint8 BGR PNG，标注为虚构的
bolt/nut/washer 各一条及一条显式空帧；它们不是工件图或模型准确率数据。
生成入口为 `sim/vision/generate_dataset_audit_fixture.py`，不会覆盖已有目录。

最终 `report.json`：source_kind=TEST_FIXTURE，status=STRUCTURE_PASS，4 帧/3 目标。
train 缺 nut/washer，val 缺 bolt/washer，test 缺 bolt/nut。
实物编号全部填写，但其真实性、人工标签与相机来源均未认证；没有模型精度值。

```powershell
python -I sim/vision/audit_fastener_dataset.py data/evidence/2026-10-10-dataset-audit/fixture sim/build/vision/inspection/audit-review.json --source-kind TEST_FIXTURE --max-targets 10
```

报告无时间戳或输出目录字段；同数据/代码/运行版本可逐字节复算。
输出须为新文件，已有报告或 pending 不自动覆盖。CSV 以 LF 保存，与仓库换行规范一致。
首次 CRLF 过程记录保留于 data/logs/2026-10-10-dataset-audit/initial-manifest.bin 和 initial-report.json。
完整验证见[日志索引](../../logs/2026-10-10-dataset-audit/README.md)，格式与限制见[审计说明](../../../docs/fastener-dataset-audit.md)。
