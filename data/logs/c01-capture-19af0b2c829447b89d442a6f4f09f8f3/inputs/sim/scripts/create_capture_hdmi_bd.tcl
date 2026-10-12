# Add a raw-frame capture branch to the existing direct HDMI display design.
# Called from a fresh project; never opens a hardware target.
source sim/scripts/create_hdmi_bd.tcl
set_property -dict [list CONFIG.PCW_USE_S_AXI_HP0 1 CONFIG.PCW_S_AXI_HP0_DATA_WIDTH 64 \
    CONFIG.PCW_USE_S_AXI_HP1 0 CONFIG.PCW_USE_S_AXI_HP2 0 CONFIG.PCW_USE_S_AXI_HP3 0 \
    CONFIG.PCW_USE_FABRIC_INTERRUPT 1 CONFIG.PCW_USE_S_AXI_GP1 0] $ps
disconnect_bd_intf_net [get_bd_intf_nets -of_objects [get_bd_intf_pins pipe/s_axi]] [get_bd_intf_pins pipe/s_axi]
set control [ip capture_control xilinx.com:ip:axi_interconnect:2.1]
set_property CONFIG.NUM_MI 3 $control
connect_bd_intf_net [get_bd_intf_pins converter/M_AXI] [get_bd_intf_pins capture_control/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins capture_control/M00_AXI] [get_bd_intf_pins pipe/s_axi]
set status [create_bd_cell -type module -reference capture_status_axi capture_status]
set dma [ip capture_dma xilinx.com:ip:axi_vdma:6.3]
set_property -dict [list CONFIG.c_include_mm2s 0 CONFIG.c_include_s2mm 1 \
    CONFIG.c_num_fstores 4 CONFIG.c_m_axi_s2mm_data_width 64 CONFIG.c_include_s2mm_dre 1 \
    CONFIG.c_include_internal_genlock 0 CONFIG.c_use_s2mm_fsync 2] $dma
set vin [ip capture_input xilinx.com:ip:v_vid_in_axi4s:5.0]
set_property -dict [list CONFIG.C_HAS_ASYNC_CLK 1 CONFIG.C_M_AXIS_VIDEO_FORMAT 2 \
    CONFIG.C_NATIVE_COMPONENT_WIDTH 8 CONFIG.C_M_AXIS_VIDEO_DATA_WIDTH 8 \
    CONFIG.C_PIXELS_PER_CLOCK 1 CONFIG.C_ADDR_WIDTH 10] $vin
set memory [ip capture_memory xilinx.com:ip:axi_protocol_converter:2.1]
set_property -dict [list CONFIG.SI_PROTOCOL AXI4 CONFIG.MI_PROTOCOL AXI3] $memory
foreach {a b} {capture_control/M01_AXI capture_status/s_axi \
    capture_control/M02_AXI capture_dma/S_AXI_LITE capture_input/video_out capture_dma/S_AXIS_S2MM \
    capture_dma/M_AXI_S2MM capture_memory/S_AXI capture_memory/M_AXI ps7/S_AXI_HP0} {
    connect_bd_intf_net [get_bd_intf_pins $a] [get_bd_intf_pins $b]
}
set reset [ip capture_reset xilinx.com:ip:proc_sys_reset:5.0]
set low [ip capture_low xilinx.com:ip:xlconstant:1.1]
set_property CONFIG.CONST_VAL 0 $low
net ps7/FCLK_CLK0 ps7/S_AXI_HP0_ACLK capture_reset/slowest_sync_clk \
    capture_control/ACLK capture_control/S00_ACLK capture_control/M00_ACLK \
    capture_control/M01_ACLK capture_control/M02_ACLK capture_status/s_axi_aclk \
    capture_memory/aclk capture_dma/s_axi_lite_aclk capture_dma/m_axi_s2mm_aclk \
    capture_dma/s_axis_s2mm_aclk capture_input/aclk
net ps7/FCLK_RESET0_N capture_reset/ext_reset_in
foreach pin {pipe/s_axi_aresetn converter/aresetn} {
    disconnect_bd_net [get_bd_nets -of_objects [get_bd_pins $pin]] [get_bd_pins $pin]
}
net high/dout capture_reset/dcm_locked capture_input/aclken capture_input/axis_enable capture_input/vid_io_in_ce
net capture_low/dout capture_reset/aux_reset_in capture_reset/mb_debug_sys_rst \
    capture_input/vid_field_id capture_input/vid_hblank capture_input/vid_vblank
net capture_reset/peripheral_aresetn capture_control/ARESETN capture_control/S00_ARESETN \
    capture_control/M00_ARESETN capture_control/M01_ARESETN capture_control/M02_ARESETN \
    capture_memory/aresetn capture_dma/axi_resetn capture_input/aresetn \
    pipe/s_axi_aresetn converter/aresetn capture_status/s_axi_aresetn
net rx/PixelClk capture_status/pclk capture_input/vid_io_in_clk
net rx/pLocked capture_status/video_locked
net rx/vid_pData capture_status/raw_rbg
net capture_status/native_rgb capture_input/vid_data
net capture_status/pixel_reset capture_input/vid_io_in_reset
net rx/vid_pVDE capture_input/vid_active_video
net rx/vid_pHSync capture_input/vid_hsync
net rx/vid_pVSync capture_input/vid_vsync
net capture_input/overflow capture_status/pixel_overflow
connect_bd_intf_net [get_bd_intf_pins capture_input/video_out] [get_bd_intf_pins capture_status/stream]
set interrupt [ip capture_interrupt xilinx.com:ip:xlconcat:2.1]
set_property -dict [list CONFIG.NUM_PORTS 2 CONFIG.IN0_WIDTH 1 CONFIG.IN1_WIDTH 15] $interrupt
set padding [ip capture_padding xilinx.com:ip:xlconstant:1.1]
set_property -dict [list CONFIG.CONST_WIDTH 15 CONFIG.CONST_VAL 0] $padding
net capture_dma/s2mm_introut capture_interrupt/In0
net capture_padding/dout capture_interrupt/In1
net capture_interrupt/dout ps7/IRQ_F2P
assign_bd_address -offset 0x40000000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs pipe/s_axi/reg0] -force
assign_bd_address -offset 0x42000000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs capture_status/s_axi/reg0]
assign_bd_address -offset 0x43000000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs capture_dma/S_AXI_LITE/Reg]
assign_bd_address
validate_bd_design
save_bd_design
set stream_bits [expr {[get_property LEFT [get_bd_pins capture_dma/s_axis_s2mm_tdata]]+1}]
if {$stream_bits != 24 || [get_property CONFIG.c_num_fstores $dma] != 4 || \
    [get_property CONFIG.c_include_mm2s $dma] != 0 || [get_property CONFIG.C_EXT_RESET_HIGH $reset] != 0} {
    error "capture contract readback failed"
}
puts "PASS: HDMI display plus C01 capture/status integrated BD; stream=$stream_bits HP0=64 stores=4"
