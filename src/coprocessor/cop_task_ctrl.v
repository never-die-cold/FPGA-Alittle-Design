`timescale 1ns/1ps
// Per-target launcher and ordered 16-byte result committer.
module cop_task_ctrl (
    input wire clk, rst_n, start_i, abort_i, soft_reset_i,
    input wire cfg_valid_i, model_valid_i, roi_valid_i,
    input wire [4:0] roi_count_i,
    input wire engine_ready_i, engine_done_i, engine_error_i, engine_timeout_i,
    input wire [15:0] target_id_i,
    input wire [1:0] result_class_i,
    input wire [7:0] result_margin_i,
    input wire [14:0] result_score_i,
    input wire result_low_conf_i,
    input wire [23:0] result_logits_i,
    input wire [31:0] result_cycles_i,
    output wire ready_o,
    output reg busy_o, done_pulse_o, error_pulse_o, timeout_pulse_o, engine_start_o,
    output reg result_write_o,
    output reg [3:0] result_index_o,
    output reg [31:0] result_seq_o,
    output wire [127:0] result_data_o
);
    localparam IDLE=0, LAUNCH=1, WAIT_ENGINE=2;
    reg [1:0] state; reg [4:0] count_snapshot;
    assign ready_o = !busy_o && cfg_valid_i && model_valid_i && roi_valid_i;
    assign result_data_o = {result_cycles_i,16'd0,1'b0,result_score_i,result_margin_i,
        result_logits_i,{5'd0,1'b0,result_low_conf_i,1'b1},{6'd0,result_class_i},target_id_i};
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            state<=IDLE; busy_o<=0; done_pulse_o<=0; error_pulse_o<=0;
            timeout_pulse_o<=0; engine_start_o<=0; result_write_o<=0;
            result_index_o<=0; result_seq_o<=0; count_snapshot<=0;
        end else begin
            done_pulse_o<=0; error_pulse_o<=0; timeout_pulse_o<=0;
            engine_start_o<=0; result_write_o<=0;
            if(soft_reset_i) begin
                state<=IDLE; busy_o<=0; result_index_o<=0; result_seq_o<=0;
            end else if(abort_i && busy_o) begin
                state<=IDLE; busy_o<=0; error_pulse_o<=1;
            end else case(state)
                IDLE: if(start_i && ready_o && roi_count_i>=1 && roi_count_i<=16) begin
                    busy_o<=1; result_index_o<=0; count_snapshot<=roi_count_i; state<=LAUNCH;
                end
                LAUNCH: if(engine_ready_i) begin engine_start_o<=1; state<=WAIT_ENGINE; end
                WAIT_ENGINE: if(engine_error_i) begin
                    busy_o<=0; error_pulse_o<=1; timeout_pulse_o<=engine_timeout_i; state<=IDLE;
                end else if(engine_done_i) begin
                    result_write_o<=1; result_seq_o<=result_seq_o+1;
                    if(result_index_o+1==count_snapshot) begin busy_o<=0; done_pulse_o<=1; state<=IDLE; end
                    else begin result_index_o<=result_index_o+1'b1; state<=LAUNCH; end
                end
                default: begin busy_o<=0; error_pulse_o<=1; state<=IDLE; end
            endcase
        end
    end
endmodule
