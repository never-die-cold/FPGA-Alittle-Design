# Project caller has loaded RTL and the pinned Digilent IP repository.
create_bd_design vision
proc ip {name vlnv} { return [create_bd_cell -type ip -vlnv $vlnv $name] }
proc net {args} {
    set pins {}
    foreach name $args { lappend pins [get_bd_pins $name] }
    connect_bd_net {*}$pins
}
proc external_intf {pin name} {
    make_bd_intf_pins_external [get_bd_intf_pins $pin]
    set port [get_bd_intf_ports [file tail $pin]_0]
    set_property name $name $port
}
set ps [ip ps7 xilinx.com:ip:processing_system7:5.5]
source sim/build/hdmi-source/ps7_config.tcl
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP1 0 CONFIG.PCW_USE_S_AXI_GP0 0 \
    CONFIG.PCW_USE_S_AXI_HP0 0 CONFIG.PCW_USE_S_AXI_HP2 0 \
    CONFIG.PCW_USE_FABRIC_INTERRUPT 0 CONFIG.PCW_EN_EMIO_GPIO 0 \
    CONFIG.PCW_GPIO_EMIO_GPIO_ENABLE 0 CONFIG.PCW_I2C1_PERIPHERAL_ENABLE 0] $ps
external_intf ps7/DDR DDR
external_intf ps7/FIXED_IO FIXED_IO
set rx [ip rx digilentinc.com:ip:dvi2rgb:2.0]
set_property -dict [list CONFIG.kRstActiveHigh false CONFIG.kClkRange 2 \
    CONFIG.kAddBUFG true CONFIG.kDebug false CONFIG.kEnableSerialClkOutput false \
    CONFIG.kEdidFileName dgl_720p_cea.data] $rx
set tx [ip tx digilentinc.com:ip:rgb2dvi:1.4]
set_property -dict [list CONFIG.kRstActiveHigh false CONFIG.kClkRange 2 \
    CONFIG.kGenerateSerialClk true CONFIG.kClkPrimitive MMCM] $tx
external_intf rx/TMDS hdmi_in
external_intf rx/DDC hdmi_in_ddc
external_intf tx/TMDS hdmi_out
set pipe [create_bd_cell -type module -reference vision_axi pipe]
set conv [ip converter xilinx.com:ip:axi_protocol_converter:2.1]
set_property -dict [list CONFIG.SI_PROTOCOL AXI3 CONFIG.MI_PROTOCOL AXI4LITE] $conv
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins converter/S_AXI]
connect_bd_intf_net [get_bd_intf_pins converter/M_AXI] [get_bd_intf_pins pipe/s_axi]
net ps7/FCLK_CLK0 ps7/M_AXI_GP0_ACLK converter/aclk pipe/s_axi_aclk
net ps7/FCLK_RESET0_N converter/aresetn pipe/s_axi_aresetn rx/aRst_n
net ps7/FCLK_CLK2 rx/RefClk
net rx/PixelClk pipe/pclk tx/PixelClk
net rx/pLocked pipe/video_locked tx/aRst_n
foreach {rx_pin pipe_pin} {vid_pData raw_rbg vid_pVDE raw_de vid_pHSync raw_hs vid_pVSync raw_vs} {
    net rx/$rx_pin pipe/$pipe_pin
}
foreach {tx_pin pipe_pin} {vid_pData video_rbg vid_pVDE video_de vid_pHSync video_hs vid_pVSync video_vs} {
    net tx/$tx_pin pipe/$pipe_pin
}
set high [ip high xilinx.com:ip:xlconstant:1.1]
net high/dout rx/pRst_n
foreach name {hdmi_in_hpd hdmi_out_hpd} {
    create_bd_port -dir O -from 0 -to 0 $name
    connect_bd_net [get_bd_pins high/dout] [get_bd_ports $name]
}
set ila [ip snapshot_ila xilinx.com:ip:ila:6.2]
set_property -dict [list CONFIG.C_MONITOR_TYPE Native CONFIG.C_NUM_OF_PROBES 1 \
    CONFIG.C_PROBE0_WIDTH 107 CONFIG.C_DATA_DEPTH 1024] $ila
net rx/PixelClk snapshot_ila/clk
net pipe/snapshot_debug snapshot_ila/probe0
assign_bd_address -offset 0x40000000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs pipe/s_axi/reg0]
validate_bd_design
save_bd_design
