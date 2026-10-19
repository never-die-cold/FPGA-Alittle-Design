`timescale 1ns/1ps
module tb_cop_task_ctrl;
    reg clk=0,rst_n=0,start=0,abort_cmd=0,soft_reset=0,engine_ready=0,engine_done=0;
    wire ready,busy,done,error,timeout,engine_start,result_write; wire [3:0] index;
    wire [31:0] seq; wire [127:0] result;
    always #5 clk=~clk;
    cop_task_ctrl dut(.clk(clk),.rst_n(rst_n),.start_i(start),.abort_i(abort_cmd),
        .soft_reset_i(soft_reset),.cfg_valid_i(1'b1),
        .model_valid_i(1'b1),.roi_valid_i(1'b1),.roi_count_i(5'd1),.engine_ready_i(engine_ready),
        .engine_done_i(engine_done),.engine_error_i(1'b0),.engine_timeout_i(1'b0),
        .target_id_i(16'h1234),.result_class_i(2'd2),.result_margin_i(8'd2),
        .result_score_i(15'd258),.result_low_conf_i(1'b1),.result_logits_i(24'h04fd02),
        .result_cycles_i(32'd472593),.ready_o(ready),.busy_o(busy),.done_pulse_o(done),
        .error_pulse_o(error),.timeout_pulse_o(timeout),.engine_start_o(engine_start),
        .result_write_o(result_write),.result_index_o(index),.result_seq_o(seq),.result_data_o(result));
    initial begin
        repeat(2) @(posedge clk); rst_n=1; if(!ready) $fatal(1);
        @(negedge clk); start=1; @(negedge clk); start=0; engine_ready=1;
        @(posedge clk); #1; if(!engine_start || !busy) $fatal(1); engine_ready=0;
        @(negedge clk); engine_done=1; @(posedge clk); #1; engine_done=0;
        if(!done || busy || !result_write || seq!=1 || index!=0) $fatal(1);
        if(result[15:0]!==16'h1234 || result[23:16]!==8'd2 || result[55:32]!==24'h04fd02 ||
           result[63:56]!==8'd2 || result[78:64]!==15'd258 || result[127:96]!==32'd472593) $fatal(1);
        @(negedge clk); start=1; engine_ready=1; @(negedge clk); start=0;
        @(posedge clk); #1; engine_ready=0; abort_cmd=1;
        @(posedge clk); #1; abort_cmd=0; if(busy || !error) $fatal(1);
        soft_reset=1; @(posedge clk); #1; soft_reset=0; if(seq || busy) $fatal(1);
        $display("PASS: cop_task_ctrl commits result, aborts and soft-resets"); $finish;
    end
    initial begin #2000; $fatal(1,"task timeout"); end
endmodule
