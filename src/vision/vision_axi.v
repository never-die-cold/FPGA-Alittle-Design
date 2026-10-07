`timescale 1ns/1ps
// Vivado AXI-Lite wrapper; Digilent video byte order is R,B,G, internal is R,G,B.
// 复位拓扑：像素域 rst_n 并入 video_locked（断源即复位视频通路）；AXI 域 axi_rst_n
// 只随 s_axi_aresetn——锁定丢失时在途 AXI 响应照常完成，已提交配置保留
// （2026-10-03 上板实测：video_locked 波及 AXI 从机会挂死 PS 总线）。
module vision_axi #(parameter ENABLE_DIAGNOSTIC=0,H_TOTAL=1650)(
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 s_axi_aclk CLK",
       X_INTERFACE_PARAMETER="ASSOCIATED_BUSIF s_axi, ASSOCIATED_RESET s_axi_aresetn" *)
    input wire s_axi_aclk,
    (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 s_axi_aresetn RST",
       X_INTERFACE_PARAMETER="POLARITY ACTIVE_LOW" *)
    input wire s_axi_aresetn,
    input wire pclk,video_locked,
    input wire raw_vs,raw_hs,raw_de,
    input wire [23:0] raw_rbg,
    output wire video_vs,video_hs,video_de,
    output wire [23:0] video_rbg,
    input wire [31:0] s_axi_awaddr,s_axi_araddr,
    input wire [2:0] s_axi_awprot,s_axi_arprot,
    input wire s_axi_awvalid,s_axi_wvalid,s_axi_bready,s_axi_arvalid,s_axi_rready,
    input wire [31:0] s_axi_wdata,
    input wire [3:0] s_axi_wstrb,
    output wire s_axi_awready,s_axi_wready,s_axi_bvalid,s_axi_arready,s_axi_rvalid,
    output wire [1:0] s_axi_bresp,s_axi_rresp,
    output wire [31:0] s_axi_rdata,
    output wire [106:0] snapshot_debug
);
    wire [23:0] rgb;
    wire cop_vs,cop_hs,cop_de;
    wire [7:0] cop_y;
    wire [31:0] frame_id,config_id,drops;
    assign video_rbg={rgb[23:16],rgb[7:0],rgb[15:8]};
    assign snapshot_debug={drops,config_id,frame_id,cop_vs,cop_hs,cop_de,cop_y};
    video_pipeline #(.ENABLE_DIAGNOSTIC(ENABLE_DIAGNOSTIC),.H_TOTAL(H_TOTAL)) u_pipeline(.pclk(pclk),.s_axi_aclk(s_axi_aclk),
        .rst_n(s_axi_aresetn && video_locked),.axi_rst_n(s_axi_aresetn),
        .raw_vs(raw_vs),.raw_hs(raw_hs),.raw_de(raw_de),
        .raw_rgb({raw_rbg[23:16],raw_rbg[7:0],raw_rbg[15:8]}),
        .video_vs(video_vs),.video_hs(video_hs),.video_de(video_de),.video_rgb(rgb),
        .awaddr(|s_axi_awaddr[15:7] ? 7'h40 : s_axi_awaddr[6:0]),
        .araddr(|s_axi_araddr[15:7] ? 7'h40 : s_axi_araddr[6:0]),
        .awvalid(s_axi_awvalid),.wvalid(s_axi_wvalid),.bready(s_axi_bready),
        .arvalid(s_axi_arvalid),.rready(s_axi_rready),
        .wdata(s_axi_wdata),.wstrb(s_axi_wstrb),
        .awready(s_axi_awready),.wready(s_axi_wready),.bvalid(s_axi_bvalid),
        .arready(s_axi_arready),.rvalid(s_axi_rvalid),
        .bresp(s_axi_bresp),.rresp(s_axi_rresp),.rdata(s_axi_rdata),
        .cop_ready(1'b1),.cop_vs(cop_vs),.cop_hs(cop_hs),.cop_de(cop_de),.cop_y(cop_y),
        .cop_frame_id(frame_id),.cop_config_id(config_id),.snapshot_drop_count(drops));
endmodule
