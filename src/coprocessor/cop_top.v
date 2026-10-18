`timescale 1ns/1ps
// C03 integration top; data/config/compute ports are added in bounded J04 steps.
module cop_top #(
    parameter [31:0] COP_BASE = 32'h8001_0000
) (
    input wire core_clk, cop_clk, rst_n,
    input wire [31:0] core_addr_i, core_wdata_i,
    input wire [3:0] core_be_i,
    input wire core_we_i,
    output wire core_hit_o,
    output wire [31:0] core_rdata_o,
    input wire task_ready_i, task_busy_i, task_done_i, task_error_i, task_timeout_i,
    input wire cfg_valid_i, model_valid_i, dma_busy_i, irq_pending_i,
    output wire task_start_o,
    output wire [31:0] status_o, fw_counts_o, fw_decision_o,
    output wire [3:0] result_index_o
);
    wire core_request,mailbox_pending,command_valid,command_done;
    wire [11:0] core_offset,command_offset; wire [31:0] core_data,command_data;
    wire done_status,error_status,timeout_status,result_valid_status;
    cop_core_mmio_gate #(.COP_BASE(COP_BASE)) gate(
        .addr_i(core_addr_i),.wdata_i(core_wdata_i),.status_i(status_o),.be_i(core_be_i),
        .we_i(core_we_i),.busy_i(task_busy_i),.mailbox_pending_i(mailbox_pending),
        .fw_counts_i(fw_counts_o),.fw_decision_i(fw_decision_o),.result_index_i(result_index_o),
        .cop_hit_o(core_hit_o),.write_request_o(core_request),.write_offset_o(core_offset),
        .write_data_o(core_data),.rdata_o(core_rdata_o));
    cop_cdc_mailbox mailbox(.src_clk(core_clk),.dst_clk(cop_clk),.rst_n(rst_n),
        .src_valid_i(core_request),.src_offset_i(core_offset),.src_data_i(core_data),
        .src_pending_o(mailbox_pending),.dst_valid_o(command_valid),.dst_offset_o(command_offset),
        .dst_data_o(command_data),.dst_done_i(command_done));
    cop_ctrl_regs regs(.clk(cop_clk),.rst_n(rst_n),.write_valid_i(command_valid),
        .write_offset_i(command_offset),.write_data_i(command_data),.task_busy_i(task_busy_i),
        .task_done_i(task_done_i),.task_error_i(task_error_i),.task_timeout_i(task_timeout_i),
        .ready_i(task_ready_i),.cfg_valid_i(cfg_valid_i),.model_valid_i(model_valid_i),
        .dma_busy_i(dma_busy_i),.irq_pending_i(irq_pending_i),.start_pulse_o(task_start_o),
        .write_done_o(command_done),.done_o(done_status),.error_o(error_status),
        .timeout_o(timeout_status),.result_valid_o(result_valid_status),.result_index_o(result_index_o),
        .fw_counts_o(fw_counts_o),.fw_decision_o(fw_decision_o),.status_o(status_o));
endmodule
