# Extend cop_system with the existing HDMI display and C01 raw capture path.
# COP/DMA/GPIO addresses stay unchanged; capture uses independent PS HP1.
set_property -dict [list CONFIG.PCW_EN_CLK2_PORT 1 CONFIG.PCW_USE_S_AXI_HP1 1 \
    CONFIG.PCW_S_AXI_HP1_DATA_WIDTH 64] $ps
set_property CONFIG.NUM_MI 6 [get_bd_cells control_ic]
set rx [cop_ip rx digilentinc.com:ip:dvi2rgb:2.0]
set_property -dict [list CONFIG.kRstActiveHigh false CONFIG.kClkRange 2 \
    CONFIG.kAddBUFG true CONFIG.kDebug false CONFIG.kEnableSerialClkOutput false \
    CONFIG.kEdidFileName dgl_720p_cea.data] $rx
set tx [cop_ip tx digilentinc.com:ip:rgb2dvi:1.4]
set_property -dict [list CONFIG.kRstActiveHigh false CONFIG.kClkRange 2 \
    CONFIG.kGenerateSerialClk true CONFIG.kClkPrimitive MMCM] $tx
cop_ext_intf rx/TMDS hdmi_in
cop_ext_intf rx/DDC hdmi_in_ddc
cop_ext_intf tx/TMDS hdmi_out
set pipe [create_bd_cell -type module -reference vision_axi pipe]
connect_bd_intf_net [get_bd_intf_pins control_ic/M03_AXI] [get_bd_intf_pins pipe/s_axi]
cop_net ps7/FCLK_CLK0 pipe/s_axi_aclk
cop_net ps7/FCLK_RESET0_N pipe/s_axi_aresetn rx/aRst_n
cop_net ps7/FCLK_CLK2 rx/RefClk
cop_net rx/PixelClk pipe/pclk tx/PixelClk
cop_net rx/pLocked pipe/video_locked tx/aRst_n
foreach {a b} {vid_pData raw_rbg vid_pVDE raw_de vid_pHSync raw_hs vid_pVSync raw_vs} {
    cop_net rx/$a pipe/$b
}
foreach {a b} {vid_pData video_rbg vid_pVDE video_de vid_pHSync video_hs vid_pVSync video_vs} {
    cop_net tx/$a pipe/$b
}
set high [cop_ip high xilinx.com:ip:xlconstant:1.1]
set low [cop_ip capture_low xilinx.com:ip:xlconstant:1.1]
set_property CONFIG.CONST_VAL 0 $low
cop_net high/dout rx/pRst_n
foreach name {hdmi_in_hpd hdmi_out_hpd} {
    create_bd_port -dir O -from 0 -to 0 $name
    connect_bd_net [get_bd_pins high/dout] [get_bd_ports $name]
}
set status [create_bd_cell -type module -reference capture_status_axi capture_status]
set vdma [cop_ip capture_dma xilinx.com:ip:axi_vdma:6.3]
set_property -dict [list CONFIG.c_include_mm2s 0 CONFIG.c_include_s2mm 1 \
    CONFIG.c_num_fstores 4 CONFIG.c_m_axi_s2mm_data_width 64 CONFIG.c_include_s2mm_dre 1 \
    CONFIG.c_include_internal_genlock 0 CONFIG.c_use_s2mm_fsync 2] $vdma
set vin [cop_ip capture_input xilinx.com:ip:v_vid_in_axi4s:5.0]
set_property -dict [list CONFIG.C_HAS_ASYNC_CLK 1 CONFIG.C_M_AXIS_VIDEO_FORMAT 2 \
    CONFIG.C_NATIVE_COMPONENT_WIDTH 8 CONFIG.C_M_AXIS_VIDEO_DATA_WIDTH 8 \
    CONFIG.C_PIXELS_PER_CLOCK 1 CONFIG.C_ADDR_WIDTH 10] $vin
set vmem [cop_ip capture_memory xilinx.com:ip:axi_protocol_converter:2.1]
set_property -dict [list CONFIG.SI_PROTOCOL AXI4 CONFIG.MI_PROTOCOL AXI3] $vmem
foreach {a b} {control_ic/M04_AXI capture_status/s_axi control_ic/M05_AXI capture_dma/S_AXI_LITE \
    capture_input/video_out capture_dma/S_AXIS_S2MM capture_dma/M_AXI_S2MM capture_memory/S_AXI \
    capture_memory/M_AXI ps7/S_AXI_HP1} {
    connect_bd_intf_net [get_bd_intf_pins $a] [get_bd_intf_pins $b]
}
set vreset [cop_ip capture_reset xilinx.com:ip:proc_sys_reset:5.0]
cop_net ps7/FCLK_CLK0 ps7/S_AXI_HP1_ACLK capture_reset/slowest_sync_clk \
    capture_status/s_axi_aclk capture_memory/aclk capture_dma/s_axi_lite_aclk \
    capture_dma/m_axi_s2mm_aclk capture_dma/s_axis_s2mm_aclk capture_input/aclk
cop_net ps7/FCLK_RESET0_N capture_reset/ext_reset_in
cop_net high/dout capture_reset/aux_reset_in capture_reset/dcm_locked capture_input/aclken \
    capture_input/axis_enable capture_input/vid_io_in_ce
cop_net capture_low/dout capture_reset/mb_debug_sys_rst capture_input/vid_field_id \
    capture_input/vid_hblank capture_input/vid_vblank
cop_net capture_reset/peripheral_aresetn capture_memory/aresetn capture_dma/axi_resetn \
    capture_input/aresetn capture_status/s_axi_aresetn
foreach index {03 04 05} {
    cop_net ps7/FCLK_CLK0 control_ic/M${index}_ACLK
    cop_net ps7/FCLK_RESET0_N control_ic/M${index}_ARESETN
}
cop_net rx/PixelClk capture_status/pclk capture_input/vid_io_in_clk
cop_net rx/pLocked capture_status/video_locked
cop_net rx/vid_pData capture_status/raw_rbg
cop_net capture_status/native_rgb capture_input/vid_data
cop_net capture_status/pixel_reset capture_input/vid_io_in_reset
cop_net rx/vid_pVDE capture_input/vid_active_video
cop_net rx/vid_pHSync capture_input/vid_hsync
cop_net rx/vid_pVSync capture_input/vid_vsync
cop_net capture_input/overflow capture_status/pixel_overflow
connect_bd_intf_net [get_bd_intf_pins capture_input/video_out] [get_bd_intf_pins capture_status/stream]
foreach {segment base} {pipe/s_axi/reg0 0x41000000 capture_status/s_axi/reg0 0x42000000 \
    capture_dma/S_AXI_LITE/Reg 0x43000000} {
    assign_bd_address -offset $base -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] \
        [get_bd_addr_segs $segment]
}
assign_bd_address
save_bd_design
puts "VIDEO ATTACHED: display + CAP1 + VDMA HP1; vision=41000000 CAP=42000000 VDMA=43000000"
