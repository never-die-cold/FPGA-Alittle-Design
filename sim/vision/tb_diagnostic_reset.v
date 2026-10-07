`timescale 1ns/1ps
module tb_diagnostic_reset;
    reg clk=0,rst=0,vs=0,de=0;
    wire ov,od,nv,nd;
    wire [23:0] rgb,nrgb;
    integer pixels=0;
    reg allow=0;
    always #5 clk=~clk;
    diagnostic_display #(.WIDTH(4),.H_TOTAL(16)) positive(
        .clk(clk),.rst_n(rst),.raw_vs(vs),.raw_hs(1'b0),.raw_de(de),.raw_rgb(24'h13579b),
        .diagnostic_en(1'b0),.frame_epoch(1'b0),.processed_vs(1'b0),.processed_de(1'b0),.processed_y(8'b0),
        .video_vs(ov),.video_de(od),.video_rgb(rgb));
    diagnostic_display #(.WIDTH(4),.H_TOTAL(16),.VS_POL(0)) negative(
        .clk(clk),.rst_n(rst),.raw_vs(!vs),.raw_hs(1'b0),.raw_de(de),.raw_rgb(24'h13579b),
        .diagnostic_en(1'b0),.frame_epoch(1'b0),.processed_vs(1'b0),.processed_de(1'b0),.processed_y(8'b0),
        .video_vs(nv),.video_de(nd),.video_rgb(nrgb));
    always @(posedge clk) begin
        #1;
        if(ov!==!nv || od!==nd || rgb!==nrgb) $fatal(1,"FAIL: VS polarity/reset outputs");
        if(od) begin
            if(!allow || rgb!==24'h13579b) $fatal(1,"FAIL: partial frame leaked");
            pixels=pixels+1;
        end
    end
    task full_frame;
        begin
            allow=1;vs=1;repeat(32) @(negedge clk);vs=0;
            repeat(16) @(negedge clk);de=1;repeat(4) @(negedge clk);de=0;
            repeat(80) @(negedge clk);
        end
    endtask
    initial begin
        repeat(3) @(negedge clk);rst=1;
        // Release reset halfway through active video: no source VS observed.
        de=1;repeat(100) @(negedge clk);de=0;repeat(80) @(negedge clk);
        full_frame;
        if(pixels!=4) $fatal(1,"FAIL: first full frame count %0d",pixels);
        de=1;repeat(5) @(negedge clk);rst=0;allow=0;
        repeat(3) @(negedge clk);rst=1;repeat(100) @(negedge clk);de=0;
        repeat(80) @(negedge clk);full_frame;
        if(pixels!=8) $fatal(1,"FAIL: recovery count %0d",pixels);
        $display("PASS: reset during active video, half-frame masking, next-frame recovery and both VS polarities");$finish;
    end
endmodule
