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
    // 一拍：valid 保持到被接收为止（AXI-Stream 语义），接收后撤 valid
    task beat;
        input [63:0] d; input [7:0] k; input is_last;
        begin
            @(negedge clk); data=d; keep=k; last=is_last; valid=1;
            @(posedge clk);
            while(!ready) @(posedge clk);
            #1; valid=0; last=0;
        end
    endtask
    initial begin
        repeat(2) @(posedge clk); rst_n=1; @(negedge clk); start=1; @(negedge clk); start=0;
        data=64'h0706050403020100; valid=1; repeat(2) @(posedge clk); #1;
        if(ready || write || writes!=0 || !busy) $fatal(1,"store_ready=0 不得接收");
        store_ready=1; @(posedge clk); #1;
        if(writes!=1 || addr!=8) $fatal(1,"第一拍接收与写地址");
        valid=0;
        repeat(2) @(posedge clk); #1;
        if(ready) $fatal(1,"CRC 消化期间不得接收新拍");
        beat(64'h0f0e0d0c0b0a0908, 8'hff, 1);
        wait(done); #1;
        if(!done || busy || error || short || bytes!=16 || writes!=2 ||
            crc32!==32'hcecee288) $fatal(1,"两拍 CRC32 值与字节数");
        @(negedge clk); start=1; @(negedge clk); start=0; data=0;
        beat(64'd0, 8'hff, 1);
        wait(!busy); #1;
        if(!error || !short || busy || bytes!=8) $fatal(1,"短包错误与字节数");
        @(posedge clk); #1; if(error) $fatal(1,"错误为单拍脉冲");
        $display("PASS: cop_dma_loader normal/backpressure/CRC32 and short-packet error pulse"); $finish;
    end
    initial begin #4000; $fatal(1,"loader timeout"); end
endmodule
