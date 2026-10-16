`timescale 1ns/1ps
module tb_capture_stream_monitor;
    reg clk=0, rst_n=0, locked=0, fault=0;
    reg valid=0, ready=1, sof=0, eol=0;
    wire active, complete;
    wire [31:0] seq, rejected, epoch;
    integer pulses=0, stalls;
    always #5 clk=~clk;
    capture_stream_monitor #(.WIDTH(4),.HEIGHT(3)) dut(
        .clk(clk),.rst_n(rst_n),.locked(locked),.fault(fault),
        .tvalid(valid),.tready(ready),.tuser(sof),.tlast(eol),
        .active(active),.stream_seq(seq),.rejected_frames(rejected),
        .error_epoch(epoch),.frame_complete(complete));
    always @(negedge clk) if(complete) pulses=pulses+1;
    task check;
        input condition; input [511:0] label;
        begin if(!condition) begin $display("FAIL: %0s",label); $fatal(1); end end
    endtask
    task beat;
        input s,l;
        begin @(negedge clk); valid=1; sof=s; eol=l;
              @(posedge clk); #1;
              @(negedge clk); valid=0; sof=0; eol=0; end
    endtask
    task frame;
        integer row,col;
        begin for(row=0;row<3;row=row+1) for(col=0;col<4;col=col+1)
            beat(row==0 && col==0,col==3); end
    endtask
    initial begin
        #2; rst_n=0; repeat(2) @(negedge clk); rst_n=1;
        beat(0,0); check(!active && seq==0,"ignore stream before SOF/unlocked");
        locked=1; frame(); check(seq==1 && epoch==0,"normal frame");
        @(negedge clk); valid=1; sof=1; ready=0;
        for(stalls=0;stalls<5;stalls=stalls+1) begin
            @(posedge clk); #1; check(!active && seq==1 && epoch==0,"stalled SOF cannot count");
        end
        @(negedge clk); ready=1; @(posedge clk); #1;
        @(negedge clk); valid=0; sof=0;
        beat(0,1); check(rejected==1 && epoch==1 && !active,"early EOL rejected");
        frame(); check(seq==2,"recover at next SOF");
        beat(1,0); beat(0,0); beat(0,0); beat(0,0);
        check(rejected==2 && epoch==2 && !active,"missing EOL rejected");
        beat(0,1); check(seq==2 && rejected==2,"drain orphan pixels");
        beat(1,0); frame();
        check(seq==3 && rejected==3 && epoch==3,"premature SOF rejects old frame and restarts");
        beat(1,0); fault=1; beat(0,0); fault=0;
        check(!active && seq==3 && rejected==4,"overflow invalidates active frame");
        beat(0,1); frame(); check(seq==4,"overflow recovery");
        beat(1,0); locked=0; @(posedge clk); #1;
        check(rejected==5 && !active,"lock loss rejects partial frame");
        repeat(4) @(negedge clk); check(rejected==5,"lock loss counted once");
        locked=1; frame(); check(seq==5,"lock recovery");
        // A fault coincident with the final accepted pixel must win.
        beat(1,0); beat(0,0); beat(0,0); beat(0,1);
        beat(0,0); beat(0,0); beat(0,0); beat(0,1);
        beat(0,0); beat(0,0); beat(0,0); fault=1; beat(0,1); fault=0;
        check(seq==5 && rejected==6 && !complete,"fault wins over completion");
        frame(); check(seq==6,"final recovery");
        @(negedge clk); rst_n=0; #1;
        check(seq==0 && rejected==0 && epoch==0 && !active,"reset clears status");
        check(pulses==6,"one completion pulse per valid frame");
        $display("PASS: capture stream geometry, stalls, faults, lock loss, SOF recovery and reset");
        $finish;
    end
    initial begin #100000; $display("FAIL: watchdog"); $fatal(1); end
endmodule
