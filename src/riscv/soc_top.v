// soc_top.v —— PL 侧 SoC 顶层外壳：核 + 指令 BRAM + 数据 RAM + LED 驱动（待实现）
// 规划见 src/riscv/design_v0.md §5.8
module soc_top (
    input  wire       clk,
    input  wire       rst_n,
    output wire [3:0] led
);

endmodule
