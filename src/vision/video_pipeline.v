`timescale 1ns/1ps
// HDMI IP 的并行 RGB 边界：显示保留原始同步波形，分析使用内部单拍标记。
// 此模块不实现 TMDS 电气收发，物理前端需独立集成 dvi2rgb/rgb2dvi。
module video_pipeline #(
    parameter SW=1280,SH=720,DW=224,DH=224,NLINES=8,VS_POL=1'b1
)(
    input wire pclk,s_axi_aclk,rst_n,
    input wire raw_vs,raw_hs,raw_de,
    input wire [23:0] raw_rgb,
    input wire awvalid,wvalid,bready,arvalid,rready,
    input wire [6:0] awaddr,araddr,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    output wire awready,wready,bvalid,arready,rvalid,
    output wire [1:0] bresp,rresp,
    output wire [31:0] rdata,
    output reg video_vs,video_hs,video_de,
    output reg [23:0] video_rgb,
    input wire cop_ready,
    output wire cop_vs,cop_hs,cop_de,
    output wire [7:0] cop_y,
    output wire [31:0] display_frame_id,active_config_id,cop_frame_id,cop_config_id,snapshot_drop_count
);
    wire normalized_vs,normalized_hs,normalized_de,pixel_reset;
    wire [23:0] normalized_rgb;
    reg seen_frame;
    reset_sync u_reset(.clk(pclk),.arst_n(rst_n),.rst_n(pixel_reset));
    in_align #(.VS_POL(VS_POL)) u_align(.clk(pclk),.rst_n(pixel_reset),
        .in_vs(raw_vs),.in_hs(raw_hs),.in_de(raw_de),.in_rgb(raw_rgb),
        .out_vs(normalized_vs),.out_hs(normalized_hs),.out_de(normalized_de),.out_rgb(normalized_rgb));
    always @(posedge pclk or negedge pixel_reset)
        if(!pixel_reset) seen_frame<=0;
        else if(normalized_vs) seen_frame<=1;
    always @(posedge pclk or negedge pixel_reset) begin
        if(!pixel_reset) begin video_vs<=0;video_hs<=0;video_de<=0;video_rgb<=0;end
        else begin video_vs<=raw_vs;video_hs<=raw_hs;video_de<=raw_de;video_rgb<=raw_rgb;end
    end
    vision_top #(.SW(SW),.SH(SH),.DW(DW),.DH(DH),.NLINES(NLINES)) u_vision(
        .clk(pclk),.s_axi_aclk(s_axi_aclk),.rst_n(rst_n),
        .in_vs(normalized_vs),.in_hs(normalized_hs && seen_frame),.in_de(normalized_de && seen_frame),.in_rgb(normalized_rgb),
        .awvalid(awvalid),.awready(awready),.awaddr(awaddr),.wvalid(wvalid),.wready(wready),
        .wdata(wdata),.wstrb(wstrb),.bvalid(bvalid),.bready(bready),.bresp(bresp),
        .arvalid(arvalid),.arready(arready),.araddr(araddr),.rvalid(rvalid),.rready(rready),.rdata(rdata),.rresp(rresp),
        .cop_ready(cop_ready),.cop_vs(cop_vs),.cop_hs(cop_hs),.cop_de(cop_de),.cop_y(cop_y),
        .display_frame_id(display_frame_id),.active_config_id(active_config_id),
        .cop_frame_id(cop_frame_id),.cop_config_id(cop_config_id),.snapshot_drop_count(snapshot_drop_count));
endmodule
