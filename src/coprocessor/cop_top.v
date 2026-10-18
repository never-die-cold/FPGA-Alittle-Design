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
    input wire ps_write_valid_i,
    input wire [11:0] ps_write_offset_i,
    input wire [31:0] ps_write_data_i,
    input wire [3:0] ps_write_strb_i,
    output wire ps_write_done_o, ps_slverr_o,
    input wire dma_start_i, dma_kind_i,
    input wire [63:0] dma_data_i,
    input wire [7:0] dma_keep_i,
    input wire dma_valid_i, dma_last_i, store_ready_i,
    output wire dma_ready_o, store_write_o,
    output wire [31:0] store_addr_o,
    output wire [63:0] store_data_o,
    output wire [7:0] store_strb_o,
    input wire task_ready_i, task_busy_i, task_done_i, task_error_i, task_timeout_i,
    input wire irq_pending_i,
    output wire task_start_o,
    output wire [31:0] status_o, fw_counts_o, fw_decision_o,
    output wire [3:0] result_index_o
);
    wire core_request,mailbox_pending,command_valid,command_done;
    wire [11:0] core_offset,command_offset; wire [31:0] core_data,command_data;
    wire done_status,error_status,timeout_status,result_valid_status;
    wire cfg_valid,loader_done,loader_error,loader_short,dma_busy;
    wire [31:0] cfg_applied,model_id,timeout_cycles,weight_bytes,dma_bytes;
    wire [4:0] roi_count; wire [7:0] min_margin; reg model_valid,roi_valid,load_kind;
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
        .ready_i(task_ready_i),.cfg_valid_i(cfg_valid),.model_valid_i(model_valid),
        .dma_busy_i(dma_busy),.irq_pending_i(irq_pending_i),.start_pulse_o(task_start_o),
        .write_done_o(command_done),.done_o(done_status),.error_o(error_status),
        .timeout_o(timeout_status),.result_valid_o(result_valid_status),.result_index_o(result_index_o),
        .fw_counts_o(fw_counts_o),.fw_decision_o(fw_decision_o),.status_o(status_o));
    cop_config_regs u_config(.clk(cop_clk),.rst_n(rst_n),.write_valid_i(ps_write_valid_i),
        .busy_i(task_busy_i),.write_offset_i(ps_write_offset_i),.write_data_i(ps_write_data_i),
        .write_strb_i(ps_write_strb_i),.write_done_o(ps_write_done_o),.slverr_o(ps_slverr_o),
        .cfg_valid_o(cfg_valid),.cfg_applied_o(cfg_applied),.model_id_o(model_id),
        .timeout_cycles_o(timeout_cycles),.weight_bytes_o(weight_bytes),.roi_count_o(roi_count),
        .min_margin_o(min_margin));
    cop_dma_loader loader(.clk(cop_clk),.rst_n(rst_n),.start_i(dma_start_i),
        .expected_bytes_i(dma_kind_i ? {roi_count,12'd0} : weight_bytes),.stream_data_i(dma_data_i),
        .stream_keep_i(dma_keep_i),.stream_valid_i(dma_valid_i),.stream_last_i(dma_last_i),
        .store_ready_i(store_ready_i),.stream_ready_o(dma_ready_o),.store_write_o(store_write_o),
        .store_addr_o(store_addr_o),.store_data_o(store_data_o),.store_strb_o(store_strb_o),
        .busy_o(dma_busy),.done_o(loader_done),.error_o(loader_error),.short_o(loader_short),
        .bytes_received_o(dma_bytes));
    always @(posedge cop_clk or negedge rst_n) begin
        if(!rst_n) begin model_valid<=0; roi_valid<=0; load_kind<=0; end
        else begin
            if(dma_start_i && !dma_busy) load_kind<=dma_kind_i;
            if(loader_done && !load_kind) model_valid<=1;
            if(loader_done && load_kind) roi_valid<=1;
        end
    end
endmodule
