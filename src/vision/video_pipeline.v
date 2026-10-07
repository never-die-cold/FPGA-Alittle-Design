`timescale 1ns/1ps
// HDMI IP 的并行 RGB 边界：显示保留原始同步波形，分析使用内部单拍标记。
// 此模块不实现 TMDS 电气收发，物理前端需独立集成 dvi2rgb/rgb2dvi。
module video_pipeline #(
    parameter SW=1280,SH=720,DW=224,DH=224,NLINES=8,VS_POL=1'b1,
    parameter ENABLE_DIAGNOSTIC=0,H_TOTAL=1650
)(
    input wire pclk,s_axi_aclk,rst_n,axi_rst_n,
    input wire raw_vs,raw_hs,raw_de,
    input wire [23:0] raw_rgb,
    input wire awvalid,wvalid,bready,arvalid,rready,
    input wire [6:0] awaddr,araddr,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    output wire awready,wready,bvalid,arready,rvalid,
    output wire [1:0] bresp,rresp,
    output wire [31:0] rdata,
    output wire video_vs,video_hs,video_de,
    output wire [23:0] video_rgb,
    input wire cop_ready,
    output wire cop_vs,cop_hs,cop_de,
    output wire [7:0] cop_y,
    output wire [31:0] display_frame_id,active_config_id,cop_frame_id,cop_config_id,snapshot_drop_count
);
    wire normalized_vs,normalized_hs,normalized_de,pixel_reset;
    wire [23:0] normalized_rgb;
    wire processed_vs,processed_de,diagnostic_en;
    wire [7:0] processed_y;
    reg seen_frame;
    reset_sync u_reset(.clk(pclk),.arst_n(rst_n),.rst_n(pixel_reset));
    in_align #(.VS_POL(VS_POL)) u_align(.clk(pclk),.rst_n(pixel_reset),
        .in_vs(raw_vs),.in_hs(raw_hs),.in_de(raw_de),.in_rgb(raw_rgb),
        .out_vs(normalized_vs),.out_hs(normalized_hs),.out_de(normalized_de),.out_rgb(normalized_rgb));
    always @(posedge pclk or negedge pixel_reset)
        if(!pixel_reset) seen_frame<=0;
        else if(normalized_vs) seen_frame<=1;
    generate if(ENABLE_DIAGNOSTIC) begin: diagnostic
        diagnostic_display #(.WIDTH(SW),.H_TOTAL(H_TOTAL),.VS_POL(VS_POL)) u_display(
            .clk(pclk),.rst_n(pixel_reset),.raw_vs(raw_vs),.raw_hs(raw_hs),.raw_de(raw_de),.raw_rgb(raw_rgb),
            .diagnostic_en(diagnostic_en),.frame_epoch(display_frame_id[0]),
            .processed_vs(processed_vs),.processed_de(processed_de),.processed_y(processed_y),
            .video_vs(video_vs),.video_hs(video_hs),.video_de(video_de),.video_rgb(video_rgb));
    end else begin: legacy
        reg vs,hs,de;
        reg [23:0] rgb;
        always @(posedge pclk or negedge pixel_reset) begin
            if(!pixel_reset) begin vs<=0;hs<=0;de<=0;rgb<=0;end
            else begin vs<=raw_vs;hs<=raw_hs;de<=raw_de;rgb<=raw_rgb;end
        end
        assign video_vs=vs;assign video_hs=hs;assign video_de=de;assign video_rgb=rgb;
    end endgenerate
    vision_top #(.SW(SW),.SH(SH),.DW(DW),.DH(DH),.NLINES(NLINES)) u_vision(
        .clk(pclk),.s_axi_aclk(s_axi_aclk),.rst_n(rst_n),.axi_rst_n(axi_rst_n),
        .in_vs(normalized_vs),.in_hs(normalized_hs && seen_frame),.in_de(normalized_de && seen_frame),.in_rgb(normalized_rgb),
        .awvalid(awvalid),.awready(awready),.awaddr(awaddr),.wvalid(wvalid),.wready(wready),
        .wdata(wdata),.wstrb(wstrb),.bvalid(bvalid),.bready(bready),.bresp(bresp),
        .arvalid(arvalid),.arready(arready),.araddr(araddr),.rvalid(rvalid),.rready(rready),.rdata(rdata),.rresp(rresp),
        .cop_ready(cop_ready),.cop_vs(cop_vs),.cop_hs(cop_hs),.cop_de(cop_de),.cop_y(cop_y),
        .display_frame_id(display_frame_id),.active_config_id(active_config_id),
        .out_vs(processed_vs),.out_de(processed_de),.out_y(processed_y),.diagnostic_display_en(diagnostic_en),
        .cop_frame_id(cop_frame_id),.cop_config_id(cop_config_id),.snapshot_drop_count(snapshot_drop_count));
endmodule
