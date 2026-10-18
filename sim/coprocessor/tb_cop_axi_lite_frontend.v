`timescale 1ns/1ps
module tb_cop_axi_lite_frontend;
    reg clk=0,rst_n=0,awv=0,wv=0,br=0,arv=0,rr=0,done=0,slverr=0;
    reg [11:0] awaddr=0,araddr=0; reg [31:0] wdata=0;
    wire awr,wr,bv,arr,rv,write_valid; wire [1:0] bresp,rresp;
    wire [31:0] rdata,write_data; wire [11:0] write_offset,read_offset; wire [3:0] write_strb;
    always #5 clk=~clk;
    cop_axi_lite_frontend dut(.clk(clk),.rst_n(rst_n),.s_awaddr_i(awaddr),.s_awvalid_i(awv),
        .s_awready_o(awr),.s_wdata_i(wdata),.s_wstrb_i(4'hf),.s_wvalid_i(wv),.s_wready_o(wr),
        .s_bresp_o(bresp),.s_bvalid_o(bv),.s_bready_i(br),.s_araddr_i(araddr),.s_arvalid_i(arv),
        .s_arready_o(arr),.s_rdata_o(rdata),.s_rresp_o(rresp),.s_rvalid_o(rv),.s_rready_i(rr),
        .write_valid_o(write_valid),.write_offset_o(write_offset),.write_data_o(write_data),
        .write_strb_o(write_strb),.write_done_i(done),.write_slverr_i(slverr),
        .read_offset_o(read_offset),.read_data_i({20'd0,read_offset}),.read_slverr_i(1'b0));
    initial begin
        repeat(2) @(posedge clk); rst_n=1; @(negedge clk); awaddr=12'h024; wdata=32'h12345678; awv=1; wv=1;
        @(negedge clk); awv=0; wv=0; wait(write_valid); #1;
        if(write_offset!=12'h024 || write_data!==32'h12345678 || write_strb!=4'hf) $fatal(1);
        @(negedge clk); done=1; @(negedge clk); done=0; wait(bv); if(bresp!=0) $fatal(1);
        br=1; @(posedge clk); #1; br=0;
        @(negedge clk); araddr=12'h010; arv=1; @(negedge clk); arv=0; wait(rv);
        if(rresp!=0 || rdata!==32'h00000010) $fatal(1); rr=1; @(posedge clk);
        $display("PASS: cop_axi_lite_frontend one write response and one read response"); $finish;
    end
    initial begin #2000; $fatal(1,"axi-lite timeout"); end
endmodule
