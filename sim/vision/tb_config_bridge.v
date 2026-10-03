`timescale 1ns/1ps
module tb_config_bridge;
    reg aclk=0,pclk=0,rst_n=0,commit=0,vs=0;
    reg [351:0] staged=0;
    wire busy;
    wire [31:0] applied,id;
    wire [351:0] active;
    config_bridge dut(.src_clk(aclk),.dst_clk(pclk),.rst_n(rst_n),
        .src_commit(commit),.src_data(staged),.dst_frame(vs),
        .src_busy(busy),.src_applied(applied),.dst_data(active),.dst_id(id));
    always #5 aclk=~aclk;
    always #7 pclk=~pclk;
    task send;
        input [31:0] value;
        begin
            @(negedge aclk);staged={11{value}};commit=1;
            @(negedge aclk);commit=0;staged={11{32'hdeadbeef}};
        end
    endtask
    task frame;
        begin @(negedge pclk);vs=1;@(negedge pclk);vs=0;end
    endtask
    initial begin
        repeat(4) @(negedge aclk);rst_n=1;
        repeat(4) @(negedge aclk);
        send(32'h11223344);
        repeat(10) @(negedge aclk);
        if(!busy || active!==0) $fatal(1,"FAIL: early application");
        send(32'h55667788); // busy 时不得覆盖在途快照
        frame;
        if(active!=={11{32'h11223344}} || id!=1) $fatal(1,"FAIL: incoherent first bundle");
        repeat(6) @(negedge aclk);
        if(busy || applied!=1) $fatal(1,"FAIL: no first acknowledgment");
        send(32'h12345678);
        frame; // 请求可能未同步，允许本帧不应用
        repeat(10) @(negedge pclk);frame;
        if(active!=={11{32'h12345678}} || id!=2) $fatal(1,"FAIL: second bundle");
        repeat(6) @(negedge aclk);
        if(busy || applied!=2) $fatal(1,"FAIL: second acknowledgment");
        send(1);rst_n=0;repeat(3) @(negedge aclk);rst_n=1;
        repeat(5) @(negedge pclk);frame;
        if(busy || active!==0 || id!=0) $fatal(1,"FAIL: reset in flight");
        $display("PASS: config CDC async clocks, atomic bundle, busy reject, frame apply, ack, reset");$finish;
    end
    initial begin #10000;$fatal(1,"FAIL: CDC timeout");end
endmodule
