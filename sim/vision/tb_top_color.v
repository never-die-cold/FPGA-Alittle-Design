`timescale 1ns/1ps
module tb_top_color;
    reg clk=0,rst_n=0,vs=0,hs=0,de=0,av=0,wv=0,br=0;
    reg [23:0] rgb=0;
    reg [6:0] addr=0;
    reg [31:0] value=0;
    wire dvs,dhs,dde;
    wire [23:0] drgb;
    wire [31:0] fid,cfg;
    integer pixels=0,frame_count=0,f,l,c;
    vision_top #(.DW(8),.DH(4),.NLINES(8)) dut(
        .clk(clk),.s_axi_aclk(clk),.rst_n(rst_n),.axi_rst_n(rst_n),.in_vs(vs),.in_hs(hs),.in_de(de),.in_rgb(rgb),
        .awvalid(av),.awaddr(addr),.wvalid(wv),.wdata(value),.wstrb(4'hf),.bready(br),
        .arvalid(1'b0),.araddr(7'b0),.rready(1'b1),.cop_ready(1'b0),
        .display_vs(dvs),.display_hs(dhs),.display_de(dde),.display_rgb(drgb),
        .display_frame_id(fid),.active_config_id(cfg));
    always #5 clk=~clk;
    always @(posedge clk) if(rst_n) begin
        if(vs) frame_count=frame_count+1;
        #1;
        if({dvs,dhs,dde,drgb}!=={vs,hs,de,rgb}) $fatal(1,"FAIL: RGB passthrough or markers");
        if(fid!=frame_count) $fatal(1,"FAIL: display frame ID");
        if(dde) pixels=pixels+1;
    end
    task write;
        input [6:0] a;
        input [31:0] v;
        begin
            @(negedge clk);addr=a;value=v;av=1;wv=1;br=1;
            @(negedge clk);av=0;wv=0;
            @(negedge clk);br=0;
        end
    endtask
    initial begin
        repeat(4) @(negedge clk);rst_n=1;
        repeat(4) @(negedge clk);
        write(0,15);write(44,1);repeat(5) @(negedge clk);
        for(f=0;f<2;f=f+1) begin
            vs=1;@(negedge clk);vs=0;@(negedge clk);
            for(l=0;l<8;l=l+1) begin
                for(c=0;c<16;c=c+1) begin
                    de=1;rgb=(f<<20)+((l*16+c)*65537)+123;@(negedge clk);
                end
                de=0;repeat(3) @(negedge clk);hs=1;
                @(negedge clk);hs=0;@(negedge clk);
            end
            repeat(1000) @(negedge clk);
        end
        if(pixels!=256 || cfg!=1) $fatal(1,"FAIL: color count/config %0d/%0d",pixels,cfg);
        $display("PASS: RGB display 256 pixels exact, all analysis enables, stalled consumer, frame IDs");$finish;
    end
    initial begin #100000;$fatal(1,"FAIL: color timeout");end
endmodule
