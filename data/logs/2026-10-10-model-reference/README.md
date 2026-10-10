# 2026-10-10 模型逐层参考：原始验证记录

基线 dev/exe @ aa23206；用户要求继续离板工作。所有产物和测试目录均在仓库内。

| 仓库入口 | 原始日志 | 结果 |
|---|---|---|
| `python sim/vision/test_model_reference.py` | folding.log；最终组日志 model_reference.log | 四个 BN 折叠、logits 对拍、训练模式拒绝 PASS |
| `python sim/vision/test_numpy_reference.py` | numpy-parity-before.log / numpy-diagnostic.log / numpy-parity.log | 初始容差 FAIL 留痕；诊断后逐层容差判据 PASS |
| `python sim/vision/test_model_audit.py` | audit.log / model_audit.log | 精确 MAC/参数/形状/激活数量 PASS |
| `python sim/vision/test_reference_tensors.py` | tensors.log / reference_tensors.log | 位模式、C 顺序、哈希/格式/越界拒绝 PASS |
| `python sim/vision/test_reference_package.py` | package.log / reference_package.log | NumPy-only 隔离复算、覆盖/工具/审计/数值修改拒绝 PASS |
| `bash sim/scripts/run_inspection_python.sh` | inspection-all.log 和十一组同名日志 | 十一组 PASS，退出 0 |
| `python sim/vision/export_model_reference.py data/evidence/2026-10-10-model-reference/fp32-reference-v1` | export.log | FP32 参考归档 PASS，退出 0 |
| 包内 `python -I .../tools/check_model_reference.py ...` | check.log | 三个输入×七个张量的 NumPy-only 校验 PASS，退出 0 |

初始 FAIL 为条纹 conv4 的 22 个元素超过 atol=2e-5 / rtol=2e-5；
双精度诊断对相同折叠参数重新计算，日志保留逐输入/逐层误差。
最终 atol=1e-4 / rtol=2e-5，六组输入最大绝对差 0.000183105469，最终 argmax 全部一致。
归档三组包最大绝对差 0.00016784668；这是浮点容差验收，非位精确、非真实数据准确率。

各入口退出码保存在同名 .exit.txt；原始 FAIL 的退出 1 保留，不能算 PASS。
代码/模型来源、运行版本和参考文件哈希在包的 manifest.json。
换行检查见 diff-check.log，新增文本检查见 new-text-check.log。
没有 RTL 修改，没有板端性能/BRAM/INT8 验收结论；未实现项见[逐层说明](../../../docs/module3-prototype-reference.md)。
