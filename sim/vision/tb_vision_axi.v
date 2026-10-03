`timescale 1ns/1ps
module tb_vision_axi;
    reg pclk=0,aclk=0,rst_n=0,locked=0;
    always #5 pclk=~pclk;
    always #7 aclk=~aclk;
    reg vs=0,hs=0,de=0;
    reg [23:0] rbg=0;
    wire ovs,ohs,ode;
    wire [23:0] orgb;
    vision_axi dut(.pclk(pclk),.s_axi_aclk(aclk),.s_axi_aresetn(rst_n),.video_locked(locked),
        .raw_vs(vs),.raw_hs(hs),.raw_de(de),.raw_rbg(rbg),
        .video_vs(ovs),.video_hs(ohs),.video_de(ode),.video_rbg(orgb),
        .s_axi_awaddr(32'b0),.s_axi_araddr(32'b0),.s_axi_awprot(3'b0),.s_axi_arprot(3'b0),
        .s_axi_awvalid(1'b0),.s_axi_wvalid(1'b0),.s_axi_bready(1'b1),
        .s_axi_arvalid(1'b0),.s_axi_rready(1'b1),.s_axi_wdata(32'b0),.s_axi_wstrb(4'b0));
    integer i;
    initial begin
        repeat(3) @(negedge pclk);
        rst_n=1;locked=1;
        repeat(8) @(negedge pclk);
        for(i=0;i<32;i=i+1) begin
            rbg={8'hA0+i[7:0],8'h20+i[7:0],8'h60+i[7:0]};
            vs=i<3;hs=i%8<2;de=i%8>=2;
            #1;
            if(dut.u_pipeline.raw_rgb !== {rbg[23:16],rbg[7:0],rbg[15:8]})
                $fatal(1,"RBG input conversion failed");
            @(posedge pclk);#1;
            if({ovs,ohs,ode,orgb} !== {vs,hs,de,rbg}) $fatal(1,"TMDS boundary color/sync changed");
            @(negedge pclk);
        end
        locked=0;#1;
        if(ode!==0) $fatal(1,"lock loss did not reset video");
        locked=1;repeat(8) @(negedge pclk);
        if(dut.u_pipeline.seen_frame!==0) $fatal(1,"partial frame admitted after lock recovery");
        $display("PASS: AXI HDMI wrapper RBG/RGB/raw sync + lock-loss reset");
        $finish;
    end
    initial begin #100000;$fatal(1,"timeout");end
endmodule
