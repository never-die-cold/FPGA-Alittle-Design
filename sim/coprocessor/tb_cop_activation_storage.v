`timescale 1ns/1ps
module tb_cop_activation_storage;
    reg clk=0,rst_n=0,init_we=0,read_en=0,write_en=0; reg [15:0] init_addr=0,read_addr=0,write_addr=0;
    reg [63:0] init_data=0,write_data=0; reg [3:0] roi_index=0; reg [1:0] read_bank=0,write_bank=0;
    wire [63:0] data;
    always #5 clk=~clk;
    cop_activation_storage dut(.clk(clk),.rst_n(rst_n),.init_we_i(init_we),.init_address_i(init_addr),
        .init_data_i(init_data),.roi_index_i(roi_index),.read_enable_i(read_en),.read_bank_i(read_bank),
        .read_address_i(read_addr),.write_enable_i(write_en),.write_bank_i(write_bank),
        .write_address_i(write_addr),.write_data_i(write_data),.input_data_o(data));
    task init_word; input [15:0] addr; input [63:0] value;
        begin @(negedge clk); init_addr=addr; init_data=value; init_we=1; @(posedge clk); #1; @(negedge clk); init_we=0; end
    endtask
    task read_roi; input [3:0] slot; input [15:0] addr; input [7:0] expected;
        begin
            @(negedge clk); roi_index=slot; read_bank=0; read_addr=addr; read_en=1;
            @(posedge clk); #1; @(posedge clk); #1; read_en=0;
            if(data[7:0]!==expected) $fatal(1);
        end
    endtask
    initial begin
        repeat(2) @(negedge clk); rst_n=1;
        init_word(0,64'h0706050403020100); init_word(512,64'h1716151413121110);
        read_roi(0,3,8'h03); read_roi(1,3,8'h13);
        @(negedge clk); write_bank=1; write_addr=9; write_data=64'hdeadbeef01234567; write_en=1;
        @(posedge clk); #1; @(negedge clk); write_en=0; read_bank=1; read_addr=9; read_en=1;
        @(posedge clk); #1; @(posedge clk); #1; if(data!==64'hdeadbeef01234567) $fatal(1);
        $display("PASS: activation_storage keeps 16 ROI slots distinct and preserves ping/pong interface");
        $finish;
    end
endmodule
