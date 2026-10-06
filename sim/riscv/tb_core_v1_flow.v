`timescale 1ns / 1ps
// D1.1 red-light test: three-stage valid/stall/redirect and single commit.
module tb_core_v1_flow;
    reg clk = 0, rst_n = 0;
    wire [31:0] imem_addr, dmem_addr, dmem_wdata;
    reg [31:0] imem_rdata;
    wire [31:0] dmem_rdata;
    wire [3:0] dmem_be;
    wire dmem_we;
    reg [31:0] imem [0:8191];
    reg [31:0] dmem [0:8191];
    integer i, cycles = 0, stalls = 0, redirects = 0;
    integer store0 = 0, store4 = 0, errors = 0;

    always #5 clk = ~clk;
    always @(posedge clk) imem_rdata <= imem[imem_addr[14:2]];
    assign dmem_rdata = dmem[dmem_addr[14:2]];
    always @(posedge clk) begin
        if (rst_n) begin
            cycles = cycles + 1;
            if (dut.front_stall) stalls = stalls + 1;
            if (dut.redirect) redirects = redirects + 1;
            if (dmem_we) begin
                if (dmem_be[0]) dmem[dmem_addr[14:2]][7:0] <= dmem_wdata[7:0];
                if (dmem_be[1]) dmem[dmem_addr[14:2]][15:8] <= dmem_wdata[15:8];
                if (dmem_be[2]) dmem[dmem_addr[14:2]][23:16] <= dmem_wdata[23:16];
                if (dmem_be[3]) dmem[dmem_addr[14:2]][31:24] <= dmem_wdata[31:24];
                if (dmem_addr == 0) store0 = store0 + 1;
                if (dmem_addr == 4) store4 = store4 + 1;
            end
        end
    end

    core_top #(.ENABLE_FORWARDING(1'b1)) dut (
        .clk(clk), .rst_n(rst_n), .imem_addr(imem_addr),
        .imem_rdata(imem_rdata), .dmem_addr(dmem_addr),
        .dmem_wdata(dmem_wdata), .dmem_be(dmem_be), .dmem_we(dmem_we),
        .dmem_rdata(dmem_rdata)
    );

    initial begin
        imem_rdata = 32'h00000013;
        for (i = 0; i < 8192; i = i + 1) begin
            imem[i] = 32'h00000013;
            dmem[i] = 0;
        end
        imem[0] = 32'h00500093; // addi x1,x0,5
        imem[1] = 32'h00308113; // addi x2,x1,3: ALU RAW
        imem[2] = 32'h00202023; // sw x2,0(x0): forwarded store data
        imem[3] = 32'h00002183; // lw x3,0(x0)
        imem[4] = 32'h00218233; // add x4,x3,x2: load-use
        imem[5] = 32'h00020463; // beq x4,x0,+8: not taken
        imem[6] = 32'h00420463; // beq x4,x4,+8: taken
        imem[7] = 32'h06300293; // wrong path: must flush
        imem[8] = 32'h00402223; // sw x4,4(x0)

        repeat (4) @(posedge clk);
        #1;
        if (dut.mem_valid !== 1'b0) begin
            $display("FAIL: mem_valid must clear during reset"); errors = errors + 1;
        end
        rst_n = 1;
        while ((store4 == 0) && (cycles < 80)) @(posedge clk);
        @(posedge clk); #1;
        if (store0 != 1 || dmem[0] !== 32'd8) begin
            $display("FAIL: first store count/value %0d/%0d", store0, dmem[0]); errors = errors + 1;
        end
        if (store4 != 1 || dmem[1] !== 32'd16) begin
            $display("FAIL: final store count/value %0d/%0d", store4, dmem[1]); errors = errors + 1;
        end
        if (stalls != 1) begin
            $display("FAIL: load-use stalls expected 1 got %0d", stalls); errors = errors + 1;
        end
        if (redirects != 1) begin
            $display("FAIL: redirects expected 1 got %0d", redirects); errors = errors + 1;
        end
        if (errors == 0)
            $display("PASS: v1 flow reset/RAW/load-use/branch/store cycles=%0d", cycles);
        else
            $fatal(1, "FAIL: v1 flow errors=%0d", errors);
        $finish;
    end
endmodule
