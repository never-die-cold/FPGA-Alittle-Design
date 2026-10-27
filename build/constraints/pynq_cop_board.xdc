# PYNQ-Z2 PL-only pins; PS DDR/FIXED_IO are supplied by the processing_system7 preset.
set_property -dict {PACKAGE_PIN R14 IOSTANDARD LVCMOS33} [get_ports {led[0]}]
set_property -dict {PACKAGE_PIN P14 IOSTANDARD LVCMOS33} [get_ports {led[1]}]
set_property -dict {PACKAGE_PIN N16 IOSTANDARD LVCMOS33} [get_ports {led[2]}]
set_property -dict {PACKAGE_PIN M14 IOSTANDARD LVCMOS33} [get_ports {led[3]}]
set_false_path -to [get_ports {led[*]}]

# CDC checks/constraints run from pynq_cop_cdc.tcl after opt_design. A blanket
# asynchronous clock group would override the held-payload max-delay bounds.
