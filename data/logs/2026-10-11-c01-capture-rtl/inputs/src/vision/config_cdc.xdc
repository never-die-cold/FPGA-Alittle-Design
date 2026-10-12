# Stable bundled-data handshake; no whole-clock asynchronous exception.
set first_sync [get_pins -hier -filter {NAME =~ *req_meta_reg/D || NAME =~ *ack_meta_reg/D}]
if {[llength $first_sync] != 2} {error "expected two config handshake first-stage inputs"}
set_false_path -to $first_sync
set bundle_from [get_cells -hier -filter {NAME =~ *u_config/hold_data_reg* || NAME =~ *u_config/hold_id_reg*}]
set bundle_to [get_cells -hier -filter {NAME =~ *u_config/dst_data_reg* || NAME =~ *u_config/dst_id_reg*}]
if {![llength $bundle_from] || ![llength $bundle_to]} {error "missing config bundle"}
set_max_delay -datapath_only 10.0 -from $bundle_from -to $bundle_to
# Only asynchronous assertion into first reset-release stages is exempted.
set_false_path -to [get_pins -hier -filter {NAME =~ *release_pipe_reg*/CLR}]
