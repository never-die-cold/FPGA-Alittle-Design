# Period variables come from build_coprocessor_gate.tcl; defaults are the 40 MHz safe profile.
create_clock -name core_clk -period $core_period [get_ports core_clk]
create_clock -name cop_clk -period $cop_period [get_ports cop_clk]
set_clock_groups -asynchronous -group [get_clocks core_clk] -group [get_clocks cop_clk]
