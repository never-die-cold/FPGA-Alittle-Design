`timescale 1ns/1ps
module tb_cop_multitarget_commit;
    reg clk=0,rst_n=0,start=0,eng_done=0;
    reg [23:0] logits=0;
    reg [127:0] memory[0:2];
    integer delay_count=0,launched=0,writes=0,i,cycles=0;
    wire busy,done,eng_start,write_result;
    wire [3:0] index;
    wire [31:0] seq;
    wire [127:0] data;
    always #5 clk=~clk;
    cop_task_ctrl dut(.clk(clk),.rst_n(rst_n),.start_i(start),.abort_i(1'b0),
        .soft_reset_i(1'b0),.cfg_valid_i(1'b1),.model_valid_i(1'b1),.roi_valid_i(1'b1),
        .roi_count_i(5'd3),.engine_ready_i(1'b1),.engine_done_i(eng_done),
        .engine_error_i(1'b0),.engine_timeout_i(1'b0),.target_id_i({12'd0,index}),
        .result_class_i(2'd2),.result_margin_i(8'd12),.result_score_i(15'd1548),
        .result_low_conf_i(1'b0),.result_logits_i(logits),.result_cycles_i(32'd100),
        .ready_o(),.busy_o(busy),.accepted_pulse_o(),.done_pulse_o(done),
        .error_pulse_o(),.timeout_pulse_o(),.engine_start_o(eng_start),
        .result_write_o(write_result),.result_index_o(index),.result_seq_o(seq),.result_data_o(data));
    // Exactly the synchronous write used in cop_top, without a post-edge delay.
    always @(posedge clk) begin
        if(rst_n && write_result) begin
            memory[index]<=data;
            writes=writes+1;
        end
        if(rst_n && eng_start) begin
            eng_done<=0;delay_count<=3;launched=launched+1;
        end else if(delay_count>0) begin
            delay_count<=delay_count-1;
            if(delay_count==1) begin eng_done<=1;logits<=24'h030200+launched;end
        end
    end
    initial begin
        for(i=0;i<3;i=i+1) memory[i]=0;
        repeat(3) @(negedge clk);rst_n=1;
        @(negedge clk);start=1;@(negedge clk);start=0;
        while(!done && cycles<100) begin @(negedge clk);cycles=cycles+1;end
        repeat(2) @(negedge clk);
        if(cycles>=100 || seq!=1 || busy || writes!=3 || launched!=3) $fatal(1,"job completion");
        for(i=0;i<3;i=i+1) begin
            if(memory[i][15:0]!=i || memory[i][24]!==1'b1 || memory[i][55:32]!==24'h030201+i)
                $fatal(1,"result slot %0d wrong: %h",i,memory[i]);
        end
        $display("PASS: three distinct ROI results committed once in matching slots 0/1/2");
        $finish;
    end
endmodule
