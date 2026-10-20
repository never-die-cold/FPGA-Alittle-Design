`timescale 1ns/1ps
// DataMover stream sink. The external AXI DMA owns DDR transactions.
// CRC 逐字节折叠（每拍占 8 个 cop 拍）：8 字节一拍折完的异或树有 13 级 LUT，
// 在 xc7z020-1 上跑不进 100 MHz（OPEN-12）。装载是一次性动作，降速代价可忽略；
// 消化期间 stream_ready_o 拉低，上游按 AXI-Stream 协议等待，不得丢字节或重复计数。
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
    reg [31:0] crc_state;
    reg [63:0] hold_data; reg [7:0] hold_keep;
    reg [2:0] step, fin_step, fin_now;
    reg capturing, finishing, finish_ok, finish_short;
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
    // 当前拍的字节数与最高有效字节下标（组合，来自流上的 keep）
    always @* begin
        beat_bytes=0;
        for(lane=0;lane<8;lane=lane+1) if(stream_keep_i[lane]) beat_bytes=beat_bytes+1;
    end
    always @* begin
        fin_now=0;                 // 升序扫，最后一次赋值落在最高的 keep 位
        for(lane=0;lane<8;lane=lane+1) if(stream_keep_i[lane]) fin_now=lane;
    end
    wire accept = stream_valid_i && stream_ready_o;
    assign stream_ready_o = busy_o && store_ready_i && !capturing;
    assign store_write_o = accept;
    assign store_addr_o = bytes_received_o;
    assign store_data_o = stream_data_i;
    assign store_strb_o = stream_keep_i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            expected_bytes<=0; busy_o<=0; done_o<=0; error_o<=0;
            short_o<=0; bytes_received_o<=0; crc_state<=32'hffff_ffff; crc32_o<=0;
            hold_data<=0; hold_keep<=0; step<=0; fin_step<=0;
            capturing<=0; finishing<=0; finish_ok<=0; finish_short<=0;
        end else begin
            done_o<=0; error_o<=0;
            if(start_i && !busy_o) begin
                expected_bytes<=expected_bytes_i; bytes_received_o<=0;
                busy_o<=expected_bytes_i!=0; error_o<=expected_bytes_i==0; short_o<=0;
                crc_state<=32'hffff_ffff; crc32_o<=0; capturing<=0; step<=0;
            end else if(capturing) begin
                if(hold_keep[step]) crc_state<=crc_byte(crc_state, hold_data[step*8 +: 8]);
                if(step==fin_step) begin
                    capturing<=0;
                    if(finishing) begin
                        busy_o<=0;
                        if(finish_ok) begin
                            done_o<=1;
                            crc32_o<=~crc_byte(crc_state, hold_data[fin_step*8 +: 8]);
                        end else begin
                            error_o<=1; short_o<=finish_short;
                        end
                    end
                end else begin
                    step<=step+3'd1;
                end
            end else if(accept) begin
                hold_data<=stream_data_i; hold_keep<=stream_keep_i;
                fin_step<=fin_now; step<=0;
                bytes_received_o<=bytes_received_o+beat_bytes;
                finishing<=stream_last_i || bytes_received_o+beat_bytes>=expected_bytes;
                finish_ok<=stream_last_i && bytes_received_o+beat_bytes==expected_bytes;
                finish_short<=stream_last_i ? (bytes_received_o+beat_bytes<expected_bytes)
                                            : (bytes_received_o+beat_bytes>expected_bytes);
                capturing<=1;
            end
        end
    end
endmodule
