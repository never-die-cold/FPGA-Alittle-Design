# Board integration clock contract: matches pynq_z2_top.CORE_CLK_DIVIDE (default 25 => 40 MHz).
if {![info exists core_clk_divide]} {set core_clk_divide 25}
if {$core_clk_divide != 25 && $core_clk_divide != 10} {
    error "Unsupported coprocessor board divider: $core_clk_divide (25=40 MHz, 10=100 MHz)"
}
set cop_board_clock_name cop_clk_[expr {$core_clk_divide == 25 ? 40 : 100}]
create_generated_clock -name $cop_board_clock_name -source [get_pins {u_mmcm/CLKIN1}] \
    -multiply_by 8 -divide_by $core_clk_divide [get_pins {u_mmcm/CLKOUT0}]
