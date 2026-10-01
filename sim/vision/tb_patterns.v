`timescale 1ns/1ps
module tb_patterns;
    reg clk=0,aclk=0,rst_n=0,vs=0,hs=0,de=0,av=0,wv=0;
    always #5 clk=~clk;
    always #7 aclk=~aclk;
    reg [23:0] rgb=0;
    reg [6:0] addr=0;
    reg [31:0] data=0;
    wire awr,wr,bv,cv,ch,cd;
    wire [7:0] cy;
    wire [31:0] frame_id,config_id;
    reg [23:0] input_px[0:383];
    reg [7:0] expected[0:95];
    integer n=0,frames=0,rows=0,f,x,y;
    vision_top #(.SW(16),.SH(8),.DW(8),.DH(4),.NLINES(8)) dut(
        .clk(clk),.s_axi_aclk(aclk),.rst_n(rst_n),.in_vs(vs),.in_hs(hs),.in_de(de),.in_rgb(rgb),
        .awvalid(av),.awready(awr),.awaddr(addr),.wvalid(wv),.wready(wr),.wdata(data),.wstrb(4'hf),
        .bvalid(bv),.bready(1'b1),.arvalid(1'b0),.araddr(7'b0),.rready(1'b1),
        .cop_ready(1'b1),.cop_vs(cv),.cop_hs(ch),.cop_de(cd),.cop_y(cy),
        .cop_frame_id(frame_id),.cop_config_id(config_id));
    always @(posedge clk) begin
        #1;
        if(cv) frames=frames+1;
        if(ch) rows=rows+1;
        if(cd) begin
            if(n>=96 || cy!==expected[n]) $fatal(1,"pattern pixel %0d got %0d expected %0d",n,cy,expected[n]);
            if(frame_id!==n/32+1 || config_id!==1) $fatal(1,"pattern metadata");
            n=n+1;
        end
    end
    task write_reg;
        input [6:0] a;input [31:0] d;
        begin
            @(negedge aclk);addr=a;data=d;av=1;wv=1;
            @(negedge aclk);av=0;wv=0;
            wait(bv);repeat(3) @(negedge aclk);
        end
    endtask
    initial begin
        $readmemh("../data/golden/vision/localize/patterns_rgb.hex",input_px);
        $readmemh("../data/golden/vision/localize/patterns_expected.hex",expected);
        repeat(4) @(negedge clk);rst_n=1;repeat(8) @(negedge clk);
        write_reg(0,3);write_reg(44,1);repeat(5) @(negedge clk);
        for(f=0;f<3;f=f+1) begin
            vs=1;@(negedge clk);vs=0;repeat(6) @(negedge clk);
            for(y=0;y<8;y=y+1) begin
                for(x=0;x<16;x=x+1) begin de=1;rgb=input_px[f*128+y*16+x];@(negedge clk);end
                de=0;repeat(3) @(negedge clk);hs=1;@(negedge clk);hs=0;@(negedge clk);
            end
            repeat(300) @(negedge clk);
        end
        if(n!=96 || frames!=3 || rows!=12) $fatal(1,"pattern count %0d/%0d/%0d",n,frames,rows);
        $display("PASS: 3 synthetic nonconstant RGB scenes -> gaussian/scaler/cop_buf, 96 pixels + IDs exact");
        $finish;
    end
    initial begin #100000;$fatal(1,"timeout");end
endmodule
