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
    input wire [11:0] s_axi_awaddr_i, input wire s_axi_awvalid_i,
    output wire s_axi_awready_o,
    input wire [31:0] s_axi_wdata_i, input wire [3:0] s_axi_wstrb_i,
    input wire s_axi_wvalid_i, output wire s_axi_wready_o,
    output wire [1:0] s_axi_bresp_o, output wire s_axi_bvalid_o, input wire s_axi_bready_i,
    input wire [11:0] s_axi_araddr_i, input wire s_axi_arvalid_i,
    output wire s_axi_arready_o,
    output wire [31:0] s_axi_rdata_o, output wire [1:0] s_axi_rresp_o,
    output wire s_axi_rvalid_o, input wire s_axi_rready_i,
    input wire dma_start_i, dma_kind_i,
    input wire [63:0] dma_data_i,
    input wire [7:0] dma_keep_i,
    input wire dma_valid_i, dma_last_i, store_ready_i,
    output wire dma_ready_o, store_write_o,
    output wire [31:0] store_addr_o,
    output wire [63:0] store_data_o,
    output wire [7:0] store_strb_o,
    input wire [15:0] target_id_i,
    input wire [63:0] memory_data_i,
    input wire [1023:0] weight_data_i,
    input wire [511:0] bias_data_i, multiplier_data_i,
    input wire [95:0] shift_data_i,
    output wire memory_enable_o, weight_enable_o, parameter_enable_o,
    output wire [1:0] read_bank_o, write_bank_o,
    output wire [15:0] read_address_o, weight_address_o, write_address_o,
    output wire [7:0] parameter_address_o,
    output wire memory_write_o,
    output wire [63:0] memory_write_data_o,
    input wire irq_pending_i,
    output wire engine_start_o, result_write_o,
    output wire [3:0] task_result_index_o,
    output wire [31:0] result_seq_o,
    output wire [127:0] result_data_o,
    output wire [31:0] status_o, fw_counts_o, fw_decision_o,
    output wire [3:0] result_index_o
);
    wire core_request,mailbox_pending,command_valid,command_done;
    wire [11:0] core_offset,command_offset; wire [31:0] core_data,command_data;
    wire done_status,error_status,timeout_status,result_valid_status;
    wire cfg_valid,loader_done,loader_error,loader_short,dma_busy;
    wire start_command,task_ready,task_busy,task_done,task_error,task_timeout;
    wire engine_ready,engine_busy,engine_done,engine_error,engine_start;
    wire [2:0] engine_error_layer; wire [31:0] engine_cycles;
    wire [1:0] engine_class; wire [7:0] engine_margin;
    wire [14:0] engine_score; wire engine_low_conf; wire [23:0] engine_logits;
    reg [127:0] result_mem [0:15]; reg [127:0] result_sample1,result_sample2;
    reg [31:0] result_seq_sync1,result_seq_sync2; integer result_slot;
    wire [31:0] cfg_applied,model_id,weight_crc32,timeout_cycles,weight_bytes,dma_bytes,work_order;
    wire [31:0] loader_crc32;
    wire ps_write_valid,ps_write_done,ps_write_error; wire [11:0] ps_write_offset,ps_read_offset;
    wire [31:0] ps_write_data; wire [3:0] ps_write_strb; reg [31:0] ps_read_data; reg ps_read_error;
    wire [4:0] roi_count; wire [7:0] min_margin; reg model_valid,roi_valid,load_kind;
    cop_core_mmio_gate #(.COP_BASE(COP_BASE)) gate(
        .addr_i(core_addr_i),.wdata_i(core_wdata_i),.status_i(status_o),.be_i(core_be_i),
        .we_i(core_we_i),.busy_i(task_busy),.mailbox_pending_i(mailbox_pending),
        .fw_counts_i(fw_counts_o),.fw_decision_i(fw_decision_o),.result_index_i(result_index_o),
        .result_data_i(result_sample2),.result_seq_i(result_seq_sync2),
        .cfg_applied_i(cfg_applied),.dma_bytes_i(dma_bytes),.work_order_i(work_order),
        .roi_count_i(roi_count),
        .cop_hit_o(core_hit_o),.write_request_o(core_request),.write_offset_o(core_offset),
        .write_data_o(core_data),.rdata_o(core_rdata_o));
    cop_cdc_mailbox mailbox(.src_clk(core_clk),.dst_clk(cop_clk),.rst_n(rst_n),
        .src_valid_i(core_request),.src_offset_i(core_offset),.src_data_i(core_data),
        .src_pending_o(mailbox_pending),.dst_valid_o(command_valid),.dst_offset_o(command_offset),
        .dst_data_o(command_data),.dst_done_i(command_done));
    cop_ctrl_regs regs(.clk(cop_clk),.rst_n(rst_n),.write_valid_i(command_valid),
        .write_offset_i(command_offset),.write_data_i(command_data),.task_busy_i(task_busy),
        .task_done_i(task_done),.task_error_i(task_error),.task_timeout_i(task_timeout),
        .ready_i(task_ready),.cfg_valid_i(cfg_valid),.model_valid_i(model_valid),
        .dma_busy_i(dma_busy),.irq_pending_i(irq_pending_i),.start_pulse_o(start_command),
        .write_done_o(command_done),.done_o(done_status),.error_o(error_status),
        .timeout_o(timeout_status),.result_valid_o(result_valid_status),.result_index_o(result_index_o),
        .fw_counts_o(fw_counts_o),.fw_decision_o(fw_decision_o),.status_o(status_o));
    cop_axi_lite_frontend axi(.clk(cop_clk),.rst_n(rst_n),.s_awaddr_i(s_axi_awaddr_i),
        .s_awvalid_i(s_axi_awvalid_i),.s_awready_o(s_axi_awready_o),.s_wdata_i(s_axi_wdata_i),
        .s_wstrb_i(s_axi_wstrb_i),.s_wvalid_i(s_axi_wvalid_i),.s_wready_o(s_axi_wready_o),
        .s_bresp_o(s_axi_bresp_o),.s_bvalid_o(s_axi_bvalid_o),.s_bready_i(s_axi_bready_i),
        .s_araddr_i(s_axi_araddr_i),.s_arvalid_i(s_axi_arvalid_i),.s_arready_o(s_axi_arready_o),
        .s_rdata_o(s_axi_rdata_o),.s_rresp_o(s_axi_rresp_o),.s_rvalid_o(s_axi_rvalid_o),
        .s_rready_i(s_axi_rready_i),.write_valid_o(ps_write_valid),.write_offset_o(ps_write_offset),
        .write_data_o(ps_write_data),.write_strb_o(ps_write_strb),.write_done_i(ps_write_done),
        .write_slverr_i(ps_write_error),.read_offset_o(ps_read_offset),.read_data_i(ps_read_data),
        .read_slverr_i(ps_read_error));
    cop_config_regs u_config(.clk(cop_clk),.rst_n(rst_n),.write_valid_i(ps_write_valid),
        .busy_i(task_busy),.write_offset_i(ps_write_offset),.write_data_i(ps_write_data),
        .write_strb_i(ps_write_strb),.write_done_o(ps_write_done),.slverr_o(ps_write_error),
        .cfg_valid_o(cfg_valid),.cfg_applied_o(cfg_applied),.model_id_o(model_id),
        .weight_crc32_o(weight_crc32),.work_order_o(work_order),
        .timeout_cycles_o(timeout_cycles),.weight_bytes_o(weight_bytes),.roi_count_o(roi_count),
        .min_margin_o(min_margin));
    always @* begin
        ps_read_error=0; ps_read_data=0;
        case(ps_read_offset)
            12'h000: ps_read_data=32'h434f5030; 12'h004: ps_read_data=0;
            12'h010: ps_read_data=status_o; 12'h020: ps_read_data=cfg_applied;
            12'h024: ps_read_data=model_id; 12'h02c: ps_read_data={27'd0,roi_count};
            12'h030: ps_read_data=timeout_cycles; 12'h04c: ps_read_data=weight_bytes;
            12'h064: ps_read_data={24'd0,min_margin}; 12'h06c: ps_read_data={28'd0,result_index_o};
            12'h070: ps_read_data=result_mem[result_index_o][31:0];
            12'h074: ps_read_data={8'd0,result_mem[result_index_o][55:32]};
            12'h078: ps_read_data={8'd0,result_mem[result_index_o][63:56],
                1'b0,result_mem[result_index_o][78:64]};
            12'h07c: ps_read_data=result_seq_o; 12'h080: ps_read_data=result_mem[result_index_o][127:96];
            12'h084: ps_read_data=dma_bytes; default: ps_read_error=1;
        endcase
    end
    cop_dma_loader loader(.clk(cop_clk),.rst_n(rst_n),.start_i(dma_start_i),
        .expected_bytes_i(dma_kind_i ? {roi_count,12'd0} : weight_bytes),.stream_data_i(dma_data_i),
        .stream_keep_i(dma_keep_i),.stream_valid_i(dma_valid_i),.stream_last_i(dma_last_i),
        .store_ready_i(store_ready_i),.stream_ready_o(dma_ready_o),.store_write_o(store_write_o),
        .store_addr_o(store_addr_o),.store_data_o(store_data_o),.store_strb_o(store_strb_o),
        .busy_o(dma_busy),.done_o(loader_done),.error_o(loader_error),.short_o(loader_short),
        .bytes_received_o(dma_bytes),.crc32_o(loader_crc32));
    cop_task_ctrl u_task(.clk(cop_clk),.rst_n(rst_n),.start_i(start_command),.cfg_valid_i(cfg_valid),
        .model_valid_i(model_valid),.roi_valid_i(roi_valid),.roi_count_i(roi_count),
        .engine_ready_i(engine_ready),.engine_done_i(engine_done),.engine_error_i(engine_error),
        .engine_timeout_i(engine_error && engine_error_layer==7),.target_id_i(target_id_i),
        .result_class_i(engine_class),.result_margin_i(engine_margin),.result_score_i(engine_score),
        .result_low_conf_i(engine_low_conf),.result_logits_i(engine_logits),
        .result_cycles_i(engine_cycles),.ready_o(task_ready),.busy_o(task_busy),
        .done_pulse_o(task_done),.error_pulse_o(task_error),.timeout_pulse_o(task_timeout),
        .engine_start_o(engine_start),.result_write_o(result_write_o),
        .result_index_o(task_result_index_o),.result_seq_o(result_seq_o),.result_data_o(result_data_o));
    assign engine_start_o=engine_start;
    cnn_sequencer engine(.clk(cop_clk),.rst_n(rst_n),.ce(1'b1),.start(engine_start),
        .min_margin(min_margin),.cycle_limit(timeout_cycles),.ready(engine_ready),.busy(engine_busy),
        .done(engine_done),.error(engine_error),.error_layer(engine_error_layer),.cycles(engine_cycles),
        .result_class(engine_class),.result_margin(engine_margin),.result_score(engine_score),
        .result_low_conf(engine_low_conf),.result_logits(engine_logits),.memory_enable(memory_enable_o),
        .weight_enable(weight_enable_o),.parameter_enable(parameter_enable_o),.read_bank(read_bank_o),
        .read_address(read_address_o),.weight_address(weight_address_o),.parameter_address(parameter_address_o),
        .input_data(memory_data_i),.weight_data(weight_data_i),.bias_data(bias_data_i),
        .multiplier_data(multiplier_data_i),.shift_data(shift_data_i),.write_enable(memory_write_o),
        .write_bank(write_bank_o),.write_address(write_address_o),.write_data(memory_write_data_o));
    always @(posedge cop_clk or negedge rst_n) begin
        if(!rst_n) begin
            model_valid<=0; roi_valid<=0; load_kind<=0;
            for(result_slot=0;result_slot<16;result_slot=result_slot+1) result_mem[result_slot]<=0;
        end
        else begin
            if(dma_start_i && !dma_busy) load_kind<=dma_kind_i;
            if(loader_done && !load_kind) model_valid<=loader_crc32==weight_crc32;
            if(loader_done && load_kind) roi_valid<=1;
            if(result_write_o) result_mem[task_result_index_o]<=result_data_o;
        end
    end
    always @(posedge core_clk or negedge rst_n) begin
        if(!rst_n) begin result_sample1<=0; result_sample2<=0; result_seq_sync1<=0; result_seq_sync2<=0; end
        else begin
            result_sample1<=result_mem[result_index_o]; result_sample2<=result_sample1;
            result_seq_sync1<=result_seq_o; result_seq_sync2<=result_seq_sync1;
        end
    end
endmodule
