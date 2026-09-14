# core_top.xdc —— v0 RISC-V 核时序约束（Fmax/WNS 基线）
# 目标 100 MHz：README 指标表要求 Fmax >= 100 MHz 且 WNS >= 0
create_clock -name sys_clk -period 10.000 [get_ports clk]

# OOC（out_of_context）模式的时钟源标注：告知工具该时钟在父级设计中的
# 缓冲位置，消除 "HD.CLK_SRC not set" 警告并使时钟延迟/偏斜可估算
set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]
