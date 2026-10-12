`timescale 1ns/1ps
// in_align —— HDMI 输入归一化（模块二，ADV7611 解码流 → design_v0.md §3.1 流约定）
// 输入：板上 ADV7611 解码后的并行 RGB + de/hs/vs（与 pclk 同步；hs/vs 的极性、
//       脉宽与相对 de 的位置随源格式/芯片配置而变，不可直接喂给流水线）。
// 输出：out_de/out_rgb 直通；out_vs 重定时为帧首单拍（raw vs 有效边沿当拍）；
//       out_hs 重定时为行尾单拍（de 拉低后第 HS_DLY 拍），满足 §3.1
//       "hs 与该行最后一个 de 间隔 >=3 拍、与下一行首个 de 间隔 >=1 拍"；
//       vs/hs 撞拍时 hs 让路顺延一拍（§3.1 vs/hs 不同拍，下游计数依赖）。
// 约束（真实 HDMI 恒成立，tb 紧凑格式须遵守）：
//   1) 源行消隐 >= HS_DLY+2 拍（hs 发射与下一行 de 留间隔）；
//   2) raw vs 位于场消隐内且不与 de 重叠（vs 边沿当拍成为 out_vs，若同拍 de
//      会吞掉下游一个像素计数——真实源 vs 恒在场消隐，不做补偿逻辑）。
module in_align #(
    parameter HS_DLY = 3,      // hs 相对 de 拉低沿的延迟拍数（>=1）
    parameter VS_POL = 1'b1,   // raw vs 有效极性
    parameter HS_POL = 1'b1    // raw hs 有效极性
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_vs,
    input  wire        in_hs,
    input  wire        in_de,
    input  wire [23:0] in_rgb,
    output reg         out_vs,
    output reg         out_hs,
    output wire        out_de,
    output wire [23:0] out_rgb
);
    // raw 同步边沿检测（同 pclk 域，无需 CDC；极性归一后取边沿成单拍）
    wire vs_eff = (in_vs == VS_POL);
    wire hs_eff = (in_hs == HS_POL);
    reg  vs_d;
    wire vs_edge = vs_eff & ~vs_d;

    reg  de_d;
    wire de_fall = de_d & ~in_de;

    // hs 重定时：de 拉低后计数到 HS_DLY 发射单拍；撞 vs 边沿则顺延一拍
    reg [7:0] hs_wait;
    reg       hs_defer;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            vs_d <= 0; de_d <= 0;
            hs_wait <= 0; hs_defer <= 0;
            out_vs <= 0; out_hs <= 0;
        end else begin
            vs_d    <= vs_eff;
            de_d    <= in_de;
            hs_wait <= de_fall ? HS_DLY :
                       (hs_wait != 0) ? hs_wait - 1 : 8'h00;
            out_vs  <= vs_edge;
            out_hs  <= (hs_wait == 1 && !vs_edge) || (hs_defer && !vs_edge);
            hs_defer <= (hs_wait == 1 && vs_edge);
        end
    end

    assign out_de  = in_de;
    assign out_rgb = in_rgb;
endmodule
