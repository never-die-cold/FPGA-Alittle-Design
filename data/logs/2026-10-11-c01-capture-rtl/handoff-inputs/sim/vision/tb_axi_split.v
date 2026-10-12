`timescale 1ns/1ps
module tb_axi_split;
    reg clk=0,rst_n=0,av=0,wv=0,br=0,rv=0,rr=0;
    reg [6:0] aa=0,ra=0;
    reg [31:0] wd=0;
    reg [3:0] ws=15;
    wire ar,wr,bv,ready,valid;
    wire [1:0] bp,rp;
    wire [31:0] rd;
    wire [511:0] flat;
    axi_regs dut(.clk(clk),.rst_n(rst_n),.awvalid(av),.awready(ar),.awaddr(aa),
        .wvalid(wv),.wready(wr),.wdata(wd),.wstrb(ws),.bvalid(bv),.bready(br),.bresp(bp),
        .arvalid(rv),.arready(ready),.araddr(ra),.rvalid(valid),.rready(rr),.rdata(rd),.rresp(rp),.regs_flat(flat),
        .cfg_busy(1'b0),.cfg_applied(32'b0));
    always #5 clk=~clk;
    task split_write;
        input integer data_first;
        input [31:0] value;
        begin
            @(negedge clk); aa=4;wd=value;
            if(data_first) wv=1; else av=1;
            @(negedge clk); av=0;wv=0; aa=40;wd=32'hdeadbeef;
            repeat(3) @(negedge clk);
            if(data_first) begin aa=4;av=1; end else begin wd=value;wv=1;end
            @(negedge clk);av=0;wv=0;
            if(!bv || flat[32+:32]!==value) $fatal(1,"FAIL: split AXI order=%0d bvalid=%b value=%h",data_first,bv,flat[32+:32]);
            repeat(3) begin
                @(negedge clk);
                if(!bv || ar || wr) $fatal(1,"FAIL: write response not held");
            end
            br=1;@(negedge clk);br=0;
        end
    endtask
    initial begin
        repeat(4) @(negedge clk);rst_n=1;
        split_write(0,32'h11223344);
        split_write(1,32'h55667788);
        @(negedge clk);ra=4;rv=1;
        @(negedge clk);rv=0;
        repeat(3) begin
            if(!valid || rd!==32'h55667788 || ready) $fatal(1,"FAIL: read not held");
            @(negedge clk);
        end
        rr=1;@(negedge clk);rr=0;
        $display("PASS: AXI AW-before-W/W-before-AW, response backpressure, captured payload");$finish;
    end
    initial begin #10000;$fatal(1,"FAIL: AXI timeout");end
endmodule
