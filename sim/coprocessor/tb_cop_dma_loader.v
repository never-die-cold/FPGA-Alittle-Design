`timescale 1ns/1ps
module tb_cop_dma_loader;
    reg clk=0,rst_n=0,start=0,valid=0,last=0,store_ready=0;
    reg [31:0] expected=16; reg [63:0] data=0; reg [7:0] keep=8'hff;
    wire ready,write,busy,done,error,short; wire [31:0] addr,bytes,crc32;
    wire [63:0] store_data; wire [7:0] store_strb; integer writes=0;
    always #5 clk=~clk;
    always @(posedge clk) if(write) writes=writes+1;
    cop_dma_loader dut(.clk(clk),.rst_n(rst_n),.start_i(start),.expected_bytes_i(expected),
        .stream_data_i(data),.stream_keep_i(keep),.stream_valid_i(valid),.stream_last_i(last),
        .store_ready_i(store_ready),.stream_ready_o(ready),.store_write_o(write),.store_addr_o(addr),
        .store_data_o(store_data),.store_strb_o(store_strb),.busy_o(busy),.done_o(done),
        .error_o(error),.short_o(short),.bytes_received_o(bytes),.crc32_o(crc32));
    initial begin
        repeat(2) @(posedge clk); rst_n=1; @(negedge clk); start=1; @(negedge clk); start=0;
        data=64'h0706050403020100; valid=1; repeat(2) @(posedge clk); #1;
        if(ready || write || writes!=0 || !busy) $fatal(1);
        store_ready=1; @(posedge clk); #1; if(writes!=1 || addr!=8) $fatal(1);
        data=64'h0f0e0d0c0b0a0908; last=1; @(posedge clk); #1;
        valid=0; last=0; if(!done || busy || error || short || bytes!=16 || writes!=2 ||
            crc32!==32'hcecee288) $fatal(1);
        $display("PASS: cop_dma_loader loads 16 bytes with backpressure and CRC32=cecee288"); $finish;
    end
    initial begin #2000; $fatal(1,"loader timeout"); end
endmodule
