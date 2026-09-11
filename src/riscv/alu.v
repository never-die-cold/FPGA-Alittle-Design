// alu.v —— 算术/逻辑/移位/比较运算；比较标志供分支裁决
// 编码见 src/riscv/design_v0.md §6.1
module alu (
    input  wire [31:0] a,
    input  wire [31:0] b,
    input  wire [3:0]  alu_op,
    output reg  [31:0] y,
    output wire        zero,
    output wire        lt,
    output wire        ltu
);

    localparam [3:0] ALU_ADD  = 4'd0,
                     ALU_SUB  = 4'd1,
                     ALU_SLL  = 4'd2,
                     ALU_XOR  = 4'd3,
                     ALU_OR   = 4'd4,
                     ALU_SRL  = 4'd5,
                     ALU_SRA  = 4'd6,
                     ALU_SLT  = 4'd7,
                     ALU_SLTU = 4'd8,
                     ALU_AND  = 4'd9;

    always @(*) begin
        case (alu_op)
            ALU_SUB:  y = a - b;
            ALU_SLL:  y = a << b[4:0];
            ALU_XOR:  y = a ^ b;
            ALU_OR:   y = a | b;
            ALU_SRL:  y = a >> b[4:0];
            ALU_SRA:  y = $signed(a) >>> b[4:0];
            ALU_SLT:  y = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            ALU_SLTU: y = (a < b) ? 32'd1 : 32'd0;
            ALU_AND:  y = a & b;
            default:  y = a + b;
        endcase
    end

    assign zero = (y == 32'd0);
    assign lt   = ($signed(a) < $signed(b));
    assign ltu  = (a < b);

endmodule
