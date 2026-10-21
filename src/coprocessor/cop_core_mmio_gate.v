`timescale 1ns/1ps
// RISC-V local MMIO admission gate. No storage, CDC, or wait-state behavior.
module cop_core_mmio_gate #(
    parameter [31:0] COP_BASE = 32'h8001_0000
) (
    input wire [31:0] addr_i, wdata_i, status_i,
    input wire [31:0] fw_counts_i, fw_decision_i,
    input wire [3:0] result_index_i,
    input wire [127:0] result_data_i,
    input wire [31:0] result_seq_i, cfg_applied_i, dma_bytes_i, work_order_i,
    input wire [4:0] roi_count_i,
    input wire [3:0] be_i,
    input wire we_i, busy_i, mailbox_pending_i,
    output wire cop_hit_o, write_request_o,
    output wire [11:0] write_offset_o,
    output wire [31:0] write_data_o,
    output reg [31:0] rdata_o
);
    wire aligned = addr_i[1:0] == 2'b00;
    wire ctrl_offset = addr_i[11:0] == 12'h00c;
    wire status_offset = addr_i[11:0] == 12'h010;
    wire result_index_offset = addr_i[11:0] == 12'h06c;
    wire fw_counts_offset = addr_i[11:0] == 12'h088;
    wire fw_decision_offset = addr_i[11:0] == 12'h08c;
    wire ctrl_bits_valid = (wdata_i & 32'hffff_ffc0) == 0;
    wire ctrl_has_command = |(wdata_i & 32'h0000_003f);
    wire start_allowed = !(wdata_i[0] && (busy_i || status_i[12]));
    wire abort_allowed = !(wdata_i[1] && !busy_i);

    assign cop_hit_o = addr_i[31:12] == COP_BASE[31:12];
    wire ctrl_write_valid = ctrl_offset && ctrl_bits_valid && ctrl_has_command &&
                            start_allowed && abort_allowed;
    wire data_write_valid = (result_index_offset && wdata_i <= 15) ||
                            fw_counts_offset || fw_decision_offset;
    assign write_request_o = cop_hit_o && aligned && we_i && be_i == 4'b1111
                           && !mailbox_pending_i && (ctrl_write_valid || data_write_valid);
    assign write_offset_o = addr_i[11:0];
    assign write_data_o = wdata_i;

    always @* begin
        rdata_o = 32'd0;
        if (cop_hit_o && aligned && !we_i && status_offset) begin
            rdata_o = status_i;
            rdata_o[10] = mailbox_pending_i;
        end else if(cop_hit_o && aligned && !we_i) begin
            case(addr_i[11:0])
                12'h000: rdata_o = 32'h434f5030;
                12'h004: rdata_o = 32'h0000_0000;
                12'h020: rdata_o = cfg_applied_i;
                12'h02c: rdata_o = {27'd0,roi_count_i};
                12'h034: rdata_o = work_order_i;
                12'h06c: rdata_o = {28'd0,result_index_i};
                12'h070: rdata_o = result_data_i[31:0];
                12'h074: rdata_o = {8'd0,result_data_i[55:32]};
                12'h078: rdata_o = {8'd0,result_data_i[63:56],1'b0,result_data_i[78:64]};
                12'h07c: rdata_o = result_seq_i;
                12'h080: rdata_o = result_data_i[127:96];
                12'h084: rdata_o = dma_bytes_i;
                12'h088: rdata_o = fw_counts_i;
                12'h08c: rdata_o = fw_decision_i;
                default: rdata_o = 32'd0;
            endcase
        end
    end
endmodule
