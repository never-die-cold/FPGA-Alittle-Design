`timescale 1ns/1ps
// vision_top —— 模块二流水线顶层（v0.3：双路径拓扑）
// 显示路径（全分辨率直通，A5 延迟固定可测）：
//   rgb2gray（恒接）→ [gaussian] → [sobel] → [osd] → out_*（送给 HDMI OUT，全分辨率）
// 快照分支（喂模块三协处理器，design_v0 §7）：
//   [scaler] → cop_*（DW×DH 灰度流，R0 bit1 使能；M3 落乒乓行组缓冲后接 cop_top）
//   两路径在 sobel 之后分叉——scaler 不再串在显示路径里（224 小图不上屏）。
// R0 位定义 v0.2：bit0 gauss_en / bit1 scaler_en（快照使能）/ bit2 osd_en / bit3 sobel_en。
// 拓扑切换语义：路径选择在输入帧首 in_vs 锁存，帧内恒定；每帧自洽，帧间可变。
// HDMI 解码/编码不在本单元：输入为归一化后的 RGB 像素流（in_align），输出为处理后的
//   灰度流；单时钟域（与 axi_regs 同，跨时钟见 design_v0 §3.1 D10 口径）。
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
    // 处理输出（显示路径，全分辨率灰度流）
    output wire       out_vs,
    output wire       out_hs,
    output wire       out_de,
    output wire [7:0] out_y,
    // 快照输出（scaler 缩放流，= 模块三 CNN 输入尺寸；R0 bit1 使能）
    output wire       cop_vs,
    output wire       cop_hs,
    output wire       cop_de,
    output wire [7:0] cop_y
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
    reg t_gauss, t_scaler, t_osd, t_sobel;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t_gauss <= 0; t_scaler <= 0; t_osd <= 0; t_sobel <= 0;
        end else if (in_vs) begin
            t_gauss  <= gauss_en;
            t_scaler <= scaler_en;
            t_osd    <= osd_en;
            t_sobel  <= r0[3];
        end
    end

    // ---- mux 1：高斯旁路 ----
    wire       m1_vs = t_gauss  ? g1_vs : g0_vs;
    wire       m1_hs = t_gauss  ? g1_hs : g0_hs;
    wire       m1_de = t_gauss  ? g1_de : g0_de;
    wire [7:0] m1_y  = t_gauss  ? g1_y  : g0_y;

    // ---- 级 1b：Sobel 边缘（窗口装配/冲刷与 gaussian 同构，3 拍延迟） ----
    wire       e_vs, e_hs, e_de;
    wire [7:0] e_y;
    sobel #(.WIDTH(SW), .HEIGHT(SH)) u_sobel (
        .clk(clk), .rst_n(rst_n),
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
        .clk(clk), .rst_n(rst_n),
        .in_vs(m1b_vs), .in_hs(m1b_hs), .in_de(m1b_de), .in_y(m1b_y),
        .out_vs(s_vs), .out_hs(s_hs), .out_de(s_de), .out_y(s_y)
    );
    assign cop_vs = t_scaler ? s_vs : 1'b0;
    assign cop_hs = t_scaler ? s_hs : 1'b0;
    assign cop_de = t_scaler ? s_de : 1'b0;
    assign cop_y  = s_y;

    // ---- 级 3：OSD 叠加（框参数 = R1..R10，坐标系 = 全分辨率显示图） ----
    wire       o_vs, o_hs, o_de;
    wire [7:0] o_y;
    osd_overlay u_osd (
        .clk(clk), .rst_n(rst_n),
        .in_vs(m1b_vs), .in_hs(m1b_hs), .in_de(m1b_de), .in_y(m1b_y),
        .box_x0(regs_flat[1*32 +: 16]), .box_y0(regs_flat[2*32 +: 16]),
        .box_x1(regs_flat[3*32 +: 16]), .box_y1(regs_flat[4*32 +: 16]),
        .box_color(regs_flat[5*32 +: 8]),
        .roi_x0(regs_flat[6*32 +: 16]), .roi_y0(regs_flat[7*32 +: 16]),
        .roi_x1(regs_flat[8*32 +: 16]), .roi_y1(regs_flat[9*32 +: 16]),
        .roi_color(regs_flat[10*32 +: 8]),
        .out_vs(o_vs), .out_hs(o_hs), .out_de(o_de), .out_y(o_y)
    );

    // ---- mux 3：OSD 旁路 → 显示输出（全分辨率直通显示） ----
    assign out_vs = t_osd ? o_vs : m1b_vs;
    assign out_hs = t_osd ? o_hs : m1b_hs;
    assign out_de = t_osd ? o_de : m1b_de;
    assign out_y  = t_osd ? o_y  : m1b_y;
endmodule
