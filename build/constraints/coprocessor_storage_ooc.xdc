# Storage clock follows the selected coprocessor profile; default is the 40 MHz safe profile.
if {![info exists cop_period]} {set cop_period 25.000}
create_clock -name clk -period $cop_period [get_ports clk]
