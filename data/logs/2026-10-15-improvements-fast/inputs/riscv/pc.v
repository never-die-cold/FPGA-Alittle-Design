// pc.v —— 程序计数器：顺序 +4 / 跳转目标 / 保持
// 接口见 src/riscv/design_v0.md §5.1
module pc (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [1:0]  pc_sel,
    input  wire        stall,
    input  wire [31:0] pc_target,
    output reg  [31:0] pc,
    output wire [31:0] pc_plus4
);

    assign pc_plus4 = pc + 32'd4;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc <= 32'h8000_0000;
        else if (stall)
            pc <= pc;
        else case (pc_sel)
            2'b00:   pc <= pc_plus4;
            2'b01:   pc <= pc_target;
            default: pc <= pc;
        endcase
    end

endmodule
