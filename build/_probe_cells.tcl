open_checkpoint [file join [pwd] build/run/pynq_cop_40mhz/project/pynq_cop_40mhz.runs/impl_1/cop_system_wrapper_routed.dcp]
puts "CONFIG_CELLS=[llength [get_cells -hier -filter {NAME =~ *u_config*}]]"
foreach c [lrange [get_cells -hier -filter {NAME =~ *u_config*}] 0 7] { puts "CELL [get_property NAME $c]" }
puts "HOLD=[llength [get_cells -hier -filter {NAME =~ *hold_data*}]]"
exit