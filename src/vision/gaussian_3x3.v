`timescale 1ns/1ps
// gaussian_3x3 —— 3×3 高斯滤波（模块二）
// 契约（src/vision/design_v0.md §3/§4）：核 [1 2 1;2 4 2;1 2 1]/16，边界像素复制。
// 实现口径 v0.1（2026-09-29，单元级，10/5 评审后冻结）：
//   * 2 片 line_buffer 按行号奇偶轮替；输出行落后输入 1 行（输出行 l 使用行 {l-1, l, l+1}，
//     对应流内行 {y-2, y-1, y}），末行 l=HEIGHT-1 在帧尾 vblank 冲刷补出（底邻居钳位为自身）；
//   * 流约定：in_vs 帧首单拍（清 x/y）；in_hs 行尾单拍（清 x、y+1），与该行最后一个 de
//     间隔 >=3 拍、与下一行首个 de 间隔 >=1 拍；帧尾 vblank >= WIDTH+8 拍供冲刷；
//   * 列方向：读地址跟随流列号，{rd, r0, r1} 三级链在输出拍自然给出 {右, 中, 左} 三列，
//     当前行用 {c1, c2, c3} 延迟链取 {右, 中, 左}；左/右边界用中列值钳位；
//   * line_buffer 同拍同址先读后写，保证 top 行从"正在被写入的 buffer"读到旧行内容。
module gaussian_3x3 #(
    parameter WIDTH  = 16,
    parameter HEIGHT = 8,
    parameter AW     = $clog2(WIDTH),
    parameter YW     = $clog2(HEIGHT+1)
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       in_vs,      // 帧首标记（单拍）
    input  wire       in_hs,      // 行尾标记（单拍，该行 de 结束 >=3 拍后）
    input  wire       in_de,      // 像素有效
    input  wire [7:0] in_y,       // 灰度像素流
    output reg        out_de,
    output reg  [7:0] out_g
);
    // ---- 位置计数与末行冲刷 ----
    reg [AW:0]   x;         // 可达 WIDTH（末列保持，供右边界钳位读数）
    reg [YW-1:0] y;         // 流内行号；末行 hs 后 = HEIGHT
    reg          flushing;
    reg [AW:0]   fc;
    wire flush_start = in_hs && (y == HEIGHT-1);
    wire eff_de = in_de || (flushing && fc < WIDTH);   // 冲刷恰好 WIDTH 拍（末列有显式钳位，无需保持拍）

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x <= 0; y <= 0; flushing <= 0; fc <= 0;
        end else begin
            if (in_vs || in_hs) x <= 0;
            else if (eff_de)    x <= x + 1;
            if (in_vs)          y <= 0;
            else if (in_hs)     y <= y + 1;
            if (flush_start) begin
                flushing <= 1; fc <= 0;
            end else if (flushing) begin
                fc <= fc + 1;
                if (fc == WIDTH-1) flushing <= 0;
            end
        end
    end

    // ---- 双行缓存轮替（we 按行号奇偶） ----
    wire [AW-1:0] ra = (x == WIDTH) ? (WIDTH-1) : x[AW-1:0];
    wire          we0 = in_de && (y[0] == 1'b0);
    wire          we1 = in_de && (y[0] == 1'b1);
    wire [7:0]    rd0, rd1;

    line_buffer #(.WIDTH(WIDTH), .DW(8)) lb0 (
        .clk(clk), .we(we0), .waddr(ra), .wdata(in_y), .raddr(ra), .rdata(rd0)
    );
    line_buffer #(.WIDTH(WIDTH), .DW(8)) lb1 (
        .clk(clk), .we(we1), .waddr(ra), .wdata(in_y), .raddr(ra), .rdata(rd1)
    );

    // 读链：输出拍 {左, 中, 右} = {r1, r0, rd}
    reg [7:0] a0, a1, b0, b1;
    always @(posedge clk) begin
        a0 <= rd0; a1 <= a0;
        b0 <= rd1; b1 <= b0;
    end

    // 当前行延迟链：输出拍 {左, 中, 右} = {c3, c2, c1}
    reg [7:0] c1, c2, c3;
    always @(posedge clk) begin
        c1 <= in_y; c2 <= c1; c3 <= c2;
    end

    // 输出对齐：de/列号打两拍（窗口中心列 = 流列号 - 2）
    reg        de_d1, de_d2;
    reg [AW:0] xd1, xd2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            de_d1 <= 0; de_d2 <= 0; xd1 <= 0; xd2 <= 0;
        end else begin
            de_d1 <= eff_de; de_d2 <= de_d1;
            xd1 <= x; xd2 <= xd1;
        end
    end

    wire [AW-1:0] k = (xd2 == WIDTH) ? (WIDTH-1) : xd2[AW-1:0];
    wire left_edge  = (k == 0);
    wire right_edge = (k == WIDTH-1);

    // 行角色：y 偶 → top 行 = buf0 链（旧内容 = 行 y-2）、mid 行 = buf1 链（行 y-1）；y 奇互换
    wire [7:0] top_rd = y[0] ? rd1 : rd0;
    wire [7:0] top_r0 = y[0] ? b0  : a0;
    wire [7:0] top_r1 = y[0] ? b1  : a1;
    wire [7:0] mid_rd = y[0] ? rd0 : rd1;
    wire [7:0] mid_r0 = y[0] ? a0  : b0;
    wire [7:0] mid_r1 = y[0] ? a1  : b1;

    // 窗口组装：列边界用中列钳位；首行 top:=mid（上邻居钳位）；冲刷行 bottom:=mid（下邻居钳位）
    wire [7:0] midL = left_edge     ? mid_r0 : mid_r1;
    wire [7:0] midM = mid_r0;
    wire [7:0] midR = right_edge    ? mid_r0 : mid_rd;
    wire [7:0] topL = (y == 1)      ? midL : (left_edge  ? top_r0 : top_r1);
    wire [7:0] topM = (y == 1)      ? midM : top_r0;
    wire [7:0] topR = (y == 1)      ? midR : (right_edge ? top_r0 : top_rd);
    wire [7:0] botL = (y == HEIGHT) ? midL : (left_edge  ? c2 : c3);
    wire [7:0] botM = (y == HEIGHT) ? midM : c2;
    wire [7:0] botR = (y == HEIGHT) ? midR : (right_edge ? c2 : c1);

    // 卷积：核 [1 2 1;2 4 2;1 2 1]，和 <= 16*255，>>4 即除 16
    wire [11:0] sum = topL + 2*topM + topR
                    + 2*midL + 4*midM + 2*midR
                    + botL + 2*botM + botR;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_de <= 0; out_g <= 0;
        end else begin
            out_de <= de_d2 && (y >= 1);   // y=0（流内首行）无输出行；y=HEIGHT 为冲刷行
            out_g  <= sum[11:4];
        end
    end
endmodule
