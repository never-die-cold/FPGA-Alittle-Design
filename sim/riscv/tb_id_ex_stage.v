`timescale 1ns/1ps
module tb_id_ex_stage;
    reg in_valid; reg [31:0] in_pc, in_instr;
    reg [31:0] rs1_value, rs2_value, muldiv_result;
    wire [4:0] rs1_addr, rs2_addr, rd_addr;
    wire uses_rs1, uses_rs2, muldiv_valid; wire [2:0] muldiv_op;
    wire branch_taken, jump_taken; wire [31:0] redirect_target;
    wire [31:0] ex_result, ex_addr, ex_store_data;
    wire ex_reg_write, ex_mem_read, ex_mem_write, ex_sign_ext;
    wire [1:0] ex_wb_sel, ex_mask_sel;
    integer checks;
    id_ex_stage dut (
        .in_valid(in_valid), .in_pc(in_pc), .in_instr(in_instr),
        .rs1_value(rs1_value), .rs2_value(rs2_value),
        .muldiv_result(muldiv_result),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rd_addr(rd_addr),
        .uses_rs1(uses_rs1), .uses_rs2(uses_rs2),
        .muldiv_valid(muldiv_valid), .muldiv_op(muldiv_op),
        .branch_taken(branch_taken), .jump_taken(jump_taken),
        .redirect_target(redirect_target), .ex_result(ex_result),
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
        $display("PASS: ID+EX decode, execute and redirect (%0d cases)", checks);
        $finish;
    end
endmodule
