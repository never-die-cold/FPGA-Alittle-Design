# Storage clock follows the selected coprocessor profile; default is the 40 MHz safe profile.
create_clock -name clk -period $cop_period [get_ports clk]
