`timescale 1ns/1ps
module tb_video_real;
    reg clk=0,aclk=0,rst_n=0,vs=0,hs=0,de=0,av=0,wv=0,br=0;
    reg [23:0] rgb=0;
    reg [6:0] addr=0;
    reg [31:0] data=0;
    wire vvs,vhs,vde,cvs,chs,cde;
    wire [23:0] vrgb;
    wire [7:0] cy;
    wire [31:0] fid,cid,drops;
    integer f,l,c,display_px=0,cop_px=0,cop_frames=0,rows=0;
    video_pipeline dut(
        .pclk(clk),.s_axi_aclk(aclk),.rst_n(rst_n),.raw_vs(vs),.raw_hs(hs),.raw_de(de),.raw_rgb(rgb),
        .awvalid(av),.awaddr(addr),.wvalid(wv),.wdata(data),.wstrb(4'hf),.bready(br),
        .arvalid(1'b0),.araddr(7'b0),.rready(1'b1),.cop_ready(1'b1),
        .video_vs(vvs),.video_hs(vhs),.video_de(vde),.video_rgb(vrgb),
        .cop_vs(cvs),.cop_hs(chs),.cop_de(cde),.cop_y(cy),.cop_frame_id(fid),.cop_config_id(cid),.snapshot_drop_count(drops));
    always #5 clk=~clk;
    always #7 aclk=~aclk;
    always @(posedge clk) if(rst_n && dut.pixel_reset) begin
        if(cvs) cop_frames=cop_frames+1;
        if(chs) rows=rows+1;
        if(cde) begin
            if(fid!=cop_frames || cid!=1 || cy!==cop_frames*32+16)
                $fatal(1,"FAIL: real snapshot px=%0d value=%d frame=%d config=%d",cop_px,cy,fid,cid);
            cop_px=cop_px+1;
        end
        #1;
        if({vvs,vhs,vde,vrgb}!=={vs,hs,de,rgb}) $fatal(1,"FAIL: real display waveform");
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
        // 1650x750 总时序：5 行 VS + 20 行前消隐 + 720 有效行 + 5 行后消隐。
        for(f=1;f<=2;f=f+1) begin
            vs=1;repeat(5*1650) @(negedge clk);vs=0;repeat(20*1650) @(negedge clk);
            rgb=f*32+16;rgb={3{rgb[7:0]}};
            for(l=0;l<720;l=l+1) begin
                de=1;repeat(1280) @(negedge clk);de=0;
                repeat(110) @(negedge clk);hs=1;
                repeat(40) @(negedge clk);hs=0;repeat(220) @(negedge clk);
            end
            repeat(5*1650) @(negedge clk);
        end
        // 最后一帧写完后还需 DW*DH + 行消隐拍数回放，不能在输入帧尾截断计数。
        repeat(60000) @(negedge clk);
        if(display_px!=1843200 || cop_px!=100352 || cop_frames!=2 || rows!=448 || drops!=0)
            $fatal(1,"FAIL: real counts display=%0d cop=%0d frames=%0d rows=%0d drops=%0d",display_px,cop_px,cop_frames,rows,drops);
        $display("PASS: 720p timing 2 consecutive frames, 1843200 RGB px + 100352 snapshot px, 448 rows, IDs exact, no drops");$finish;
    end
    initial begin #30000000;$fatal(1,"FAIL: real timeout");end
endmodule
