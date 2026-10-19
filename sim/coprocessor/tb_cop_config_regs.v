`timescale 1ns/1ps
module tb_cop_config_regs;
    reg clk=0,rst_n=0,valid=0,busy=0; reg [11:0] offset; reg [31:0] data; reg [3:0] strb=4'hf;
    wire done,slverr,cfg_valid; wire [31:0] applied,model_id,timeout_cycles,weight_bytes;
    wire [4:0] roi_count; wire [7:0] min_margin;
    wire [31:0] weight_crc32,work_order,read_data;
    always #5 clk=~clk;
    cop_config_regs dut(.clk(clk),.rst_n(rst_n),.write_valid_i(valid),.busy_i(busy),
        .write_offset_i(offset),.write_data_i(data),.write_strb_i(strb),.write_done_o(done),
        .slverr_o(slverr),.cfg_valid_o(cfg_valid),.cfg_applied_o(applied),.model_id_o(model_id),
        .weight_crc32_o(weight_crc32),.work_order_o(work_order),.read_offset_i(12'h034),
        .read_data_o(read_data),
        .timeout_cycles_o(timeout_cycles),.weight_bytes_o(weight_bytes),.roi_count_o(roi_count),
        .min_margin_o(min_margin));
    task wr; input [11:0] a; input [31:0] d;
        begin @(negedge clk); offset=a; data=d; valid=1; @(posedge clk); #1;
            if(!done || slverr) $fatal(1); @(negedge clk); valid=0; end
    endtask
    initial begin
        repeat(2) @(posedge clk); rst_n=1;
        wr(12'h01c,7); wr(12'h024,32'h12345678); wr(12'h02c,1); wr(12'h030,1000);
        wr(12'h048,32'h1000); wr(12'h04c,64); wr(12'h050,32'h2000); wr(12'h054,32'h3000);
        wr(12'h034,32'h0a010101); wr(12'h058,4096); wr(12'h05c,32'h4000);
        wr(12'h060,16); wr(12'h064,12);
        wr(12'h068,1);
        if(!cfg_valid || applied!=7 || model_id!==32'h12345678 || roi_count!=1 ||
           timeout_cycles!=1000 || weight_bytes!=64 || work_order!=32'h0a010101 ||
           min_margin!=12 || read_data!=32'h0a010101) $fatal(1);
        $display("PASS: cop_config_regs atomically applies one valid shadow configuration"); $finish;
    end
    initial begin #3000; $fatal(1,"config timeout"); end
endmodule
