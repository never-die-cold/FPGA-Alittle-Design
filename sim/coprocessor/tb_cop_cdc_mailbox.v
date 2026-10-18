`timescale 1ns/1ps
module tb_cop_cdc_mailbox;
    reg src_clk=0,dst_clk=0,rst_n=0,src_valid=0,dst_done=0;
    reg [11:0] src_offset; reg [31:0] src_data;
    wire pending,dst_valid; wire [11:0] dst_offset; wire [31:0] dst_data;
    integer deliveries=0;
    always #5 src_clk=~src_clk; always #7 dst_clk=~dst_clk;
    cop_cdc_mailbox dut(.src_clk(src_clk),.dst_clk(dst_clk),.rst_n(rst_n),.src_valid_i(src_valid),
        .src_offset_i(src_offset),.src_data_i(src_data),.src_pending_o(pending),.dst_valid_o(dst_valid),
        .dst_offset_o(dst_offset),.dst_data_o(dst_data),.dst_done_i(dst_done));
    always @(posedge dst_clk) if(dst_valid) deliveries=deliveries+1;
    task send;
        input [11:0] offset; input [31:0] data;
        begin @(negedge src_clk); src_offset=offset; src_data=data; src_valid=1;
            @(negedge src_clk); src_valid=0; end
    endtask
    initial begin
        src_offset=0; src_data=0; repeat(3) @(negedge src_clk); rst_n=1;
        send(12'h00c,32'h1); if(!pending) $fatal(1);
        send(12'h088,32'h11223344);
        wait(dst_valid); @(posedge dst_clk); #1;
        if(dst_offset!==12'h00c || dst_data!==32'h1 || deliveries!=1 || !pending) $fatal(1);
        repeat(3) @(posedge dst_clk); if(deliveries!=1 || !pending) $fatal(1);
        dst_done=1; @(posedge dst_clk); #1; dst_done=0;
        wait(!pending); repeat(2) @(posedge src_clk);
        if(deliveries!=1) $fatal(1);
        send(12'h088,32'h55667788); wait(dst_valid); @(posedge dst_clk); #1;
        if(dst_offset!==12'h088 || dst_data!==32'h55667788 || deliveries!=2) $fatal(1);
        dst_done=1; @(posedge dst_clk); #1; dst_done=0; wait(!pending);
        $display("PASS: cop_cdc_mailbox rejects pending overwrite and ACKs only after destination done");
        $finish;
    end
    initial begin #2000; $fatal(1,"mailbox timeout"); end
endmodule
