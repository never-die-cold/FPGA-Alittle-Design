`timescale 1ns/1ps
module tb_diagnostic_rows;
    reg clk=0,rst=0,vs=0,de=0,epoch=0,re=0;
    reg [7:0] y=0;
    reg [15:0] row=0;
    reg [2:0] x=0;
    wire [7:0] out;
    wire valid;
    integer r,c;
    always #5 clk=~clk;
    diagnostic_rows #(.WIDTH(5)) dut(clk,rst,vs,de,epoch,y,row,x,re,out,valid);
    task check;
        input [15:0] rr;input [2:0] xx;input ee,vv;input [7:0] yy;
        begin
            @(negedge clk);row=rr;x=xx;re=ee;
            @(posedge clk);#1;
            if(valid!==vv || (vv && out!==yy)) $fatal(1,"FAIL: row tag/data %0d/%0d",rr,xx);
        end
    endtask
    initial begin
        repeat(2) @(negedge clk);rst=1;check(0,0,0,0,0);
        for(r=0;r<5;r=r+1) begin
            for(c=0;c<5;c=c+1) begin @(negedge clk);de=1;y=r*10+c;end
            @(negedge clk);de=0;
        end
        check(0,0,0,0,0); // slot zero has been replaced by row four
        check(4,4,0,1,44);check(3,2,0,1,32);check(3,2,1,0,0);
        @(negedge clk);vs=1;@(negedge clk);vs=0;
        check(3,2,0,0,0);
        @(negedge clk);rst=0;@(negedge clk);rst=1;
        check(4,4,0,0,0);
        $display("PASS: completed row storage, non-power-of-two width, overwrite/frame/reset rejection");$finish;
    end
endmodule
