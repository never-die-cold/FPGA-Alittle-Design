`timescale 1ns/1ps
module tb_cop_axi_lite_frontend;
    reg clk=0,rst_n=0,awv=0,wv=0,br=0,arv=0,rr=0,done=0,wslverr=0,rslverr=0;
    reg [11:0] awaddr=0,araddr=0; reg [31:0] wdata=0;
    wire awr,wr,bv,arr,rv,write_valid; wire [1:0] bresp,rresp;
    wire [31:0] rdata,write_data; wire [11:0] write_offset,read_offset; wire [3:0] write_strb;
    integer hold;
    always #5 clk=~clk;
    cop_axi_lite_frontend dut(.clk(clk),.rst_n(rst_n),.s_awaddr_i(awaddr),.s_awvalid_i(awv),
        .s_awready_o(awr),.s_wdata_i(wdata),.s_wstrb_i(4'hf),.s_wvalid_i(wv),.s_wready_o(wr),
        .s_bresp_o(bresp),.s_bvalid_o(bv),.s_bready_i(br),.s_araddr_i(araddr),.s_arvalid_i(arv),
        .s_arready_o(arr),.s_rdata_o(rdata),.s_rresp_o(rresp),.s_rvalid_o(rv),.s_rready_i(rr),
        .write_valid_o(write_valid),.write_offset_o(write_offset),.write_data_o(write_data),
        .write_strb_o(write_strb),.write_done_i(done),.write_slverr_i(wslverr),
        .read_offset_o(read_offset),.read_data_i({20'd0,read_offset}),.read_slverr_i(rslverr));
    initial begin
        repeat(2) @(posedge clk); rst_n=1;
        // 1) AW/W 同拍：一拍接收、等后端完成才回 B
        @(negedge clk); awaddr=12'h024; wdata=32'h12345678; awv=1; wv=1;
        @(negedge clk); awv=0; wv=0; wait(write_valid); #1;
        if(write_offset!=12'h024 || write_data!==32'h12345678 || write_strb!=4'hf) $fatal(1,"same-cycle launch");
        @(negedge clk); done=1; @(negedge clk); done=0; wait(bv); if(bresp!=0) $fatal(1,"bresp ok");
        hold=0; while(br==0 && hold<6) begin
            if(awr||wr) $fatal(1,"single outstanding violated during B");
            @(posedge clk); #1; hold=hold+1;
        end
        if(!bv) $fatal(1,"bvalid dropped under backpressure"); br=1; @(posedge clk); #1; br=0;
        // 2) W 先到、AW 后到：两笔都收齐才发 launch
        @(negedge clk); wdata=32'hA5A50001; wv=1;
        @(negedge clk); wv=0; if(write_valid) $fatal(1,"launch before AW");
        @(negedge clk); awaddr=12'h028; awv=1;
        @(negedge clk); awv=0; wait(write_valid); #1;
        if(write_offset!=12'h028 || write_data!==32'hA5A50001) $fatal(1,"W-before-AW");
        // 3) 写 SLVERR -> bresp=2'b10
        @(negedge clk); wslverr=1; done=1; @(negedge clk); wslverr=0; done=0; wait(bv);
        if(bresp!=2'b10) $fatal(1,"write slverr"); br=1; @(posedge clk); #1; br=0;
        // 4) 读：rvalid 未消费前不再收 AR
        @(negedge clk); araddr=12'h010; arv=1; @(negedge clk); arv=0; wait(rv);
        if(rresp!=0 || rdata!==32'h00000010) $fatal(1,"read ok");
        hold=0; while(rr==0 && hold<6) begin
            if(arr) $fatal(1,"AR accepted while R outstanding");
            @(posedge clk); #1; hold=hold+1;
        end
        if(!rv) $fatal(1,"rvalid dropped under backpressure"); rr=1; @(posedge clk); #1; rr=0;
        // 5) 读 SLVERR -> rresp=2'b10
        @(negedge clk); rslverr=1; araddr=12'h01c; arv=1;
        @(negedge clk); arv=0; rslverr=0; wait(rv);
        if(rresp!=2'b10 || rdata!==32'h0000001c) $fatal(1,"read slverr"); rr=1; @(posedge clk); #1; rr=0;
        // 6) 复位清掉未消费的 B/R
        @(negedge clk); awaddr=12'h030; wdata=32'h11; awv=1; wv=1;
        @(negedge clk); awv=0; wv=0; wait(write_valid);
        @(negedge clk); done=1; @(negedge clk); done=0; wait(bv);
        @(negedge clk); araddr=12'h010; arv=1; @(negedge clk); arv=0; wait(rv);
        @(negedge clk); rst_n=0; @(negedge clk); rst_n=1; #1;
        if(bv||rv||awr!=1 || wr!=1) $fatal(1,"reset did not clear B/R");
        $display("PASS: cop_axi_lite_frontend AW/W order, B/R backpressure, SLVERR, one-outstanding and reset");
        $finish;
    end
    initial begin #4000; $fatal(1,"axi-lite timeout"); end
endmodule
