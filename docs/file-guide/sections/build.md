# build：逐文件说明

30个文件；返回[主页](../README.md)，完整关系见[搜索页](../index.html)或[JSON](../files.json)。

| 文件 | 一两句话说明 | 关联文件（最多展示5项） |
| --- | --- | --- |
| **build** | | |
| [build/README.md](../../../build/README.md)<br>说明/计划/契约 · 已纳入Git（含暂存） | 说明《build —— 可复现构建》的规则、过程或结果；其引用文件见关联栏，日期/候选/冻结边界按正文保留。 | 所在目录说明：[README.md](../../../README.md)<br>文本引用：[build/build.tcl](../../../build/build.tcl)<br>文本引用：[build/build_fmax.tcl](../../../build/build_fmax.tcl)<br>文本引用：[build/build_soc.tcl](../../../build/build_soc.tcl)<br>文档链接：[build/reports/timing_impl.rpt](../../../build/reports/timing_impl.rpt)<br>另9项见搜索页 |
| [build/build.tcl](../../../build/build.tcl)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 核独立综合/时序构建入口；资源和频率按该脚本的器件/约束口径解释。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/build_fmax.tcl](../../../build/build_fmax.tcl)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 执行核频率/OOC比较构建；报告按参数档保存，不能把slack外推当该频率实点通过。 | 所在目录说明：[build/README.md](../../../build/README.md)<br>文本引用：[build/build.tcl](../../../build/build.tcl)<br>文本引用：[build/constraints/core_top.xdc](../../../build/constraints/core_top.xdc)<br>文本引用：[docs/core_comparison.md](../../../docs/core_comparison.md) |
| [build/build_soc.tcl](../../../build/build_soc.tcl)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 构建最小SoC板级实现及报告；位流由board/scripts下载，软件镜像按参数预载。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| **build/constraints** | | |
| [build/constraints/core_top.xdc](../../../build/constraints/core_top.xdc)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 规定核独立综合/实现时的时钟约束；与build脚本一起解释OOC频率口径。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/constraints/pynq_z2_soc.xdc](../../../build/constraints/pynq_z2_soc.xdc)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 绑定PYNQ-Z2最小SoC的板钟/复位/LED及相应时序；与pynq_z2_top和build_soc配套。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| **build/reports** | | |
| [build/reports/design_analysis_impl.rpt](../../../build/reports/design_analysis_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存该轮设计分析报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| **build/reports/soc_40mhz_bht2** | | |
| [build/reports/soc_40mhz_bht2/soc_check_timing.rpt](../../../build/reports/soc_40mhz_bht2/soc_check_timing.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_clock_utilization_impl.rpt](../../../build/reports/soc_40mhz_bht2/soc_clock_utilization_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_clock_utilization_synth.rpt](../../../build/reports/soc_40mhz_bht2/soc_clock_utilization_synth.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_drc_impl.rpt](../../../build/reports/soc_40mhz_bht2/soc_drc_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存设计规则检查报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_timing_impl.rpt](../../../build/reports/soc_40mhz_bht2/soc_timing_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_timing_worst_paths.rpt](../../../build/reports/soc_40mhz_bht2/soc_timing_worst_paths.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_utilization_impl.rpt](../../../build/reports/soc_40mhz_bht2/soc_utilization_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_utilization_synth.rpt](../../../build/reports/soc_40mhz_bht2/soc_utilization_synth.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_40mhz_bht2/soc_vivado_version.txt](../../../build/reports/soc_40mhz_bht2/soc_vivado_version.txt)<br>文本记录 · 已纳入Git（含暂存） | 保存soc_vivado_version的文本记录或工具读回；用于build/README.md中对应步骤的对照，不从文件名推断PASS。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| **build/reports** | | |
| [build/reports/soc_check_timing.rpt](../../../build/reports/soc_check_timing.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_clock_utilization_impl.rpt](../../../build/reports/soc_clock_utilization_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_clock_utilization_synth.rpt](../../../build/reports/soc_clock_utilization_synth.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_drc_impl.rpt](../../../build/reports/soc_drc_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存设计规则检查报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_timing_impl.rpt](../../../build/reports/soc_timing_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_timing_worst_paths.rpt](../../../build/reports/soc_timing_worst_paths.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_utilization_impl.rpt](../../../build/reports/soc_utilization_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_utilization_synth.rpt](../../../build/reports/soc_utilization_synth.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/soc_vivado_version.txt](../../../build/reports/soc_vivado_version.txt)<br>文本记录 · 已纳入Git（含暂存） | 保存soc_vivado_version的文本记录或工具读回；用于build/README.md中对应步骤的对照，不从文件名推断PASS。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/timing_impl.rpt](../../../build/reports/timing_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/timing_synth.rpt](../../../build/reports/timing_synth.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/timing_worst_paths.rpt](../../../build/reports/timing_worst_paths.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存时序路径和slack报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/utilization_impl.rpt](../../../build/reports/utilization_impl.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
| [build/reports/utilization_synth.rpt](../../../build/reports/utilization_synth.rpt)<br>Vivado报告 · 已纳入Git（含暂存） | 保存资源占用报告，供build/README.md复查；它是工具输出，不是待编辑的RTL。 | 所在目录说明：[build/README.md](../../../build/README.md) |
