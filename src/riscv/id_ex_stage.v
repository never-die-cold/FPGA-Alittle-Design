// id_ex_stage.v -- Part B v1 combinational decode/execute stage
module id_ex_stage (
    input wire in_valid, input wire [31:0] in_pc, in_instr,
    input wire [31:0] rs1_value, rs2_value, muldiv_result,
    output wire [4:0] rs1_addr, rs2_addr, rd_addr,
    output wire uses_rs1, uses_rs2, muldiv_valid,
    output wire [2:0] muldiv_op,
    output wire branch_taken, jump_taken,
    output wire [31:0] redirect_target,
    output wire [31:0] ex_result, ex_addr, ex_store_data,
    output wire ex_reg_write, ex_mem_read, ex_mem_write,
    output wire [1:0] ex_wb_sel, ex_mask_sel,
    output wire ex_sign_ext
);
    wire [31:0] instr = in_instr;
    wire [31:0] imm; wire [2:0] imm_type, branch_type;
    wire [3:0] alu_op; wire [1:0] alu_a_sel, alu_b_sel;
    wire [1:0] wb_sel, mask_sel, jump_type;
    wire reg_write, mem_read, mem_write, sign_ext;
    decode u_decode (.*);

    wire [31:0] alu_a = (alu_a_sel == 2'b01) ? in_pc :
                            (alu_a_sel == 2'b10) ? 32'd0 : rs1_value;
    wire [31:0] alu_b = (alu_b_sel == 2'b00) ? rs2_value : imm;
    wire [31:0] alu_y; wire alu_zero, alu_lt, alu_ltu;
    alu u_alu (.a(alu_a), .b(alu_b), .alu_op(alu_op), .y(alu_y),
               .zero(alu_zero), .lt(alu_lt), .ltu(alu_ltu));

    wire cond_taken = (branch_type == 3'd1) ?  alu_zero :
                      (branch_type == 3'd2) ? ~alu_zero :
                      (branch_type == 3'd3) ?  alu_lt :
                      (branch_type == 3'd4) ? ~alu_lt :
                      (branch_type == 3'd5) ?  alu_ltu :
                      (branch_type == 3'd6) ? ~alu_ltu : 1'b0;
    assign branch_taken = (branch_type != 0) && cond_taken;
    assign jump_taken = (jump_type != 0);
    assign redirect_target = (jump_type == 2'd2) ?
                             (alu_y & 32'hffff_fffe) : (in_pc + imm);
    assign ex_result = (wb_sel == 2'd2) ? (in_pc + 4) :
                       (wb_sel == 2'd3) ? muldiv_result : alu_y;
    assign ex_addr = alu_y;
    assign ex_store_data = rs2_value;
    assign ex_reg_write = reg_write;
    assign ex_mem_read = mem_read;
    assign ex_mem_write = mem_write;
    assign ex_wb_sel = wb_sel;
    assign ex_mask_sel = mask_sel;
    assign ex_sign_ext = sign_ext;
endmodule
