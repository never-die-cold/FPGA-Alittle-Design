open_checkpoint [file join [pwd] build/run/pynq_cop_40mhz/project/pynq_cop_40mhz.runs/impl_1/cop_system_wrapper_routed.dcp]
foreach p {*u_config/hold_data_reg* *u_config/hold_id_reg* *u_config/dst_data_reg* *u_config/hold_data* *u_config/*data_reg*} {
  set hit [get_cells -hier -filter "NAME =~ $p"]
  puts "PAT $p N=[llength $hit]"
  foreach c [lrange $hit 0 3] { puts "   [get_property NAME $c]" }
}
exit