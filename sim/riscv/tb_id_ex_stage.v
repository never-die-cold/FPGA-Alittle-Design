`timescale 1ns/1ps
module tb_id_ex_stage;
    reg in_valid; reg [31:0] in_pc, in_instr;
    reg [31:0] rs1_value, rs2_value, muldiv_result;
    wire [4:0] rs1_addr, rs2_addr, rd_addr;
    wire uses_rs1, uses_rs2, muldiv_valid; wire [2:0] muldiv_op;
    wire branch_taken, jump_taken; wire [31:0] redirect_target;
    wire [31:0] branch_target, branch_target_next;
    wire [31:0] ex_result, ex_addr, ex_store_data;
    wire ex_reg_write, ex_mem_read, ex_mem_write, ex_sign_ext;
    wire [1:0] ex_wb_sel, ex_mask_sel;
    integer checks, offset, pc_case;
    reg [12:0] b_offset;
    reg [31:0] expected_target;
    id_ex_stage dut (
        .in_valid(in_valid), .in_pc(in_pc), .in_instr(in_instr),
        .rs1_value(rs1_value), .rs2_value(rs2_value),
        .muldiv_result(muldiv_result),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rd_addr(rd_addr),
        .uses_rs1(uses_rs1), .uses_rs2(uses_rs2),
        .muldiv_valid(muldiv_valid), .muldiv_op(muldiv_op),
        .branch_taken(branch_taken), .jump_taken(jump_taken),
        .redirect_target(redirect_target), .ex_result(ex_result),
        .branch_target(branch_target), .branch_target_next(branch_target_next),
        .ex_addr(ex_addr), .ex_store_data(ex_store_data),
        .ex_reg_write(ex_reg_write), .ex_mem_read(ex_mem_read),
        .ex_mem_write(ex_mem_write), .ex_wb_sel(ex_wb_sel),
        .ex_mask_sel(ex_mask_sel), .ex_sign_ext(ex_sign_ext)
    );
    task check; input ok; begin checks=checks+1; if (ok !== 1'b1) begin
        $display("FAIL: ID+EX case %0d", checks); $fatal(1); end end endtask
    task check_branch;
        input [31:0] branch_instr, lhs, rhs; input expected;
        begin
            in_instr=branch_instr; rs1_value=lhs; rs2_value=rhs; #1;
            check(branch_taken === expected);
        end
    endtask

    initial begin
        checks=0; in_valid=1; in_pc=32'h80000000; muldiv_result=32'h15;
        in_instr=32'h002081b3; rs1_value=7; rs2_value=3; #1;
        check(rs1_addr==1 && rs2_addr==2 && rd_addr==3 && uses_rs1 &&
              uses_rs2 && ex_result==10 && ex_reg_write && !ex_mem_write);
        in_instr=32'h0062a423; rs1_value=32'h80000100; rs2_value=32'hdeadbeef; #1;
        check(ex_addr==32'h80000108 && ex_store_data==32'hdeadbeef &&
              ex_mem_write && !ex_reg_write && ex_mask_sel==2);
        in_instr=32'h00208463; in_pc=32'h80000010; rs1_value=5; rs2_value=5; #1;
        check(branch_taken && !jump_taken && redirect_target==32'h80000018);
        check_branch(32'h00208463, 5, 6, 0);                    // beq
        check_branch(32'h00209463, 5, 6, 1);                    // bne
        check_branch(32'h00209463, 5, 5, 0);
        check_branch(32'h0020c463, 32'h80000000, 1, 1);         // blt signed
        check_branch(32'h0020c463, 1, 32'h80000000, 0);
        check_branch(32'h0020d463, 1, 32'h80000000, 1);         // bge signed
        check_branch(32'h0020d463, 32'h80000000, 1, 0);
        check_branch(32'h0020e463, 1, 32'h80000000, 1);         // bltu unsigned
        check_branch(32'h0020e463, 32'h80000000, 1, 0);
        check_branch(32'h0020f463, 32'h80000000, 1, 1);         // bgeu unsigned
        check_branch(32'h0020f463, 1, 32'h80000000, 0);
        in_instr=32'h001100e7; in_pc=32'h80000020; rs1_value=32'h1000; #1;
        check(jump_taken && redirect_target==32'h1000 &&
              ex_result==32'h80000024 && rd_addr==1);
        in_instr=32'h022081b3; rs1_value=7; rs2_value=3; #1;
        check(muldiv_valid && muldiv_op==0 && ex_wb_sel==3 && ex_result==21);
        // Every encodable B offset, including sign extension, bit1 and wraparound.
        for (pc_case=0; pc_case<3; pc_case=pc_case+1) begin
            case (pc_case)
                0: in_pc=32'h80000000;
                1: in_pc=32'hfffffffc;
                2: in_pc=32'h00000002;
            endcase
            for (offset=-4096; offset<=4094; offset=offset+2) begin
                b_offset=offset[12:0];
                in_instr={b_offset[12],b_offset[10:5],5'd2,5'd1,
                          3'b000,b_offset[4:1],b_offset[11],7'b1100011};
                expected_target=in_pc+offset; #1;
                check(branch_target === expected_target &&
                      branch_target_next === (expected_target+32'd4) &&
                      redirect_target === expected_target);
            end
        end
        $display("PASS: ID+EX decode, execute and redirect (%0d cases)", checks);
        $finish;
    end
endmodule
