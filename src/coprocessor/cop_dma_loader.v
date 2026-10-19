`timescale 1ns/1ps
// DataMover stream sink. The external AXI DMA owns DDR transactions.
module cop_dma_loader (
    input wire clk, rst_n, start_i,
    input wire [31:0] expected_bytes_i,
    input wire [63:0] stream_data_i,
    input wire [7:0] stream_keep_i,
    input wire stream_valid_i, stream_last_i, store_ready_i,
    output wire stream_ready_o, store_write_o,
    output wire [31:0] store_addr_o,
    output wire [63:0] store_data_o,
    output wire [7:0] store_strb_o,
    output reg busy_o, done_o, error_o, short_o,
    output reg [31:0] bytes_received_o, crc32_o
);
    reg [31:0] expected_bytes;
    reg [31:0] crc_state,crc_next;
    integer beat_bytes; integer lane;
    function [31:0] crc_byte;
        input [31:0] crc; input [7:0] data; integer bit_index; reg [31:0] value;
        begin
            value=crc^{24'd0,data};
            for(bit_index=0;bit_index<8;bit_index=bit_index+1)
                value=value[0] ? (value>>1)^32'hedb88320 : value>>1;
            crc_byte=value;
        end
    endfunction
    always @* begin
        beat_bytes=0; crc_next=crc_state;
        for(lane=0;lane<8;lane=lane+1) if(stream_keep_i[lane]) begin
            beat_bytes=beat_bytes+1; crc_next=crc_byte(crc_next,stream_data_i[lane*8 +: 8]);
        end
    end
    assign stream_ready_o = busy_o && store_ready_i;
    assign store_write_o = stream_valid_i && stream_ready_o;
    assign store_addr_o = bytes_received_o;
    assign store_data_o = stream_data_i;
    assign store_strb_o = stream_keep_i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            expected_bytes<=0; busy_o<=0; done_o<=0; error_o<=0;
            short_o<=0; bytes_received_o<=0; crc_state<=32'hffff_ffff; crc32_o<=0;
        end else begin
            done_o<=0; error_o<=0;
            if(start_i && !busy_o) begin
                expected_bytes<=expected_bytes_i; bytes_received_o<=0;
                busy_o<=expected_bytes_i!=0; error_o<=expected_bytes_i==0; short_o<=0;
                crc_state<=32'hffff_ffff; crc32_o<=0;
            end else if(store_write_o) begin
                bytes_received_o<=bytes_received_o+beat_bytes; crc_state<=crc_next;
                if(stream_last_i || bytes_received_o+beat_bytes>=expected_bytes) begin
                    busy_o<=0;
                    if(stream_last_i && bytes_received_o+beat_bytes==expected_bytes) begin
                        done_o<=1; crc32_o<=~crc_next;
                    end
                    else begin error_o<=1; short_o<=bytes_received_o+beat_bytes<expected_bytes; end
                end
            end
        end
    end
endmodule
