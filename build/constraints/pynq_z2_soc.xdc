# PYNQ-Z2 RISC-V SoC 板级约束。
# 引脚源：官方 PYNQ-Z2 Master XDC，原文件 SHA256：
# 07441e999bac956c77e78091c782cade278efc5a78affc51e5b12b4800b1fe73

# 板载 PL 时钟：H16，125 MHz。
set_property -dict {PACKAGE_PIN H16 IOSTANDARD LVCMOS33} [get_ports {clk}]
create_clock -name sys_clk_125 -period 8.000 -waveform {0.000 4.000} [get_ports {clk}]

# MMCME2_BASE：125 MHz * 8 / 25 = 40 MHz。
create_generated_clock -name core_clk_40 \
    -source [get_pins {u_mmcm/CLKIN1}] -multiply_by 8 -divide_by 25 \
    [get_pins {u_mmcm/CLKOUT0}]

# BTN0：高电平按下；四个用户 LED：高电平点亮。
set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports {btn0}]
set_property -dict {PACKAGE_PIN R14 IOSTANDARD LVCMOS33} [get_ports {led[0]}]
set_property -dict {PACKAGE_PIN P14 IOSTANDARD LVCMOS33} [get_ports {led[1]}]
set_property -dict {PACKAGE_PIN N16 IOSTANDARD LVCMOS33} [get_ports {led[2]}]
set_property -dict {PACKAGE_PIN M14 IOSTANDARD LVCMOS33} [get_ports {led[3]}]

# BTN0 仅驱动异步复位；LED 没有外部采样时钟，均不声明虚假 I/O 延迟。
set_false_path -from [get_ports {btn0}]
set_false_path -to [get_ports {led[*]}]
