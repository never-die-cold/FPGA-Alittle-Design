`timescale 1ns/1ps
module tb_cop_bram_latency;
    reg clk=0,rst_n=0,init_we=0,read_enable=0; reg [2:0] init_kind=0;
    reg [15:0] init_address=0,read_address=0; reg [63:0] init_data=0; wire [63:0] q;
    always #5 clk=~clk;
    cop_bram_storage dut(.clk(clk),.rst_n(rst_n),.init_we_i(init_we),.init_kind_i(init_kind),
        .init_address_i(init_address),.init_data_i(init_data),.read_enable_i(read_enable),
        .read_bank_i(2'd0),.read_address_i(read_address),.weight_enable_i(1'b0),.weight_address_i(16'd0),
        .parameter_enable_i(1'b0),.parameter_address_i(8'd0),.write_enable_i(1'b0),
        .write_bank_i(2'd0),.write_address_i(16'd0),.write_data_i(64'd0),.input_data_o(q));
    task load; input [15:0] address; input [63:0] data;
        begin @(negedge clk); init_address=address; init_data=data; init_we=1;
            @(posedge clk); #1; init_we=0; end
    endtask
    initial begin
        load(0,64'h0807060504030201); load(1,64'h1817161514131211); load(2,64'h2827262524232221);
        @(negedge clk); rst_n=1; read_enable=1; read_address=0; #1;
        if(q===64'h1) $fatal(1,"early sample silently matched");
        @(posedge clk); #1; if(q!==64'h1) $fatal(1,"nominal one-cycle read failed");
        @(negedge clk); read_address=8; @(posedge clk); #1; if(q!==64'h11) $fatal(1);
        @(negedge clk); read_address=16; @(posedge clk); #1;
        if(q===64'h11 || q!==64'h21) $fatal(1,"late sample was not visible");
        $display("PASS: K3-LATENCY nominal one-cycle BRAM read matches; early/late samples mismatch visibly");
        $finish;
    end
endmodule
