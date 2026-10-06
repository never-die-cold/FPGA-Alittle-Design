`timescale 1ns / 1ps
// D1.2b: integrated byte/half/word stores and signed/unsigned loads.
module tb_core_v1_mem;
    reg clk = 0, rst_n = 0;
    reg [31:0] imem_rdata;
    wire [31:0] imem_addr, dmem_addr, dmem_wdata, dmem_rdata;
    wire [3:0] dmem_be;
    wire dmem_we;
    reg [31:0] imem [0:8191];
    reg [31:0] dmem [0:8191];
    integer i, writes = 0, errors = 0;

    always #5 clk = ~clk;
    always @(posedge clk) imem_rdata <= imem[imem_addr[14:2]];
    assign dmem_rdata = dmem[dmem_addr[14:2]];
    always @(posedge clk) if (dmem_we) begin
        writes = writes + 1;
        if (dmem_be[0]) dmem[dmem_addr[14:2]][7:0] <= dmem_wdata[7:0];
        if (dmem_be[1]) dmem[dmem_addr[14:2]][15:8] <= dmem_wdata[15:8];
        if (dmem_be[2]) dmem[dmem_addr[14:2]][23:16] <= dmem_wdata[23:16];
        if (dmem_be[3]) dmem[dmem_addr[14:2]][31:24] <= dmem_wdata[31:24];
    end

    core_top #(.ENABLE_FORWARDING(1'b1)) dut (
        .clk(clk), .rst_n(rst_n), .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata), .dmem_be(dmem_be),
        .dmem_we(dmem_we), .dmem_rdata(dmem_rdata)
    );

    task expect_word;
        input integer index; input [31:0] expected;
        begin
            if (dmem[index] !== expected) begin
                $display("FAIL: dmem[%0d] expected=%08x actual=%08x", index, expected, dmem[index]);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        imem_rdata = 32'h00000013;
        for (i = 0; i < 8192; i = i + 1) begin imem[i] = 32'h00000013; dmem[i] = 0; end
        dmem[0]  = 32'h80ff7f01;
        dmem[1]  = 32'h11223344;
        dmem[2]  = 32'h11223344;
        imem[0]  = 32'h05a00093; // addi x1,x0,0x5a
        imem[1]  = 32'h00100223; // sb x1,4(x0), lane 0
        imem[2]  = 32'h001003a3; // sb x1,7(x0), lane 3
        imem[3]  = 32'h7ab00113; // addi x2,x0,0x7ab
        imem[4]  = 32'h00201423; // sh x2,8(x0), lanes 1:0
        imem[5]  = 32'h00201523; // sh x2,10(x0), lanes 3:2
        imem[6]  = 32'hfff00193; // addi x3,x0,-1
        imem[7]  = 32'h00302623; // sw x3,12(x0)
        imem[8]  = 32'h00000203; // lb x4,0(x0)
        imem[9]  = 32'h00204283; // lbu x5,2(x0)
        imem[10] = 32'h00300303; // lb x6,3(x0)
        imem[11] = 32'h00001383; // lh x7,0(x0)
        imem[12] = 32'h00205403; // lhu x8,2(x0)
        imem[13] = 32'h00002483; // lw x9,0(x0)
        imem[14] = 32'h00402823; // sw x4,16(x0)
        imem[15] = 32'h00502a23; // sw x5,20(x0)
        imem[16] = 32'h00602c23; // sw x6,24(x0)
        imem[17] = 32'h00702e23; // sw x7,28(x0)
        imem[18] = 32'h02802023; // sw x8,32(x0)
        imem[19] = 32'h02902223; // sw x9,36(x0)

        repeat (4) @(posedge clk); #1;
        if (dmem_we !== 1'b0 || writes != 0) $fatal(1, "FAIL: reset allowed a store");
        rst_n = 1;
        repeat (120) @(posedge clk); #1;
        expect_word(0, 32'h80ff7f01); expect_word(1, 32'h5a22335a);
        expect_word(2, 32'h07ab07ab); expect_word(3, 32'hffffffff);
        expect_word(4, 32'h00000001); expect_word(5, 32'h000000ff);
        expect_word(6, 32'hffffff80); expect_word(7, 32'h00007f01);
        expect_word(8, 32'h000080ff); expect_word(9, 32'h80ff7f01);
        if (writes != 11) begin $display("FAIL: expected 11 stores got %0d", writes); errors = errors + 1; end
        if (errors == 0) $display("PASS: v1 byte/half/word memory path, writes=%0d", writes);
        else $fatal(1, "FAIL: v1 memory path errors=%0d", errors);
        $finish;
    end
endmodule
