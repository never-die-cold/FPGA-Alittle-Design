# data-golden：逐文件说明

29个文件；返回[主页](../README.md)，完整关系见[搜索页](../index.html)或[JSON](../files.json)。

| 文件 | 一两句话说明 | 关联文件（最多展示5项） |
| --- | --- | --- |
| **data/golden/coremark_2k_32iter** | | |
| [data/golden/coremark_2k_32iter/README.md](../../../data/golden/coremark_2k_32iter/README.md)<br>说明/计划/契约 · 已纳入Git（含暂存） | 说明《Golden：CoreMark 2K profile / 32 迭代 crcfinal》的规则、过程或结果；其引用文件见关联栏，日期/候选/冻结边界按正文保留。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[data/evidence/2026-09-23-coremark-source.md](../../../data/evidence/2026-09-23-coremark-source.md)<br>文本引用：[docs/coremark.md](../../../docs/coremark.md) |
| **data/golden/vision/fullchain** | | |
| [data/golden/vision/fullchain/expected_fullchain.hex](../../../data/golden/vision/fullchain/expected_fullchain.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_fullchain的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/fullchain/expected_gauss_sobel.hex](../../../data/golden/vision/fullchain/expected_gauss_sobel.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_gauss_sobel的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/fullchain/expected_gray_sobel.hex](../../../data/golden/vision/fullchain/expected_gray_sobel.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_gray_sobel的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/fullchain/gen_fullchain.py](../../../data/golden/vision/fullchain/gen_fullchain.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_fullchain相关流程，定义at、spec_gauss、src_coord、lerp8；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/fullchain/gen_top_sobel.py](../../../data/golden/vision/fullchain/gen_top_sobel.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_top_sobel相关流程，定义load_hex、at、sobel_ref、save_hex；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[data/golden/vision/sobel/gen_sobel.py](../../../data/golden/vision/sobel/gen_sobel.py) |
| **data/golden/vision/gaussian3x3** | | |
| [data/golden/vision/gaussian3x3/expected_y.hex](../../../data/golden/vision/gaussian3x3/expected_y.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_y的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/gaussian3x3/gen_gaussian3x3.py](../../../data/golden/vision/gaussian3x3/gen_gaussian3x3.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_gaussian3x3相关流程，定义gen_gray、at、spec_gauss、main；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[src/vision/design_v0.md](../../../src/vision/design_v0.md) |
| [data/golden/vision/gaussian3x3/input_gray.hex](../../../data/golden/vision/gaussian3x3/input_gray.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存input_gray的输入像素/张量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| **data/golden/vision/localize** | | |
| [data/golden/vision/localize/gen_patterns.py](../../../data/golden/vision/localize/gen_patterns.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_patterns相关流程；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/localize/patterns_expected.hex](../../../data/golden/vision/localize/patterns_expected.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存patterns_expected的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/localize/patterns_rgb.hex](../../../data/golden/vision/localize/patterns_rgb.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存patterns_rgb的固件或数值测试向量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/localize/reference.py](../../../data/golden/vision/localize/reference.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置reference相关流程，定义locate、crop_resize、coord、prepare_targets；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| **data/golden/vision/osd** | | |
| [data/golden/vision/osd/expected_osd_f1.hex](../../../data/golden/vision/osd/expected_osd_f1.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_osd_f1的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/osd/expected_osd_f2.hex](../../../data/golden/vision/osd/expected_osd_f2.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_osd_f2的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/osd/gen_osd.py](../../../data/golden/vision/osd/gen_osd.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_osd相关流程，定义border_hit、main；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[src/vision/design_v0.md](../../../src/vision/design_v0.md) |
| [data/golden/vision/osd/input_y.hex](../../../data/golden/vision/osd/input_y.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存input_y的输入像素/张量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| **data/golden/vision/rgb2gray** | | |
| [data/golden/vision/rgb2gray/expected_y.hex](../../../data/golden/vision/rgb2gray/expected_y.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_y的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/rgb2gray/gen_rgb2gray.py](../../../data/golden/vision/rgb2gray/gen_rgb2gray.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_rgb2gray相关流程，定义gen_image、spec_y、main；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[src/vision/design_v0.md](../../../src/vision/design_v0.md) |
| [data/golden/vision/rgb2gray/input_rgb.hex](../../../data/golden/vision/rgb2gray/input_rgb.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存input_rgb的输入像素/张量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| **data/golden/vision/scaler** | | |
| [data/golden/vision/scaler/expected_y.hex](../../../data/golden/vision/scaler/expected_y.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_y的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/scaler/gen_scaler.py](../../../data/golden/vision/scaler/gen_scaler.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_scaler相关流程，定义gen_gray、at、src_coord、lerp8；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[src/vision/design_v0.md](../../../src/vision/design_v0.md) |
| [data/golden/vision/scaler/input_gray.hex](../../../data/golden/vision/scaler/input_gray.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存input_gray的输入像素/张量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| **data/golden/vision/scaler_ds** | | |
| [data/golden/vision/scaler_ds/expected_y.hex](../../../data/golden/vision/scaler_ds/expected_y.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_y的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/scaler_ds/gen_scaler_ds.py](../../../data/golden/vision/scaler_ds/gen_scaler_ds.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_scaler_ds相关流程，定义gen_gray、at、src_coord、lerp8；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/scaler_ds/input_gray.hex](../../../data/golden/vision/scaler_ds/input_gray.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存input_gray的输入像素/张量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| **data/golden/vision/sobel** | | |
| [data/golden/vision/sobel/expected_y.hex](../../../data/golden/vision/sobel/expected_y.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存expected_y的期望输出；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/golden/vision/sobel/gen_sobel.py](../../../data/golden/vision/sobel/gen_sobel.py)<br>源码/配置脚本 · 已纳入Git（含暂存） | 实现/配置gen_sobel相关流程，定义gen_gray、at、spec_sobel、main；实际导入、例化和文本引用见关联栏，与data/README.md配套阅读。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[src/vision/design_v0.md](../../../src/vision/design_v0.md) |
| [data/golden/vision/sobel/input_gray.hex](../../../data/golden/vision/sobel/input_gray.hex)<br>十六进制数据 · 已纳入Git（含暂存） | 以十六进制数据形式保存input_gray的输入像素/张量；由对应加载器/testbench读取，位宽、排布和端序按data/README.md核对。 | 所在目录说明：[data/README.md](../../../data/README.md) |
