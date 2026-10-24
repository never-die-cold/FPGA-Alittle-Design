`timescale 1ns/1ps
// Cop-domain task status and RISC-V command subset; CDC is external.
module cop_ctrl_regs (
    input wire clk, rst_n,
    input wire write_valid_i,
    input wire [11:0] write_offset_i,
    input wire [31:0] write_data_i,
    input wire task_busy_i, task_accepted_i, task_done_i, task_error_i, task_timeout_i,
    input wire cfg_valid_i, model_valid_i, dma_busy_i, irq_pending_i,
    output reg start_pulse_o, abort_pulse_o, soft_reset_pulse_o, write_done_o,
    output reg accepted_o, done_o, error_o, timeout_o, result_valid_o,
    output reg [31:0] error_code_o,
    output reg [3:0] result_index_o,
    output reg [31:0] fw_counts_o, fw_decision_o,
    output wire unconsumed_o,
    output wire [31:0] status_o
);
    localparam ERR_TASK=32'd1, ERR_ABORTED=32'd12, ERR_WATCHDOG=32'd13;
    assign unconsumed_o=done_o|error_o|timeout_o;
    assign status_o = {19'd0,unconsumed_o,accepted_o,1'b0,irq_pending_i,dma_busy_i,result_valid_o,
        model_valid_i,cfg_valid_i,timeout_o,error_o,done_o,task_busy_i,
        !task_busy_i};
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            start_pulse_o<=0; abort_pulse_o<=0; soft_reset_pulse_o<=0; write_done_o<=0; done_o<=0;
            accepted_o<=0; error_o<=0; timeout_o<=0; result_valid_o<=0; error_code_o<=0;
            result_index_o<=0; fw_counts_o<=0; fw_decision_o<=0;
        end else begin
            start_pulse_o<=0; abort_pulse_o<=0; soft_reset_pulse_o<=0; write_done_o<=0;
            if(write_valid_i) begin
                write_done_o<=1;
                if(write_offset_i==12'h00c) begin
                    if(write_data_i[0] && !task_busy_i && !unconsumed_o) start_pulse_o<=1;
                    if(write_data_i[1]) begin
                        abort_pulse_o<=1; done_o<=0; error_o<=1; timeout_o<=0;
                        result_valid_o<=0; error_code_o<=ERR_ABORTED;
                    end
                    if(write_data_i[2]) soft_reset_pulse_o<=1;
                    if(write_data_i[6] && unconsumed_o && !task_busy_i) begin
                        accepted_o<=0; done_o<=0; error_o<=0; timeout_o<=0;
                        result_valid_o<=0; error_code_o<=0;
                    end
                end else if(write_offset_i==12'h06c) result_index_o<=write_data_i[3:0];
                else if(write_offset_i==12'h088) fw_counts_o<=write_data_i;
                else if(write_offset_i==12'h08c) fw_decision_o<=write_data_i;
            end
            if(task_accepted_i) accepted_o<=1;
            if(task_timeout_i && !unconsumed_o) begin
                done_o<=0; error_o<=0; timeout_o<=1; result_valid_o<=0; error_code_o<=ERR_WATCHDOG;
            end else if(task_error_i && !unconsumed_o) begin
                done_o<=0; error_o<=1; timeout_o<=0; result_valid_o<=0; error_code_o<=ERR_TASK;
            end else if(task_done_i && !unconsumed_o) begin
                done_o<=1; error_o<=0; timeout_o<=0; result_valid_o<=1;
            end
        end
    end
endmodule
