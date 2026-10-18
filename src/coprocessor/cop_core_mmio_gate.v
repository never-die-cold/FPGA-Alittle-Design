`timescale 1ns/1ps
// RISC-V local MMIO admission gate. No storage, CDC, or wait-state behavior.
module cop_core_mmio_gate #(
    parameter [31:0] COP_BASE = 32'h8001_0000
) (
    input wire [31:0] addr_i, wdata_i, status_i,
    input wire [31:0] fw_counts_i, fw_decision_i,
    input wire [3:0] result_index_i,
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
    wire ctrl_bits_valid = (wdata_i & 32'hffff_ffe6) == 0;
    wire ctrl_has_command = |(wdata_i & 32'h0000_0019);
    wire start_allowed = !(wdata_i[0] && busy_i);

    assign cop_hit_o = addr_i[31:12] == COP_BASE[31:12];
    wire ctrl_write_valid = ctrl_offset && ctrl_bits_valid && ctrl_has_command && start_allowed;
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
                12'h06c: rdata_o = {28'd0,result_index_i};
                12'h088: rdata_o = fw_counts_i;
                12'h08c: rdata_o = fw_decision_i;
                default: rdata_o = 32'd0;
            endcase
        end
    end
endmodule
