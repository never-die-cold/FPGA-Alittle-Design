`timescale 1ns/1ps
// vision_top —— 模块二流水线顶层（v0.1 骨架）
// 链路：rgb2gray（恒接）→ [gaussian] → [scaler] → [osd]，方括号为 R0 开关可控级。
// R0 位定义 v0.1：bit0 gauss_en / bit1 scaler_en / bit2 osd_en / bit3 sobel_en（预留，
//   sobel 接入位置待 10/5 评审：置于缩放后则参数需随输出尺寸走）。
// 拓扑切换语义：路径选择在输入帧首 in_vs 锁存，帧内恒定——直通与处理级延迟不同，
//   帧内切换会撕裂；每帧自洽（输出 vs/hs/de 由所选路径自产），帧间可变。
// HDMI 解码/编码不在本单元：输入为解码后的 RGB 像素流（ADV7611 选型 10/5 拍板，
//   design_v0.md §5），输出为处理后的灰度流；单时钟域（与 axi_regs 同）。
module vision_top #(
    parameter SW = 16,            // 源宽（= gaussian 行宽）
    parameter SH = 8,
    parameter DW = 32,            // 缩放目标宽
    parameter DH = 16,
    parameter NLINES = 16
)(
    input  wire       clk,
    input  wire       rst_n,
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
    // 处理输出（灰度流，尺寸随拓扑：无 scaler 为 SW×SH，有 scaler 为 DW×DH）
    output wire       out_vs,
    output wire       out_hs,
    output wire       out_de,
    output wire [7:0] out_y
);
    wire [16*32-1:0] regs_flat;
    axi_regs #(.NREG(16), .AW(7), .RESV_BASE(11)) u_regs (
        .clk(clk), .rst_n(rst_n),
        .awvalid(awvalid), .awready(awready), .awaddr(awaddr),
        .wvalid(wvalid), .wready(wready), .wdata(wdata), .wstrb(wstrb),
        .bvalid(bvalid), .bready(bready), .bresp(bresp),
        .arvalid(arvalid), .arready(arready), .araddr(araddr),
        .rvalid(rvalid), .rready(rready), .rdata(rdata), .rresp(rresp),
        .regs_flat(regs_flat)
    );
    wire [31:0] r0 = regs_flat[0*32 +: 32];
    wire gauss_en  = r0[0];
    wire scaler_en = r0[1];
    wire osd_en    = r0[2];

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
        .clk(clk), .rst_n(rst_n),
        .in_vs(g0_vs), .in_hs(g0_hs), .in_de(g0_de), .in_y(g0_y),
        .out_vs(g1_vs), .out_hs(g1_hs), .out_de(g1_de), .out_g(g1_y)
    );

    // ---- 拓扑锁存（帧首；帧内恒定） ----
    reg t_gauss, t_scaler, t_osd;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t_gauss <= 0; t_scaler <= 0; t_osd <= 0;
        end else if (in_vs) begin
            t_gauss  <= gauss_en;
            t_scaler <= scaler_en;
            t_osd    <= osd_en;
        end
    end

    // ---- mux 1：高斯旁路 ----
    wire       m1_vs = t_gauss  ? g1_vs : g0_vs;
    wire       m1_hs = t_gauss  ? g1_hs : g0_hs;
    wire       m1_de = t_gauss  ? g1_de : g0_de;
    wire [7:0] m1_y  = t_gauss  ? g1_y  : g0_y;

    // ---- 级 2：双线性缩放 ----
    wire       s_vs, s_hs, s_de;
    wire [7:0] s_y;
    scaler #(.SW(SW), .SH(SH), .DW(DW), .DH(DH), .NLINES(NLINES)) u_scaler (
        .clk(clk), .rst_n(rst_n),
        .in_vs(m1_vs), .in_hs(m1_hs), .in_de(m1_de), .in_y(m1_y),
        .out_vs(s_vs), .out_hs(s_hs), .out_de(s_de), .out_y(s_y)
    );

    // ---- mux 2：缩放旁路 ----
    wire       m2_vs = t_scaler ? s_vs : m1_vs;
    wire       m2_hs = t_scaler ? s_hs : m1_hs;
    wire       m2_de = t_scaler ? s_de : m1_de;
    wire [7:0] m2_y  = t_scaler ? s_y  : m1_y;

    // ---- 级 3：OSD 叠加（框参数 = R1..R10，输出图坐标系） ----
    wire       o_vs, o_hs, o_de;
    wire [7:0] o_y;
    osd_overlay u_osd (
        .clk(clk), .rst_n(rst_n),
        .in_vs(m2_vs), .in_hs(m2_hs), .in_de(m2_de), .in_y(m2_y),
        .box_x0(regs_flat[1*32 +: 16]), .box_y0(regs_flat[2*32 +: 16]),
        .box_x1(regs_flat[3*32 +: 16]), .box_y1(regs_flat[4*32 +: 16]),
        .box_color(regs_flat[5*32 +: 8]),
        .roi_x0(regs_flat[6*32 +: 16]), .roi_y0(regs_flat[7*32 +: 16]),
        .roi_x1(regs_flat[8*32 +: 16]), .roi_y1(regs_flat[9*32 +: 16]),
        .roi_color(regs_flat[10*32 +: 8]),
        .out_vs(o_vs), .out_hs(o_hs), .out_de(o_de), .out_y(o_y)
    );

    // ---- mux 3：OSD 旁路 → 输出 ----
    assign out_vs = t_osd ? o_vs : m2_vs;
    assign out_hs = t_osd ? o_hs : m2_hs;
    assign out_de = t_osd ? o_de : m2_de;
    assign out_y  = t_osd ? o_y  : m2_y;
endmodule
