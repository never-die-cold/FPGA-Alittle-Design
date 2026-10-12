`timescale 1ns/1ps
// sobel —— 3×3 Sobel 边缘检测（模块二可选级）
// 契约（与 data/golden/vision/sobel/gen_sobel.py 一致）：
//   Gx = [-1 0 1; -2 0 2; -1 0 1]，Gy 为其转置；幅值取 |Gx|+|Gy|（L1 近似），8 位饱和。
// 实现口径：窗口装配/末行冲刷/流约定与 gaussian_3x3.v 完全同构（v0.1，见其头注释）；
// 若 10/5 评审决定抽公共窗口模块，二者一并重构。
module sobel #(
    parameter WIDTH  = 16,
    parameter HEIGHT = 8,
    parameter AW     = $clog2(WIDTH),
    parameter YW     = $clog2(HEIGHT+1)
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       in_vs,
    input  wire       in_hs,
    input  wire       in_de,
    input  wire [7:0] in_y,
    output reg        out_vs,     // 级间标记：与 out_de 同拍传播（4 拍延迟）
    output reg        out_hs,     // 行尾标记；末行冲刷时输出合成 hs（vblank 内）
    output reg        out_de,
    output reg  [7:0] out_g
);
    // ---- 位置计数与末行冲刷（同 gaussian_3x3） ----
    reg [AW:0]   x;
    reg [YW-1:0] y;
    reg          flushing;
    reg [AW+2:0] fc;
    // 冲刷窗口时序同 gaussian_3x3.v：eff_de 推迟 2 拍启动（fc∈[2,WIDTH+1]），
    // 给直通行尾 hs 留间隔；合成 hs 注入 fc==WIDTH+2（末像素后 1 拍）。
    wire flush_start = in_hs && (y == HEIGHT-1);
    wire eff_de = in_de || (flushing && fc >= 2 && fc < WIDTH+2);

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
                if (fc == WIDTH+3) flushing <= 0;
            end
        end
    end

    // ---- 双行缓存轮替（同 gaussian_3x3） ----
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

    reg [7:0] a0, a1, b0, b1;
    always @(posedge clk) begin
        a0 <= rd0; a1 <= a0;
        b0 <= rd1; b1 <= b0;
    end

    reg [7:0] c1, c2, c3;
    always @(posedge clk) begin
        c1 <= in_y; c2 <= c1; c3 <= c2;
    end

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

    wire [7:0] top_rd = y[0] ? rd1 : rd0;
    wire [7:0] top_r0 = y[0] ? b0  : a0;
    wire [7:0] top_r1 = y[0] ? b1  : a1;
    wire [7:0] mid_rd = y[0] ? rd0 : rd1;
    wire [7:0] mid_r0 = y[0] ? a0  : b0;
    wire [7:0] mid_r1 = y[0] ? a1  : b1;

    wire [7:0] midL = left_edge     ? mid_r0 : mid_r1;
    wire [7:0] midM = mid_r0;
    wire [7:0] midR = right_edge    ? mid_r0 : mid_rd;
    wire [7:0] topL = (y == 1)      ? midL : (left_edge  ? top_r0 : top_r1);
    wire [7:0] topM = (y == 1)      ? midM : top_r0;
    wire [7:0] topR = (y == 1)      ? midR : (right_edge ? top_r0 : top_rd);
    wire [7:0] botL = (y == HEIGHT) ? midL : (left_edge  ? c2 : c3);
    wire [7:0] botM = (y == HEIGHT) ? midM : c2;
    wire [7:0] botR = (y == HEIGHT) ? midR : (right_edge ? c2 : c1);

    // Sobel：Gx（水平差分）、Gy（垂直差分），幅值 |Gx|+|Gy|，饱和 255
    wire [10:0] gx_pos = topR + 2*midR + botR;
    wire [10:0] gx_neg = topL + 2*midL + botL;
    wire [10:0] gy_pos = botL + 2*botM + botR;
    wire [10:0] gy_neg = topL + 2*topM + topR;
    reg [9:0] gx_pos_r,gx_neg_r,gy_pos_r,gy_neg_r;
    reg arithmetic_valid;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            gx_pos_r<=0;gx_neg_r<=0;gy_pos_r<=0;gy_neg_r<=0;arithmetic_valid<=0;
        end else begin
            gx_pos_r<=gx_pos[9:0];gx_neg_r<=gx_neg[9:0];
            gy_pos_r<=gy_pos[9:0];gy_neg_r<=gy_neg[9:0];
            arithmetic_valid<=de_d2 && (y>=1);
        end
    end
    wire [10:0] gx = (gx_pos_r > gx_neg_r) ? (gx_pos_r - gx_neg_r) : (gx_neg_r - gx_pos_r);
    wire [10:0] gy = (gy_pos_r > gy_neg_r) ? (gy_pos_r - gy_neg_r) : (gy_neg_r - gy_pos_r);
    wire [11:0] mag = gx + gy;                     // <= 4*255*2 = 2040

    // 级间标记（同 gaussian_3x3）：直通 hs 门控 y>=1，冲刷末像素拍注入合成 hs
    wire hs_gen = (in_hs && (y >= 1)) || (flushing && (fc == WIDTH+2));
    reg  vs_d1, vs_d2, vs_d3,vs_d4;
    reg  hs_d1, hs_d2, hs_d3,hs_d4;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            vs_d1 <= 0; vs_d2 <= 0; vs_d3 <= 0;
            hs_d1 <= 0; hs_d2 <= 0; hs_d3 <= 0;
            vs_d4<=0;hs_d4<=0;
        end else begin
            vs_d1 <= in_vs; vs_d2 <= vs_d1; vs_d3 <= vs_d2;
            hs_d1 <= hs_gen; hs_d2 <= hs_d1; hs_d3 <= hs_d2;
            vs_d4<=vs_d3;hs_d4<=hs_d3;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_de <= 0; out_g <= 0;
            out_vs <= 0; out_hs <= 0;
        end else begin
            out_de <= arithmetic_valid;
            out_g  <= (mag > 12'd255) ? 8'd255 : mag[7:0];
            out_vs <= vs_d4;
            out_hs <= hs_d4;
        end
    end
endmodule
