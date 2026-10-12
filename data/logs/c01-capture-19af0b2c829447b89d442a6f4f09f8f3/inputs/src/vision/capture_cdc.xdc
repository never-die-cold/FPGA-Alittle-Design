# Only first-stage single-bit synchronizer inputs; no whole-clock exception.
set capture_first [get_pins -hier -regexp {.*capture_status.*/(lock_sync_reg\[0\]|fault_bridge/(ack_sync_reg\[0\]|pending_sync_reg\[0\]))/D}]
set_false_path -to $capture_first
