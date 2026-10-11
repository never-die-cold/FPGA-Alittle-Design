`timescale 1ns/1ps
// osd_overlay —— 检测框 / ROI 叠加（模块二）
// 契约（data/golden/vision/osd/gen_osd.py 一致）：
//   灰度流直通（1 拍延迟），两个 1px 描边框（box 检测框 / roi）内嵌输出，
//   命中像素以各自颜色替换，重叠处 box 优先；坐标在框范围外自然无命中。
//   框参数在帧首 in_vs 锁存——帧内改参数不影响当前帧（A4 动效换帧生效的语义基础）。
// 流约定与全链一致（vs 帧首 / hs 行尾 / de 像素）；x/y 计数器 16 位，与参数同宽。
module osd_overlay (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_vs,
    input  wire        in_hs,
    input  wire        in_de,
    input  wire [7:0]  in_y,
    input  wire [15:0] box_x0, box_y0, box_x1, box_y1,
    input  wire [7:0]  box_color,
    input  wire [15:0] roi_x0, roi_y0, roi_x1, roi_y1,
    input  wire [7:0]  roi_color,
    output reg         out_vs,
    output reg         out_hs,
    output reg         out_de,
    output reg  [7:0]  out_y
);
    // ---- 流位置计数（与 scaler 写侧同约定） ----
    reg [15:0] wx, wy;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wx <= 0; wy <= 0;
        end else begin
            if (in_vs || in_hs) wx <= 0;
            else if (in_de)     wx <= wx + 1;
            if (in_vs)          wy <= 0;
            else if (in_hs)     wy <= wy + 1;
        end
    end

    // ---- 参数帧首锁存 ----
    reg [15:0] bx0, by0, bx1, by1, rx0, ry0, rx1, ry1;
    reg [7:0]  bcol, rcol;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bx0 <= 0; by0 <= 0; bx1 <= 0; by1 <= 0; bcol <= 0;
            rx0 <= 0; ry0 <= 0; rx1 <= 0; ry1 <= 0; rcol <= 0;
        end else if (in_vs) begin
            bx0 <= box_x0; by0 <= box_y0; bx1 <= box_x1; by1 <= box_y1; bcol <= box_color;
            rx0 <= roi_x0;  ry0 <= roi_y0;  rx1 <= roi_x1;  ry1 <= roi_y1;  rcol <= roi_color;
        end
    end

    // ---- 命中判定（组合，1px 描边；box 优先） ----
    wire bx_in = (wx >= bx0) && (wx <= bx1);
    wire by_in = (wy >= by0) && (wy <= by1);
    wire box_border = bx_in && by_in && ((wx == bx0) || (wx == bx1) || (wy == by0) || (wy == by1));
    wire rx_in = (wx >= rx0) && (wx <= rx1);
    wire ry_in = (wy >= ry0) && (wy <= ry1);
    wire roi_border = rx_in && ry_in && ((wx == rx0) || (wx == rx1) || (wy == ry0) || (wy == ry1));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_vs <= 0; out_hs <= 0; out_de <= 0; out_y <= 0;
        end else begin
            out_vs <= in_vs;
            out_hs <= in_hs;
            out_de <= in_de;
            if (in_de)
                out_y <= box_border ? bcol : (roi_border ? rcol : in_y);
        end
    end
endmodule
