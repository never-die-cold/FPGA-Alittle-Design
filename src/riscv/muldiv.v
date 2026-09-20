// muldiv.v —— M 扩展乘除单元（v0 预留未实现，接口已冻结）
// 接口见 src/riscv/design_v0.md §5.6；Part A 收尾补实现
module muldiv (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [1:0]  op,
    input  wire        start,
    input  wire [31:0] a,
    input  wire [31:0] b,
    output wire [31:0] result,
    output wire        busy
);

    assign result = 32'd0;
    assign busy   = 1'b0;

endmodule
