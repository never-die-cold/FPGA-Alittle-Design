`timescale 1ns/1ps
module tb_raster_delay;
    reg clk=0,rst=0;
    reg [7:0] data=0;
    wire [7:0] out;
    wire valid;
    integer i;
    always #5 clk=~clk;
    raster_delay #(.WIDTH(8),.DEPTH(7)) dut(clk,rst,data,out,valid);
    task run;
        begin
            for(i=0;i<40;i=i+1) begin
                data=i;
                @(posedge clk);#1;
                if(valid!==(i>=7)) $fatal(1,"FAIL: delay warmup %0d",i);
                if(valid && out!==i-7) $fatal(1,"FAIL: delay wrap %0d %0d",i,out);
                @(negedge clk);
            end
        end
    endtask
    initial begin
        repeat(2) @(negedge clk);rst=1;run;
        @(negedge clk);rst=0;@(negedge clk);rst=1;run;
        $display("PASS: circular raster RAM delay, wrap, validity and reset");$finish;
    end
endmodule
