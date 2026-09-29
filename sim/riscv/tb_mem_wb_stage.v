`timescale 1ns/1ps
module tb_mem_wb_stage;
    reg clk, rst_n, in_valid;
    reg [31:0] in_instr, in_pc; reg [4:0] in_rd;
    reg [31:0] in_result, in_addr, in_store_data;
    reg in_reg_write, in_mem_read, in_mem_write;
    reg [1:0] in_wb_sel, in_mask_sel; reg in_sign_ext;
    wire mem_valid; wire [31:0] mem_instr, mem_pc; wire [4:0] mem_rd;
    wire [31:0] mem_result, mem_addr, mem_store_data;
    wire mem_reg_write, mem_mem_read, mem_mem_write;
    wire [1:0] mem_wb_sel, mem_mask_sel; wire mem_sign_ext;
    integer checks;
    mem_wb_stage dut (.*);
    always #5 clk = ~clk;

    task capture_check;
        begin
            @(posedge clk); #1; checks = checks + 1;
            if ({mem_valid,mem_instr,mem_pc,mem_rd,mem_result,mem_addr,
                 mem_store_data,mem_reg_write,mem_mem_read,mem_mem_write,
                 mem_wb_sel,mem_mask_sel,mem_sign_ext} !==
                {in_valid,in_instr,in_pc,in_rd,in_result,in_addr,
                 in_store_data,in_reg_write,in_mem_read,in_mem_write,
                 in_wb_sel,in_mask_sel,in_sign_ext}) begin
                $display("FAIL %0d: MEM+WB capture mismatch", checks);
                $fatal(1);
            end
        end
    endtask

    initial begin
        clk=0; rst_n=0; checks=0;
        in_valid=0; in_instr=0; in_pc=0; in_rd=0;
        in_result=0; in_addr=0; in_store_data=0;
        in_reg_write=0; in_mem_read=0; in_mem_write=0;
        in_wb_sel=0; in_mask_sel=0; in_sign_ext=0;
        #2; if (mem_valid !== 0) $fatal(1, "reset did not clear valid");
        rst_n=1; in_valid=1; in_instr=32'h11111111; in_pc=32'h80000000;
        in_rd=5; in_result=32'ha5; in_addr=32'h80000100;
        in_store_data=32'h12345678; in_reg_write=1; in_wb_sel=3;
        capture_check;
        in_valid=0; in_instr=32'h22222222; in_reg_write=0; in_wb_sel=0;
        capture_check;
        in_valid=1; in_instr=32'h33333333; in_pc=32'h80000008;
        in_rd=7; in_mem_write=1; in_store_data=32'hdeadbeef;
        capture_check;
        @(negedge clk); #1 rst_n=0; #1;
        if (mem_valid !== 0) $fatal(1, "async reset did not clear valid");
        $display("PASS: MEM+WB capture, bubble overwrite and reset (%0d captures)", checks);
        $finish;
    end
endmodule
