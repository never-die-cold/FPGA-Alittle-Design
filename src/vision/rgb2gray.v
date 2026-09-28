`timescale 1ns/1ps
// rgb2gray —— RGB888 转灰度（模块二流水线第一级）
// 契约：Y = (77R + 150G + 29B) >> 8（BT.601 定点，src/vision/design_v0.md §4）
// 流约定：单时钟域，in_de 高表示当前输入像素有效；输出对齐输入，固定延迟 1 拍。
module rgb2gray (
    input  wire        clk,
    input  wire        in_de,
    input  wire [23:0] in_rgb,      // {R[7:0], G[7:0], B[7:0]}
    output reg         out_de,
    output reg  [7:0]  out_y
);
    always @(posedge clk) begin
        out_de <= in_de;
        if (in_de)
            out_y <= (77  * in_rgb[23:16]
                    + 150 * in_rgb[15:8]
                    + 29  * in_rgb[7:0]) >> 8;
    end
endmodule
