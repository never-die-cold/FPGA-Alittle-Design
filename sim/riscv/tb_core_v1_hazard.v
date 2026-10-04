`timescale 1ns/1ps
module tb_core_v1_hazard;
    parameter [0:0] ENABLE_FORWARDING = 1'b1;
    reg clk = 0, rst_n = 0;
    wire [31:0] imem_addr, dmem_addr, dmem_wdata;
    reg [31:0] imem_rdata;
    wire [31:0] dmem_rdata;
    wire [3:0] dmem_be;
    wire dmem_we;
    reg [31:0] imem [0:8191], dmem [0:8191];
    reg expect_flush = 0;
    integer i, cycles = 0, branch_stalls = 0, redirects = 0;
    integer flush_checks = 0, x6_writes = 0;
    integer store0 = 0, store8 = 0, store12 = 0, errors = 0;

    always #5 clk = ~clk;
    always @(posedge clk) imem_rdata <= imem[imem_addr[14:2]];
    assign dmem_rdata = dmem[dmem_addr[14:2]];
    always @(posedge clk) if (rst_n) begin
        cycles = cycles + 1;
        if (dut.redirect && dut.front_stall) begin
            $display("FAIL: redirect during front_stall"); errors = errors + 1;
        end
        if ((dut.instr == 32'h00500093) && dut.data_stall) begin
            $display("FAIL: x0 fake RAW stalled"); errors = errors + 1;
        end
        if ((dut.instr == 32'h00138463) && dut.data_stall) begin
            branch_stalls = branch_stalls + 1;
            if (dut.redirect || dut.mem_in_valid) begin
                $display("FAIL: load-branch accepted or redirected while stalled"); errors = errors + 1;
            end
        end
        if (expect_flush) begin
            flush_checks = flush_checks + 1;
            if (dut.instr_valid !== 1'b0) begin
                $display("FAIL: redirect did not invalidate young slot"); errors = errors + 1;
            end
            expect_flush = 0;
        end
        if (dut.redirect) begin redirects = redirects + 1; expect_flush = 1; end
        if (dut.rf_we && (dut.mem_rd == 5'd6)) x6_writes = x6_writes + 1;
        if (dmem_we) begin
            if (dmem_be[0]) dmem[dmem_addr[14:2]][7:0] <= dmem_wdata[7:0];
            if (dmem_be[1]) dmem[dmem_addr[14:2]][15:8] <= dmem_wdata[15:8];
            if (dmem_be[2]) dmem[dmem_addr[14:2]][23:16] <= dmem_wdata[23:16];
            if (dmem_be[3]) dmem[dmem_addr[14:2]][31:24] <= dmem_wdata[31:24];
            if (dmem_addr == 0) store0 = store0 + 1;
            if (dmem_addr == 8) store8 = store8 + 1;
            if (dmem_addr == 12) store12 = store12 + 1;
        end
    end

    core_top #(.ENABLE_FORWARDING(ENABLE_FORWARDING)) dut (
        .clk(clk), .rst_n(rst_n), .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata), .dmem_be(dmem_be),
        .dmem_we(dmem_we), .dmem_rdata(dmem_rdata)
    );

    initial begin
        imem_rdata = 32'h00000013;
        for (i = 0; i < 8192; i = i + 1) begin imem[i] = 32'h00000013; dmem[i] = 0; end
        dmem[1] = 5;
        imem[0] = 32'h00700013; // addi x0,x0,7: must not create RAW
        imem[1] = 32'h00500093; // addi x1,x0,5
        imem[2] = 32'h00300293; // addi x5,x0,3
        imem[3] = 32'h00528333; // add x6,x5,x5: both sources depend on x5
        imem[4] = 32'h00602023; // sw x6,0(x0)
        imem[5] = 32'h00402383; // lw x7,4(x0)
        imem[6] = 32'h00138463; // beq x7,x1,+8: stall once, then take
        imem[7] = 32'h00102423; // wrong path: sw x1,8(x0)
        imem[8] = 32'h00602623; // target: sw x6,12(x0)
        repeat (4) @(posedge clk); rst_n = 1;
        while ((store12 == 0) && (cycles < 100)) @(posedge clk);
        @(posedge clk); #1;
        if (branch_stalls != 1) begin $display("FAIL: branch stalls=%0d", branch_stalls); errors = errors + 1; end
        if (redirects != 1 || flush_checks != 1) begin
            $display("FAIL: redirects/flushes=%0d/%0d", redirects, flush_checks); errors = errors + 1;
        end
        if (x6_writes != 1) begin $display("FAIL: x6 writes=%0d", x6_writes); errors = errors + 1; end
        if (store0 != 1 || store8 != 0 || store12 != 1 || dmem[0] !== 6 || dmem[2] !== 0 || dmem[3] !== 6) begin
            $display("FAIL: stores=%0d/%0d/%0d data=%0d/%0d/%0d", store0, store8, store12, dmem[0], dmem[2], dmem[3]); errors = errors + 1;
        end
        if (errors == 0) $display("PASS: v1 hazard mode=%0d cycles=%0d", ENABLE_FORWARDING, cycles);
        else $fatal(1, "FAIL: v1 hazard errors=%0d", errors);
        $finish;
    end
endmodule
