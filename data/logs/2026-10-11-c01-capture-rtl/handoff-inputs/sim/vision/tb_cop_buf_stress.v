`timescale 1ns/1ps
module tb_cop_buf_stress;
    reg clk=0, rst_n=0, in_vs=0, in_hs=0, in_de=0, ready=0;
    reg [7:0] in_y=0;
    reg [31:0] input_id=0;
    wire [31:0] output_id,output_cfg,drops;
    wire vs, hs, de, done, full;
    wire [7:0] y;
    integer pixels=0, frames=0, index=0, expected=0, base=0;
    cop_buf #(.DW(8),.DH(4)) dut (
        .clk(clk),.rst_n(rst_n),.in_vs(in_vs),.in_hs(in_hs),.in_de(in_de),.in_y(in_y),
        .cop_ready(ready),.out_vs(vs),.out_hs(hs),.out_de(de),.out_y(y),
        .frame_done(done),.buf_full(full),.in_frame_id(input_id),.in_config_id(32'd7),
        .out_frame_id(output_id),.out_config_id(output_cfg),.drop_count(drops));
    always #5 clk=~clk;
    always @(posedge clk) if (rst_n) begin
        if (dut.replay && in_de && dut.rd_buf == dut.wr_sel)
            $fatal(1,"FAIL: write overlaps active replay bank");
        if (vs) begin frames=frames+1; index=0; end
        if (de) begin
            if (index==0) begin
                base=y;
                if(output_id!=base || output_cfg!=7) $fatal(1,"FAIL: metadata does not match replay");
            end
            expected=base+index;
            if (y !== expected[7:0]) $fatal(1,"FAIL: mixed frame index=%0d y=%h expected=%h",index,y,expected);
            index=index+1; pixels=pixels+1;
        end
        if (hs && index%8!=0) $fatal(1,"FAIL: hs not at complete row");
    end
    task feed;
        input integer tag;
        input integer collide;
        integer row,col;
        begin
            @(negedge clk); in_vs=1;input_id=tag;
            @(negedge clk); in_vs=0;
            for(row=0;row<4;row=row+1) begin
                for(col=0;col<8;col=col+1) begin
                    in_de=1; in_y=tag+row*8+col; @(negedge clk);
                end
                in_de=0; repeat(3) @(negedge clk);
                in_hs=1;
                if(collide && row==3) ready=1;
                @(negedge clk); in_hs=0; @(negedge clk);
            end
        end
    endtask
    initial begin
        repeat(4) @(negedge clk); rst_n=1;
        feed(16,0);
        feed(80,1); // 读启动与第二帧提交同拍
        feed(144,0);
        repeat(200) @(negedge clk);
        if(pixels<64 || index!=32) $fatal(1,"FAIL: stranded frame pixels=%0d last=%0d",pixels,index);
        // 长期拒收允许丢帧，但恢复后不得回放被写坏或半帧数据。
        ready=0; feed(32,0); feed(96,0); feed(160,0);
        ready=1; repeat(200) @(negedge clk);
        if(index!=32) $fatal(1,"FAIL: incomplete congested replay");
        if(drops==0) $fatal(1,"FAIL: dropped snapshots not reported");
        rst_n=0; repeat(3) @(negedge clk); rst_n=1;
        pixels=0; frames=0; index=0;
        // 复位后残余半帧（没有新 vs）不得发布。
        repeat(4) begin
            in_de=1;repeat(8) @(negedge clk);in_de=0;
            in_hs=1;@(negedge clk);in_hs=0;
        end
        repeat(100) @(negedge clk);
        if(pixels!=0) $fatal(1,"FAIL: orphan half-frame replayed after reset");
        feed(48,0); repeat(100) @(negedge clk);
        if(pixels!=32 || frames!=1) $fatal(1,"FAIL: reset replay %0d/%0d",pixels,frames);
        $display("PASS: cop_buf distinct frames, simultaneous start/commit, congestion, drain and reset");
        $finish;
    end
    initial begin #100000; $fatal(1,"FAIL: timeout"); end
endmodule
