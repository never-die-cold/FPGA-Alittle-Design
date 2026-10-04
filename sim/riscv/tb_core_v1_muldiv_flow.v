`timescale 1ns / 1ps
// D1.4/D2.2b: single M flow plus forwarding on/off RAW boundaries.
module tb_core_v1_muldiv_flow;
    parameter [0:0] ENABLE_FORWARDING = 1'b1;
    reg clk = 0, rst_n = 0;
    reg [31:0] imem_rdata;
    wire [31:0] imem_addr, dmem_addr, dmem_wdata;
    wire [3:0] dmem_be;
    wire dmem_we;
    reg [31:0] imem [0:8191];
    integer i, cycles = 0, starts = 0, busy_cycles = 0;
    integer dones = 0, x2_writes = 0, x3_writes = 0, x4_writes = 0;
    integer data_stalls = 0, pre_stalls = 0, post_stalls = 0, errors = 0;
    reg [31:0] held_pc;
    reg started = 0;

    always #5 clk = ~clk;
    always @(posedge clk) imem_rdata <= imem[imem_addr[14:2]];

    core_top #(.ENABLE_FORWARDING(ENABLE_FORWARDING)) dut (
        .clk(clk), .rst_n(rst_n), .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata), .dmem_be(dmem_be),
        .dmem_we(dmem_we), .dmem_rdata(32'd0)
    );

    always @(posedge clk) if (rst_n) begin
        cycles = cycles + 1;
        if (dut.muldiv_start) begin
            starts = starts + 1;
            held_pc = imem_addr;
            started = 1;
            if (!dut.front_stall) begin
                $display("FAIL: start cycle did not stall front end"); errors = errors + 1;
            end
        end
        if (dut.muldiv_busy) begin
            busy_cycles = busy_cycles + 1;
            if (!dut.front_stall) begin
                $display("FAIL: busy cycle released front end"); errors = errors + 1;
            end
            if (dut.mem_valid) begin
                $display("FAIL: MEM+WB did not drain during wait"); errors = errors + 1;
            end
        end
        if (started && dut.muldiv_wait && imem_addr !== held_pc) begin
            $display("FAIL: PC moved during muldiv wait"); errors = errors + 1;
        end
        if (dut.muldiv_done) begin
            dones = dones + 1;
            if (!dut.muldiv_pending) begin
                $display("FAIL: pending cleared before done acceptance"); errors = errors + 1;
            end
            if (dut.rf_we && dut.mem_rd == 5'd3) begin
                $display("FAIL: done cycle wrote x3 directly"); errors = errors + 1;
            end
        end
        if (dut.rf_we && dut.mem_rd == 5'd2) x2_writes = x2_writes + 1;
        if (dut.rf_we && dut.mem_rd == 5'd3) begin
            x3_writes = x3_writes + 1;
            if (dut.wb_data !== 32'd21) begin $display("FAIL: x3 data=%0d", dut.wb_data); errors = errors + 1; end
        end
        if (dut.rf_we && dut.mem_rd == 5'd4) begin
            x4_writes = x4_writes + 1;
            if (dut.wb_data !== 32'd22) begin $display("FAIL: x4 data=%0d", dut.wb_data); errors = errors + 1; end
        end
        if (dut.data_stall) begin
            data_stalls = data_stalls + 1;
            if (!started) pre_stalls = pre_stalls + 1;
            else post_stalls = post_stalls + 1;
            if (dut.muldiv_start || !dut.front_stall || dut.mem_in_valid) begin
                $display("FAIL: RAW stall leaked start/accept"); errors = errors + 1;
            end
        end
    end

    initial begin
        imem_rdata = 32'h00000013;
        for (i = 0; i < 8192; i = i + 1) imem[i] = 32'h00000013;
        imem[0] = 32'h00700093; // addi x1,x0,7
        imem[1] = 32'h00300113; // addi x2,x0,3: older producer
        imem[2] = 32'h022081b3; // mul x3,x1,x2
        imem[3] = 32'h00118213; // addi x4,x3,1: immediate M-result consumer
        repeat (4) @(posedge clk); rst_n = 1;
        repeat (100) @(posedge clk); #1;
        if (starts != 1) begin $display("FAIL: starts expected 1 got %0d", starts); errors = errors + 1; end
        if (busy_cycles != 32) begin $display("FAIL: busy cycles expected 32 got %0d", busy_cycles); errors = errors + 1; end
        if (dones != 1) begin $display("FAIL: done pulses expected 1 got %0d", dones); errors = errors + 1; end
        if (x2_writes != 1) begin $display("FAIL: old x2 commit expected 1 got %0d", x2_writes); errors = errors + 1; end
        if (x3_writes != 1) begin $display("FAIL: x3 writes expected 1 got %0d", x3_writes); errors = errors + 1; end
        if (x4_writes != 1) begin $display("FAIL: x4 writes expected 1 got %0d", x4_writes); errors = errors + 1; end
        if (ENABLE_FORWARDING && (data_stalls != 0 || pre_stalls != 0 || post_stalls != 0)) begin
            $display("FAIL: fwd stalls total/pre/post=%0d/%0d/%0d", data_stalls, pre_stalls, post_stalls); errors = errors + 1;
        end
        if (!ENABLE_FORWARDING && (data_stalls != 2 || pre_stalls != 1 || post_stalls != 1)) begin
            $display("FAIL: nofwd stalls total/pre/post=%0d/%0d/%0d", data_stalls, pre_stalls, post_stalls); errors = errors + 1;
        end
        if (errors == 0)
            $display("PASS: v1 muldiv mode=%0d start=%0d busy=%0d done=%0d x2/x3/x4=%0d/%0d/%0d stalls=%0d/%0d/%0d",
                     ENABLE_FORWARDING, starts, busy_cycles, dones, x2_writes, x3_writes, x4_writes,
                     data_stalls, pre_stalls, post_stalls);
        else $fatal(1, "FAIL: v1 muldiv flow errors=%0d", errors);
        $finish;
    end
endmodule
