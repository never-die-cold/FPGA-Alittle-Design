`timescale 1ns/1ps
module tb_if_stage;
    reg clk=0, rst_n=0, stall=0, flush=0;
    reg [31:0] pc=32'h80000000, imem_rdata=32'h024185b3;
    wire [31:0] instr, pc_id;
    wire instr_valid;
    integer checks=0;
    if_stage dut (.clk(clk), .rst_n(rst_n), .pc(pc),
        .imem_rdata(imem_rdata), .stall(stall), .flush(flush),
        .instr(instr), .instr_valid(instr_valid), .pc_id(pc_id));
    always #5 clk=~clk;
    task check;
        input ok;
        begin
            checks=checks+1;
            if (ok !== 1'b1) $fatal(1,"FAIL: IF boundary case %0d",checks);
        end
    endtask
    task tick;
        begin @(posedge clk); #1; end
    endtask
    initial begin
        tick; check(!instr_valid); // Raw M payload is permitted in a reset bubble.
        @(negedge clk); rst_n=1;
        tick; check(instr_valid && instr==32'h024185b3 && pc_id==pc);
        // Start holding the original M, then change incoming BRAM payload.
        @(negedge clk); stall=1; tick;
        @(negedge clk); imem_rdata=32'h00a02223; pc=32'h80000004;
        tick; check(instr_valid && instr==32'h024185b3 && pc_id==32'h80000000);
        repeat (3) begin
            @(negedge clk); imem_rdata=imem_rdata+32'd4; tick;
            check(instr_valid && instr==32'h024185b3 && pc_id==32'h80000000);
        end
        // Removing stall must not release held instruction before the sampling edge.
        @(negedge clk); stall=0; imem_rdata=32'h0000006f; #1;
        check(instr==32'h024185b3); tick;
        check(instr_valid && instr==32'h0000006f && pc_id==pc);
        // Flush carries raw store/M/JAL payload with valid=0, not a NOP mux.
        @(negedge clk); flush=1; imem_rdata=32'h00a02223; tick;
        check(!instr_valid && instr==32'h00a02223);
        @(negedge clk); stall=1; tick;
        @(negedge clk); imem_rdata=32'h024185b3; tick;
        check(!instr_valid && instr==32'h00a02223);
        @(negedge clk); stall=0; flush=0; tick;
        check(instr_valid && instr==32'h024185b3);
        @(negedge clk); rst_n=0; #1; check(!instr_valid);
        $display("PASS: IF valid-only flush, hold/release and reset (%0d cases)",checks);
        $finish;
    end
endmodule
