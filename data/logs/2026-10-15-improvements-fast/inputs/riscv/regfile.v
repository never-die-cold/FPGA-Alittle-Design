// regfile.v —— 32×32 通用寄存器堆：2 读 1 写，组合读、时钟沿写，x0 恒 0
// 接口见 src/riscv/design_v0.md §5.4
module regfile (
    input  wire        clk,
    input  wire [4:0]  raddr1,
    input  wire [4:0]  raddr2,
    output wire [31:0] rdata1,
    output wire [31:0] rdata2,
    input  wire [4:0]  waddr,
    input  wire [31:0] wdata,
    input  wire        we
);

    reg [31:0] regs [0:31];

    assign rdata1 = (raddr1 == 5'd0) ? 32'd0 : regs[raddr1];
    assign rdata2 = (raddr2 == 5'd0) ? 32'd0 : regs[raddr2];

    always @(posedge clk) begin
        if (we && waddr != 5'd0)
            regs[waddr] <= wdata;
    end

endmodule
