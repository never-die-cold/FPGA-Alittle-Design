`timescale 1ns/1ps
// Compare observable PC/flush choices with the pre-optimization equations.
module tb_core_pc_control;
    reg clk=0, rst_n=0;
    reg valid, wait_data, wait_m, branch, taken, jump, prediction;
    reg [31:0] current_pc, instruction_pc, target, target_next;
    wire [31:0] imem_addr;
    integer kind, bits, n, checks=0;
    reg accept, resolve, miss, jump_event, correct_taken, redirect_ref;
    reg [31:0] recover_ref, fetch_ref, pc_ref;
    reg select_ref;
    core_top dut (.clk(clk), .rst_n(rst_n), .imem_addr(imem_addr),
        .imem_rdata(32'h00000013), .dmem_addr(), .dmem_wdata(),
        .dmem_be(), .dmem_we(), .dmem_rdata(32'd0));
    always #5 clk=~clk;
    initial begin
        force dut.instr_valid=valid;
        force dut.data_stall=wait_data;
        force dut.muldiv_wait=wait_m;
        force dut.branch_valid=branch;
        force dut.branch_taken=taken;
        force dut.jump_taken=jump;
        force dut.bp_predict_taken=prediction;
        force dut.pc=current_pc;
        force dut.pc_id=instruction_pc;
        force dut.redirect_target=target;
        force dut.branch_target=target;
        force dut.branch_target_next=target_next;
        for (n=0; n<8; n=n+1) begin
            // Include carry, wraparound and bit1 cases without assuming aligned PC.
            case (n)
                0: begin current_pc=32'h80000024; instruction_pc=32'h80000020; target=32'h80000010; end
                1: begin current_pc=32'hffffffff; instruction_pc=32'hfffffffc; target=32'hfffffffe; end
                default: begin current_pc=$random; instruction_pc=$random; target=$random; end
            endcase
            target_next=target+32'd4;
            for (kind=0; kind<3; kind=kind+1) begin
                branch=(kind==1); jump=(kind==2);
                for (bits=0; bits<32; bits=bits+1) begin
                    valid=bits[0]; wait_data=bits[1]; wait_m=bits[2];
                    taken=branch && bits[3]; prediction=bits[4]; #1;
                    accept=valid && !(wait_data || wait_m);
                    resolve=accept && branch;
                    miss=resolve && (prediction != taken);
                    jump_event=accept && jump;
                    correct_taken=resolve && prediction && !miss;
                    redirect_ref=jump_event || miss;
                    recover_ref=jump_event ? target : (taken ? target : instruction_pc+32'd4);
                    fetch_ref=redirect_ref ? recover_ref : (correct_taken ? target : current_pc);
                    select_ref=redirect_ref || correct_taken;
                    pc_ref=redirect_ref ? recover_ref : target+32'd4;
                    if (imem_addr !== fetch_ref || dut.flush !== redirect_ref ||
                        dut.pc_sel !== (select_ref ? 2'b01 : 2'b00) ||
                        (select_ref && dut.pc_target !== pc_ref) ||
                        dut.front_stall !== (wait_data || wait_m))
                        $fatal(1,"FAIL: PC control n/kind/bits=%0d/%0d/%0d",n,kind,bits);
                    checks=checks+1;
                end
            end
        end
        $display("PASS: PC control matches pre-optimization truth table (%0d cases)",checks);
        $finish;
    end
endmodule
