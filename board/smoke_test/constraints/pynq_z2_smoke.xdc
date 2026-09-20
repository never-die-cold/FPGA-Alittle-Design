# Source: official PYNQ-Z2 Master XDC, accessed 2026-09-20.
# Official index: https://pynq.readthedocs.io/en/v3.1/overlay_design_methodology/board_settings.html
# Archive: https://dpoauwgwqsy2x.cloudfront.net/Download/pynq-z2_v1.0.xdc.zip
# Member: PYNQ-Z2 v1.0.xdc
# Original member SHA256: 07441e999bac956c77e78091c782cade278efc5a78affc51e5b12b4800b1fe73
# Enabled Clock/LEDs/Buttons entries; renamed sysclk -> clk, btn[0] -> btn0.
# Pin locations, I/O standards and the 8 ns clock are unchanged.
# BTN0 and LEDs are active high: TUL Reference Manual v1.0, section 14.

set_property -dict {PACKAGE_PIN H16 IOSTANDARD LVCMOS33} [get_ports {clk}]
create_clock -name sys_clk_pin -period 8.000 -waveform {0 4} [get_ports {clk}]
set_property -dict {PACKAGE_PIN R14 IOSTANDARD LVCMOS33} [get_ports {led[0]}]
set_property -dict {PACKAGE_PIN P14 IOSTANDARD LVCMOS33} [get_ports {led[1]}]
set_property -dict {PACKAGE_PIN N16 IOSTANDARD LVCMOS33} [get_ports {led[2]}]
set_property -dict {PACKAGE_PIN M14 IOSTANDARD LVCMOS33} [get_ports {led[3]}]
set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports {btn0}]

# Design-specific exceptions (not copied from Master XDC): btn0 feeds only
# the reset synchronizer's asynchronous preset inputs. Its release is synced.
# LEDs drive human-visible indicators, not a clocked external receiver.
# Internal register-to-register setup/hold paths remain timed at 125 MHz.
set_false_path -from [get_ports {btn0}]
set_false_path -to [get_ports {led[*]}]
