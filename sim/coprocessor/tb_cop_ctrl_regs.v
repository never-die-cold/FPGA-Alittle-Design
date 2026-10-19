`timescale 1ns/1ps
module tb_cop_ctrl_regs;
    reg clk=0,rst_n=0,we=0,busy=0,pending=0,done_evt=0,error_evt=0,timeout_evt=0;
    reg [31:0] addr=0,wdata=0; reg [3:0] be=4'hf;
    wire request,start,abort_cmd,soft_reset,write_done,done,error,timeout,result_valid,hit;
    wire [11:0] offset; wire [31:0] request_data,status,rdata;
    wire [3:0] result_index; wire [31:0] fw_counts,fw_decision;
    reg [3:0] before; integer checks=0;
    always #5 clk=~clk;
    cop_core_mmio_gate gate(.addr_i(addr),.wdata_i(wdata),.status_i(status),.be_i(be),.we_i(we),
        .fw_counts_i(fw_counts),.fw_decision_i(fw_decision),.result_index_i(result_index),
        .result_data_i(128'd0),.result_seq_i(32'd0),.cfg_applied_i(32'd0),.dma_bytes_i(32'd0),
        .work_order_i(32'h0a010101),.roi_count_i(5'd3),
        .busy_i(busy),.mailbox_pending_i(pending),.cop_hit_o(hit),.write_request_o(request),
        .write_offset_o(offset),.write_data_o(request_data),.rdata_o(rdata));
    cop_ctrl_regs regs(.clk(clk),.rst_n(rst_n),.write_valid_i(request),.write_offset_i(offset),
        .write_data_i(request_data),.task_busy_i(busy),.task_done_i(done_evt),.task_error_i(error_evt),
        .task_timeout_i(timeout_evt),.ready_i(1'b1),.cfg_valid_i(1'b1),.model_valid_i(1'b1),
        .dma_busy_i(1'b0),.irq_pending_i(1'b0),.start_pulse_o(start),.abort_pulse_o(abort_cmd),
        .soft_reset_pulse_o(soft_reset),.write_done_o(write_done),
        .done_o(done),.error_o(error),.timeout_o(timeout),.result_valid_o(result_valid),
        .result_index_o(result_index),.fw_counts_o(fw_counts),.fw_decision_o(fw_decision),.status_o(status));
    task reject;
        input [31:0] a,d; input [3:0] b; input bz,p;
        begin before={done,error,timeout,result_valid}; addr=a; wdata=d; be=b; busy=bz; pending=p; we=1;
            @(posedge clk); #1; we=0;
            if(request || write_done || start || {done,error,timeout,result_valid}!==before) $fatal(1);
            checks=checks+1;
        end
    endtask
    initial begin
        repeat(2) @(posedge clk); rst_n=1;
        done_evt=1; error_evt=1; timeout_evt=1; @(posedge clk); #1;
        done_evt=0; error_evt=0; timeout_evt=0;
        reject(32'h8001000c,1,4'b0011,0,0);
        reject(32'h8001000d,1,4'b1111,0,0);
        reject(32'h8001100c,1,4'b1111,0,0);
        reject(32'h80010010,1,4'b1111,0,0);
        reject(32'h8001000c,1,4'b1111,1,0);
        reject(32'h8001000c,1,4'b1111,0,1);
        addr=32'h8001000c; wdata=32'h18; be=4'hf; busy=0; pending=0; we=1;
        @(posedge clk); #1; we=0; if(!write_done || done || error || timeout || result_valid) $fatal(1);
        wdata=1; we=1; @(posedge clk); #1; we=0; if(!start || !write_done) $fatal(1);
        @(posedge clk); #1; if(start || write_done) $fatal(1);
        busy=1; wdata=2; we=1; @(posedge clk); #1; we=0;
        if(!abort_cmd || !error) $fatal(1); busy=0;
        @(posedge clk); #1; if(abort_cmd) $fatal(1);
        wdata=4; we=1; @(posedge clk); #1; we=0; if(!soft_reset || done || error) $fatal(1);
        addr=32'h8001006c; wdata=15; we=1; @(posedge clk); #1; we=0;
        if(result_index!=15 || !write_done) $fatal(1);
        addr=32'h80010088; wdata=32'h00030201; we=1; @(posedge clk); #1; we=0;
        addr=32'h8001008c; wdata=32'ha5000002; we=1; @(posedge clk); #1; we=0;
        if(fw_counts!==32'h00030201 || fw_decision!==32'ha5000002) $fatal(1);
        addr=32'h80010088; we=0; #1; if(rdata!==32'h00030201) $fatal(1);
        $display("PASS: cop_ctrl_regs normal START/W1C and %0d full-state reject diffs",checks); $finish;
    end
endmodule
