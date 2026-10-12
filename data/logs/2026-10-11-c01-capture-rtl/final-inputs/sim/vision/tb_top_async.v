`timescale 1ns/1ps
module tb_top_async;
    reg clk=0,aclk=0,rst_n=0,vs=0,av=0,wv=0,br=0,arv=0,rr=0;
    reg [6:0] aa=0,ra=0;
    reg [31:0] wd=0;
    wire awr,wr,bv,arr,rv;
    wire [1:0] bp,rp;
    wire [31:0] rd;
    vision_top #(.DW(8),.DH(4),.NLINES(8)) dut(
        .clk(clk),.s_axi_aclk(aclk),.rst_n(rst_n),.axi_rst_n(rst_n),.in_vs(vs),.in_hs(1'b0),.in_de(1'b0),.in_rgb(24'b0),
        .awvalid(av),.awready(awr),.awaddr(aa),.wvalid(wv),.wready(wr),.wdata(wd),.wstrb(4'hf),
        .bvalid(bv),.bready(br),.bresp(bp),.arvalid(arv),.arready(arr),.araddr(ra),
        .rvalid(rv),.rready(rr),.rdata(rd),.rresp(rp),.cop_ready(1'b1));
    always #7 clk=~clk;
    always #5 aclk=~aclk;
    task write;
        input [6:0] addr;
        input [31:0] value;
        input [1:0] response;
        begin
            @(negedge aclk);aa=addr;wd=value;av=1;wv=1;br=1;
            @(negedge aclk);av=0;wv=0;
            if(!bv || bp!==response) $fatal(1,"FAIL: AXI config response %b expected %b",bp,response);
            @(negedge aclk);br=0;
        end
    endtask
    task read;
        input [6:0] addr;
        input [31:0] expected;
        begin
            @(negedge aclk);ra=addr;arv=1;
            @(negedge aclk);arv=0;
            if(!rv || rd!==expected) $fatal(1,"FAIL: status %h expected %h",rd,expected);
            rr=1;@(negedge aclk);rr=0;
        end
    endtask
    task frame;
        begin @(negedge clk);vs=1;@(negedge clk);vs=0;end
    endtask
    initial begin
        repeat(5) @(negedge aclk);rst_n=1;
        repeat(4) @(negedge aclk);
        write(0,9,0);write(4,100,0);write(8,200,0);
        frame;
        if(dut.active_cfg!==0) $fatal(1,"FAIL: staging applied without commit");
        write(44,1,0);repeat(5) @(negedge aclk);read(44,1);
        write(4,300,0);write(8,400,0);write(44,1,2);
        frame;
        if(dut.active_cfg[32+:32]!=100 || dut.active_cfg[64+:32]!=200 || !dut.t_sobel)
            $fatal(1,"FAIL: bundle mixed or applied one frame late");
        repeat(8) @(negedge aclk);read(44,0);read(48,1);
        write(0,0,0);write(44,1,0);repeat(5) @(negedge aclk);frame;
        if(dut.active_cfg[32+:32]!=300 || dut.active_cfg[64+:32]!=400 || dut.t_sobel)
            $fatal(1,"FAIL: second bundle incorrect");
        repeat(8) @(negedge aclk);read(48,2);
        $display("PASS: top async config staging, busy SLVERR, atomic frame apply, status epoch");$finish;
    end
    initial begin #20000;$fatal(1,"FAIL: async top timeout");end
endmodule
