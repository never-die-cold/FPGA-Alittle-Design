`timescale 1ns/1ps
// vision_top —— 彩色显示、灰度分析和快照分流。
// display_* 原图 RGB 直通；out_* 为灰度诊断流，不能直接驱动物理 HDMI。
// 分析：rgb2gray → [gaussian] → [sobel] → [osd]；scaler 在 sobel 后分叉。
// 快照：scaler → cop_buf → cop_*；ready 仅授权整帧启动。
// R0: bit0 gauss / bit1 snapshot / bit2 OSD / bit3 Sobel / bit4 diagnostic display.
// R0..10 整组暂存，R11 提交，config_bridge 在帧首应用并确认 R12 配置编号。
// 请求/确认两级同步；在途配置总线保持不变。两时钟分别同步释放复位。
module vision_top #(
    parameter SW = 16,            // 源宽（= gaussian 行宽）
    parameter SH = 8,
    parameter DW = 32,            // 缩放目标宽
    parameter DH = 16,
    parameter NLINES = 16
)(
    input  wire       clk,          // pclk：像素流域
    input  wire       s_axi_aclk,   // AXI-Lite 配置域，允许与像素时钟异步
    input  wire       rst_n,        // 像素域复位（顶层可并入 video_locked）
    input  wire       axi_rst_n,    // AXI 域复位：仅 PS 复位，不得并入 video_locked——
                                  // 锁定丢失时在途 AXI 响应必须照常完成（2026-10-03 上板挂死）
    // 像素输入（解码后 RGB 流）
    input  wire       in_vs,
    input  wire       in_hs,
    input  wire       in_de,
    input  wire [23:0] in_rgb,
    // AXI-Lite（单时钟域）
    input  wire       awvalid,
    output wire       awready,
    input  wire [6:0] awaddr,
    input  wire       wvalid,
    output wire       wready,
    input  wire [31:0] wdata,
    input  wire [3:0]  wstrb,
    output wire       bvalid,
    input  wire       bready,
    output wire [1:0] bresp,
    input  wire       arvalid,
    output wire       arready,
    input  wire [6:0] araddr,
    output wire       rvalid,
    input  wire       rready,
    output wire [31:0] rdata,
    output wire [1:0]  rresp,
    // 处理输出（显示路径，全分辨率灰度流）
    output wire       out_vs,
    output wire       out_hs,
    output wire       out_de,
    output wire [7:0] out_y,
    // 快照输出（scaler 缩放流经乒乓帧缓冲，= 模块三 CNN 输入尺寸；R0 bit1 使能）
    input  wire       cop_ready,    // cop 消费侧反压（=1 允许下一帧回放；§7 占位接口）
    output wire       cop_vs,
    output wire       cop_hs,
    output wire       cop_de,
    output wire [7:0] cop_y,
    output reg display_vs,display_hs,display_de,
    output reg [23:0] display_rgb,
    output reg [31:0] display_frame_id,
    output wire [31:0] active_config_id,
    output wire [31:0] cop_frame_id,cop_config_id,snapshot_drop_count,
    output wire diagnostic_display_en
);
    wire [16*32-1:0] regs_flat;
    wire pixel_reset,axi_reset;
    reset_sync u_pixel_reset(.clk(clk),.arst_n(rst_n),.rst_n(pixel_reset));
    reset_sync u_axi_reset(.clk(s_axi_aclk),.arst_n(axi_rst_n),.rst_n(axi_reset));
    wire [351:0] active_cfg;
    wire cfg_commit,cfg_busy;
    wire [31:0] cfg_applied,cfg_id;
    // 桥与从机同属 AXI 域：锁定丢失不清请求/已应用配置，恢复后未确认提交在首帧生效。
    config_bridge u_config(.src_clk(s_axi_aclk),.dst_clk(clk),.rst_n(axi_rst_n),
        .src_commit(cfg_commit),.src_data(regs_flat[351:0]),.dst_frame(in_vs),
        .src_busy(cfg_busy),.src_applied(cfg_applied),.dst_data(active_cfg),.dst_id(cfg_id));
    axi_regs #(.NREG(16), .AW(7), .RESV_BASE(11),.ATOMIC_CONFIG(1)) u_regs (
        .clk(s_axi_aclk), .rst_n(axi_reset),
        .awvalid(awvalid), .awready(awready), .awaddr(awaddr),
        .wvalid(wvalid), .wready(wready), .wdata(wdata), .wstrb(wstrb),
        .bvalid(bvalid), .bready(bready), .bresp(bresp),
        .arvalid(arvalid), .arready(arready), .araddr(araddr),
        .rvalid(rvalid), .rready(rready), .rdata(rdata), .rresp(rresp),
        .regs_flat(regs_flat),.cfg_commit(cfg_commit),.cfg_busy(cfg_busy),.cfg_applied(cfg_applied)
    );
    assign active_config_id=cfg_id;
    assign diagnostic_display_en=active_cfg[4];
    // 彩色原图独立显示，分析开关/缩放/消费反压均不影响该路径。
    always @(posedge clk or negedge pixel_reset) begin
        if(!pixel_reset) begin
            display_vs<=0;display_hs<=0;display_de<=0;display_rgb<=0;display_frame_id<=0;
        end else begin
            display_vs<=in_vs;display_hs<=in_hs;display_de<=in_de;display_rgb<=in_rgb;
            if(in_vs) display_frame_id<=display_frame_id+1;
        end
    end
    wire gauss_en  = active_cfg[0];
    wire scaler_en = active_cfg[1];
    wire osd_en    = active_cfg[2];

    // ---- 级 0：RGB→灰度（恒接） ----
    wire       g0_vs, g0_hs, g0_de;
    wire [7:0] g0_y;
    rgb2gray u_gray (
        .clk(clk), .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_rgb(in_rgb),
        .out_vs(g0_vs), .out_hs(g0_hs), .out_de(g0_de), .out_y(g0_y)
    );

    // ---- 级 1：3×3 高斯 ----
    wire       g1_vs, g1_hs, g1_de;
    wire [7:0] g1_y;
    gaussian_3x3 #(.WIDTH(SW), .HEIGHT(SH)) u_gauss (
        .clk(clk), .rst_n(pixel_reset),
        .in_vs(g0_vs), .in_hs(g0_hs), .in_de(g0_de), .in_y(g0_y),
        .out_vs(g1_vs), .out_hs(g1_hs), .out_de(g1_de), .out_g(g1_y)
    );

    // ---- 拓扑锁存（帧首；帧内恒定） ----
    // bridge 已在帧首整体锁存；这里再锁存会错误地多延迟一帧。
    wire t_gauss=gauss_en,t_scaler=scaler_en,t_osd=osd_en,t_sobel=active_cfg[3];

    // ---- mux 1：高斯旁路 ----
    wire       m1_vs = t_gauss  ? g1_vs : g0_vs;
    wire       m1_hs = t_gauss  ? g1_hs : g0_hs;
    wire       m1_de = t_gauss  ? g1_de : g0_de;
    wire [7:0] m1_y  = t_gauss  ? g1_y  : g0_y;

    // ---- 级 1b：Sobel 边缘（窗口装配/冲刷与 gaussian 同构，3 拍延迟） ----
    wire       e_vs, e_hs, e_de;
    wire [7:0] e_y;
    sobel #(.WIDTH(SW), .HEIGHT(SH)) u_sobel (
        .clk(clk), .rst_n(pixel_reset),
        .in_vs(m1_vs), .in_hs(m1_hs), .in_de(m1_de), .in_y(m1_y),
        .out_vs(e_vs), .out_hs(e_hs), .out_de(e_de), .out_g(e_y)
    );

    // ---- mux 1b：sobel 旁路 ----
    wire       m1b_vs = t_sobel ? e_vs  : m1_vs;
    wire       m1b_hs = t_sobel ? e_hs  : m1_hs;
    wire       m1b_de = t_sobel ? e_de  : m1_de;
    wire [7:0] m1b_y  = t_sobel ? e_y   : m1_y;

    // ---- mux 2 → 快照分支：scaler 缩放（R0 bit1 使能输出；不回显示路径） ----
    wire       s_vs, s_hs, s_de;
    wire [7:0] s_y;
    scaler #(.SW(SW), .SH(SH), .DW(DW), .DH(DH), .NLINES(NLINES)) u_scaler (
        .clk(clk), .rst_n(pixel_reset),
        .in_vs(m1b_vs), .in_hs(m1b_hs), .in_de(m1b_de), .in_y(m1b_y),
        .out_vs(s_vs), .out_hs(s_hs), .out_de(s_de), .out_y(s_y)
    );
    // 快照流帧首锁存门控后落乒乓帧缓冲（§7：乒乓行组缓冲占位实现，cop 契约定稿换封装）
    wire       cw_vs = t_scaler ? s_vs : 1'b0;
    wire       cw_hs = t_scaler ? s_hs : 1'b0;
    wire       cw_de = t_scaler ? s_de : 1'b0;
    cop_buf #(.DW(DW), .DH(DH)) u_copbuf (
        .clk(clk), .rst_n(pixel_reset),
        .in_vs(cw_vs), .in_hs(cw_hs), .in_de(cw_de), .in_y(s_y),
        .cop_ready(cop_ready),
        .out_vs(cop_vs), .out_hs(cop_hs), .out_de(cop_de), .out_y(cop_y),
        .frame_done(), .buf_full(),
        .in_frame_id(display_frame_id),.in_config_id(cfg_id),
        .out_frame_id(cop_frame_id),.out_config_id(cop_config_id),.drop_count(snapshot_drop_count)
    );

    // ---- 级 3：OSD 叠加（框参数 = R1..R10，坐标系 = 全分辨率显示图） ----
    wire       o_vs, o_hs, o_de;
    wire [7:0] o_y;
    osd_overlay u_osd (
        .clk(clk), .rst_n(pixel_reset),
        .in_vs(m1b_vs), .in_hs(m1b_hs), .in_de(m1b_de), .in_y(m1b_y),
        .box_x0(active_cfg[1*32 +: 16]), .box_y0(active_cfg[2*32 +: 16]),
        .box_x1(active_cfg[3*32 +: 16]), .box_y1(active_cfg[4*32 +: 16]),
        .box_color(active_cfg[5*32 +: 8]),
        .roi_x0(active_cfg[6*32 +: 16]), .roi_y0(active_cfg[7*32 +: 16]),
        .roi_x1(active_cfg[8*32 +: 16]), .roi_y1(active_cfg[9*32 +: 16]),
        .roi_color(active_cfg[10*32 +: 8]),
        .out_vs(o_vs), .out_hs(o_hs), .out_de(o_de), .out_y(o_y)
    );

    // ---- mux 3：OSD 旁路 → 显示输出（全分辨率直通显示） ----
    assign out_vs = t_osd ? o_vs : m1b_vs;
    assign out_hs = t_osd ? o_hs : m1b_hs;
    assign out_de = t_osd ? o_de : m1b_de;
    assign out_y  = t_osd ? o_y  : m1b_y;
endmodule
