// decode.v —— 指令译码：全部控制信号 + 立即数生成（RV32I；M 扩展预留 muldiv_op）
// 控制真值表见 src/riscv/design_v0.md §6
module decode (
    input  wire [31:0] instr,
    output reg  [4:0]  rs1_addr,
    output reg  [4:0]  rs2_addr,
    output reg  [4:0]  rd_addr,
    output reg  [31:0] imm,
    output reg  [2:0]  imm_type,
    output reg  [3:0]  alu_op,
    output reg  [1:0]  alu_a_sel,
    output reg  [1:0]  alu_b_sel,
    output reg  [1:0]  wb_sel,
    output reg         reg_write,
    output reg         mem_read,
    output reg         mem_write,
    output reg  [1:0]  mask_sel,
    output reg         sign_ext,
    output reg  [2:0]  branch_type,
    output reg  [1:0]  jump_type,
    output reg  [1:0]  muldiv_op
);

    localparam [6:0] OP_LUI    = 7'h37,
                     OP_AUIPC  = 7'h17,
                     OP_JAL    = 7'h6F,
                     OP_JALR   = 7'h67,
                     OP_BRANCH = 7'h63,
                     OP_LOAD   = 7'h03,
                     OP_STORE  = 7'h23,
                     OP_IMM    = 7'h13,
                     OP_REG    = 7'h33;

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

    localparam [1:0] A_RS1  = 2'b00,
                     A_PC   = 2'b01,
                     A_ZERO = 2'b10;

    localparam [1:0] B_RS2 = 2'b00,
                     B_IMM = 2'b01;

    localparam [1:0] WB_ALU = 2'b00,
                     WB_MEM = 2'b01,
                     WB_PC4 = 2'b10;

    wire [6:0] opcode = instr[6:0];
    wire [2:0] funct3 = instr[14:12];
    wire [6:0] funct7 = instr[31:25];

    always @(*) begin
        rs1_addr = instr[19:15];
        rs2_addr = instr[24:20];
        rd_addr  = instr[11:7];

        imm_type    = 3'd0;
        alu_op      = ALU_ADD;
        alu_a_sel   = A_RS1;
        alu_b_sel   = B_IMM;
        wb_sel      = WB_ALU;
        reg_write   = 1'b0;
        mem_read    = 1'b0;
        mem_write   = 1'b0;
        mask_sel    = 2'b10;
        sign_ext    = 1'b0;
        branch_type = 3'd0;
        jump_type   = 2'd0;
        muldiv_op   = 2'd0;

        case (opcode)
            OP_LUI: begin
                imm_type  = 3'd3;
                alu_a_sel = A_ZERO;
                reg_write = 1'b1;
            end
            OP_AUIPC: begin
                imm_type  = 3'd3;
                alu_a_sel = A_PC;
                reg_write = 1'b1;
            end
            OP_JAL: begin
                imm_type  = 3'd4;
                alu_a_sel = A_PC;
                wb_sel    = WB_PC4;
                reg_write = 1'b1;
                jump_type = 2'd1;
            end
            OP_JALR: begin
                imm_type  = 3'd0;
                wb_sel    = WB_PC4;
                reg_write = 1'b1;
                jump_type = 2'd2;
            end
            OP_BRANCH: begin
                imm_type  = 3'd2;
                alu_a_sel = A_RS1;
                alu_b_sel = B_RS2;
                alu_op    = ALU_SUB;
                case (funct3)
                    3'b000:  branch_type = 3'd1;
                    3'b001:  branch_type = 3'd2;
                    3'b100:  branch_type = 3'd3;
                    3'b101:  branch_type = 3'd4;
                    3'b110:  branch_type = 3'd5;
                    3'b111:  branch_type = 3'd6;
                    default: branch_type = 3'd0;
                endcase
            end
            OP_LOAD: begin
                imm_type  = 3'd0;
                reg_write = 1'b1;
                mem_read  = 1'b1;
                wb_sel    = WB_MEM;
                case (funct3)
                    3'b000: begin mask_sel = 2'b00; sign_ext = 1'b1; end
                    3'b001: begin mask_sel = 2'b01; sign_ext = 1'b1; end
                    3'b100: begin mask_sel = 2'b00; sign_ext = 1'b0; end
                    3'b101: begin mask_sel = 2'b01; sign_ext = 1'b0; end
                    default: begin mask_sel = 2'b10; sign_ext = 1'b0; end
                endcase
            end
            OP_STORE: begin
                imm_type  = 3'd1;
                mem_write = 1'b1;
                case (funct3)
                    3'b000:  mask_sel = 2'b00;
                    3'b001:  mask_sel = 2'b01;
                    default: mask_sel = 2'b10;
                endcase
            end
            OP_IMM: begin
                imm_type  = 3'd0;
                reg_write = 1'b1;
                case (funct3)
                    3'b000:  alu_op = ALU_ADD;
                    3'b001:  alu_op = ALU_SLL;
                    3'b010:  alu_op = ALU_SLT;
                    3'b011:  alu_op = ALU_SLTU;
                    3'b100:  alu_op = ALU_XOR;
                    3'b101:  alu_op = funct7[5] ? ALU_SRA : ALU_SRL;
                    3'b110:  alu_op = ALU_OR;
                    3'b111:  alu_op = ALU_AND;
                    default: alu_op = ALU_ADD;
                endcase
            end
            OP_REG: begin
                alu_a_sel = A_RS1;
                alu_b_sel = B_RS2;
                reg_write = 1'b1;
                if (funct7 == 7'h01) begin
                    // M 扩展：v0 暂不实现（design_v0.md §9 决策 2），按 NOP 处理
                    reg_write = 1'b0;
                    muldiv_op = {1'b0, funct3[1:0]};
                end else begin
                    case (funct3)
                        3'b000:  alu_op = funct7[5] ? ALU_SUB : ALU_ADD;
                        3'b001:  alu_op = ALU_SLL;
                        3'b010:  alu_op = ALU_SLT;
                        3'b011:  alu_op = ALU_SLTU;
                        3'b100:  alu_op = ALU_XOR;
                        3'b101:  alu_op = funct7[5] ? ALU_SRA : ALU_SRL;
                        3'b110:  alu_op = ALU_OR;
                        3'b111:  alu_op = ALU_AND;
                        default: alu_op = ALU_ADD;
                    endcase
                end
            end
            default: ; // NOP / 未实现指令（fence/ecall/ebreak 等）
        endcase

        // 立即数生成（依赖上面得到的 imm_type）
        case (imm_type)
            3'd0:    imm = {{20{instr[31]}}, instr[31:20]};
            3'd1:    imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};
            3'd2:    imm = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
            3'd3:    imm = {instr[31:12], 12'b0};
            default: imm = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};
        endcase
    end

endmodule
