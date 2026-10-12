`timescale 1ns/1ps
module tb_video_pipeline;
    reg clk=0,aclk=0,rst_n=0,vs=0,hs=0,de=0,av=0,wv=0,br=0;
    reg [23:0] rgb=0;
    reg [6:0] addr=0;
    reg [31:0] data=0;
    wire vvs,vhs,vde,cvs,chs,cde;
    wire [23:0] vrgb;
    wire [7:0] cy;
    wire [31:0] fid,cid;
    integer f,l,c,display_px=0,cop_px=0,cop_frames=0;
    video_pipeline #(.SW(16),.SH(8),.DW(8),.DH(4),.NLINES(8)) dut(
        .pclk(clk),.s_axi_aclk(aclk),.rst_n(rst_n),.axi_rst_n(rst_n),.raw_vs(vs),.raw_hs(hs),.raw_de(de),.raw_rgb(rgb),
        .awvalid(av),.awaddr(addr),.wvalid(wv),.wdata(data),.wstrb(4'hf),.bready(br),
        .arvalid(1'b0),.araddr(7'b0),.rready(1'b1),.cop_ready(1'b1),
        .video_vs(vvs),.video_hs(vhs),.video_de(vde),.video_rgb(vrgb),
        .cop_vs(cvs),.cop_hs(chs),.cop_de(cde),.cop_y(cy),.cop_frame_id(fid),.cop_config_id(cid));
    always #5 clk=~clk;
    always #7 aclk=~aclk;
    always @(posedge clk) if(rst_n && dut.pixel_reset) begin
        if(cvs) cop_frames=cop_frames+1;
        if(cde) begin
            if(fid!=cop_frames || cid!=1 || cy!==cop_frames*32) $fatal(1,"FAIL: snapshot pixels/frame/config");
            cop_px=cop_px+1;
        end
        #1;
        if({vvs,vhs,vde,vrgb}!=={vs,hs,de,rgb}) $fatal(1,"FAIL: physical sync waveform modified");
        if(vde) display_px=display_px+1;
    end
    task write;
        input [6:0] a;
        input [31:0] v;
        begin
            @(negedge aclk);addr=a;data=v;av=1;wv=1;br=1;
            @(negedge aclk);av=0;wv=0;@(negedge aclk);br=0;
        end
    endtask
    initial begin
        repeat(4) @(negedge clk);rst_n=1;repeat(5) @(negedge clk);
        write(0,3);write(44,1);repeat(8) @(negedge clk);
        for(f=1;f<=2;f=f+1) begin
            vs=1;repeat(4) @(negedge clk);vs=0;repeat(4) @(negedge clk);
            for(l=0;l<8;l=l+1) begin
                for(c=0;c<16;c=c+1) begin
                    de=1;rgb=f*32;rgb={3{rgb[7:0]}};@(negedge clk);
                end
                de=0;hs=1;repeat(4) @(negedge clk);hs=0;repeat(4) @(negedge clk);
            end
            repeat(300) @(negedge clk);
        end
        if(display_px!=256 || cop_px!=64 || cop_frames!=2) $fatal(1,"FAIL: pipeline counts %0d/%0d/%0d",display_px,cop_px,cop_frames);
        $display("PASS: raw HDMI parallel sync/color passthrough + normalized analysis, 2 snapshots with frame/config IDs");$finish;
    end
    initial begin #100000;$fatal(1,"FAIL: pipeline timeout");end
endmodule
