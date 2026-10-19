`timescale 1ns/1ps
// One outstanding stable-payload request; ACK follows destination completion.
module cop_cdc_mailbox (
    input wire src_clk, dst_clk, rst_n,
    input wire src_valid_i,
    input wire [11:0] src_offset_i,
    input wire [31:0] src_data_i,
    output wire src_pending_o,
    output reg dst_valid_o,
    output reg [11:0] dst_offset_o,
    output reg [31:0] dst_data_o,
    input wire dst_done_i
);
    reg req_toggle, ack_toggle;
    reg ack_sync1, ack_sync2, req_sync1, req_sync2, req_seen, dst_busy;
    reg [11:0] payload_offset;
    reg [31:0] payload_data;
    assign src_pending_o = req_toggle != ack_sync2;
    always @(posedge src_clk or negedge rst_n) begin
        if(!rst_n) begin
            req_toggle<=0; ack_sync1<=0; ack_sync2<=0;
            payload_offset<=0; payload_data<=0;
        end else begin
            ack_sync1<=ack_toggle; ack_sync2<=ack_sync1;
            if(src_valid_i && !src_pending_o) begin
                payload_offset<=src_offset_i; payload_data<=src_data_i;
                req_toggle<=~req_toggle;
            end
        end
    end
    always @(posedge dst_clk or negedge rst_n) begin
        if(!rst_n) begin
            req_sync1<=0; req_sync2<=0; req_seen<=0; ack_toggle<=0;
            dst_busy<=0; dst_valid_o<=0; dst_offset_o<=0; dst_data_o<=0;
        end else begin
            req_sync1<=req_toggle; req_sync2<=req_sync1; dst_valid_o<=0;
            if(!dst_busy && req_sync2!=req_seen) begin
                dst_offset_o<=payload_offset; dst_data_o<=payload_data;
                req_seen<=req_sync2; dst_busy<=1; dst_valid_o<=1;
            end
            if(dst_busy && dst_done_i) begin
                ack_toggle<=req_seen; dst_busy<=0;
            end
        end
    end
endmodule
