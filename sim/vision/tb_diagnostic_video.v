`timescale 1ns/1ps
// Independent clamped-border integer reference. Compact uses changing RGB;
// 720p uses frame-distinct flat fields to keep the full raster test fast.
module diagnostic_case #(parameter W=16,H=8,HT=32,REAL=0)(output reg done=0);
    localparam DELAY=3*HT+18;
    reg clk=0,aclk=0,rst=0,vs=0,hs=0,de=0,av=0,wv=0;
    reg [23:0] rgb=0;
    reg [6:0] addr=0;
    reg [31:0] wd=0;
    wire ov,oh,od,bv;
    wire [23:0] out;
    integer f,l,c,mode=0,next_mode=0,ptr=0,checks=0,frames=0,pass=0;
    reg [26:0] history[0:DELAY-1];
    reg [26:0] expected;
    reg started=0,prev_vs=0;
    event change_mode;
    always #(REAL?6.734:5) clk=~clk;
    always #7 aclk=~aclk;
    video_pipeline #(.SW(W),.SH(H),.DW(8),.DH(4),.NLINES(8),.ENABLE_DIAGNOSTIC(1),.H_TOTAL(HT)) dut(
        .pclk(clk),.s_axi_aclk(aclk),.rst_n(rst),.axi_rst_n(rst),.raw_vs(vs),.raw_hs(hs),.raw_de(de),.raw_rgb(rgb),
        .awvalid(av),.awaddr(addr),.wvalid(wv),.wdata(wd),.wstrb(4'hf),.bready(1'b1),.bvalid(bv),
        .arvalid(1'b0),.araddr(7'b0),.rready(1'b1),.cop_ready(1'b1),
        .video_vs(ov),.video_hs(oh),.video_de(od),.video_rgb(out));
    function [23:0] color;
        input integer x,y,frame;
        reg [7:0] r,g,b;
        begin
            if(REAL) begin r=40+frame*23;g=70+frame*19;b=110+frame*13;end
            else begin r=(x*43+y*17+frame*29)%256;g=(x*11+y*57+frame*19)%256;b=(x*71+y*7+frame*37)%256;end
            color={r,g,b};
        end
    endfunction
    function integer gray;
        input integer x,y,frame;
        reg [23:0] px;
        begin
            if(x<0)x=0;if(x>=W)x=W-1;if(y<0)y=0;if(y>=H)y=H-1;
            px=color(x,y,frame);gray=(77*px[23:16]+150*px[15:8]+29*px[7:0])/256;
        end
    endfunction
    function integer gauss;
        input integer x,y,frame;
        integer a,b,sum,weight;
        begin
            if(x<0)x=0;if(x>=W)x=W-1;if(y<0)y=0;if(y>=H)y=H-1;
            sum=0;
            for(a=-1;a<=1;a=a+1) for(b=-1;b<=1;b=b+1) begin
                weight=((a==0)?2:1)*((b==0)?2:1);sum=sum+weight*gray(x+b,y+a,frame);
            end
            gauss=sum/16;
        end
    endfunction
    function [23:0] golden;
        input integer x,y,frame,view;
        integer gx,gy,v;
        begin
            if(view==0) golden=color(x,y,frame);
            else begin
                if(view==1 || REAL) v=gray(x,y,frame);
                else if(view==2) v=gauss(x,y,frame);
                else begin
                    gx=-gauss(x-1,y-1,frame)+gauss(x+1,y-1,frame)-2*gauss(x-1,y,frame)+2*gauss(x+1,y,frame)-gauss(x-1,y+1,frame)+gauss(x+1,y+1,frame);
                    gy=-gauss(x-1,y-1,frame)-2*gauss(x,y-1,frame)-gauss(x+1,y-1,frame)+gauss(x-1,y+1,frame)+2*gauss(x,y+1,frame)+gauss(x+1,y+1,frame);
                    v=((gx<0)?-gx:gx)+((gy<0)?-gy:gy);if(v>255)v=255;
                end
                if(REAL && view==3)v=0;
                golden={3{v[7:0]}};
            end
        end
    endfunction
    task write;
        input [6:0] a;input [31:0] d;
        begin
            @(negedge aclk);addr=a;wd=d;av=1;wv=1;
            @(negedge aclk);av=0;wv=0;wait(bv);repeat(3) @(negedge aclk);
        end
    endtask
    task configure;
        input integer v;
        begin
            case(v) 0:write(0,0);1:write(0,16);2:write(0,17);3:write(0,25);endcase
            write(44,1);
        end
    endtask
    initial forever begin @change_mode;configure(next_mode);end
    always @(posedge clk) begin
        if(!rst) begin ptr=0;started=0;prev_vs=0;end
        else begin
            expected=history[ptr];history[ptr]={vs,hs,de,(de?golden(c,l-25,f,mode):24'b0)};
            ptr=(ptr==DELAY-1)?0:ptr+1;
            #1;
            if(ov && !prev_vs) begin started=1;frames=frames+1;end
            prev_vs=ov;
            if(started) begin
                if({ov,oh,od,out}!==expected)
                    $fatal(1,"FAIL: diagnostic REAL=%0d mode=%0d pixel=%0d got=%h expected=%h",REAL,mode,checks,{ov,oh,od,out},expected);
                if(od)checks=checks+1;
            end
        end
    end
    initial begin
        // Two complete four-view rounds with lock/reset loss between rounds.
        for(pass=0;pass<2;pass=pass+1) begin
            rst=0;vs=0;hs=0;de=0;repeat(5) @(negedge clk);
            rst=1;repeat(8) @(negedge clk);configure(0);repeat(8) @(negedge clk);
            for(f=0;f<4;f=f+1) begin
                mode=f;
                for(l=0;l<H+30;l=l+1) begin
                    for(c=0;c<HT;c=c+1) begin
                        vs=(l<5);hs=(c>=W+(REAL?110:2) && c<W+(REAL?150:6));de=(l>=25 && l<25+H && c<W);
                        rgb=de?color(c,l-25,f):0;
                        if(l==25+H/2 && c==W/2 && f<3) begin next_mode=f+1;->change_mode;end
                        @(negedge clk);
                    end
                end
            end
            vs=0;hs=0;de=0;repeat(DELAY+8) @(negedge clk);
            if(checks!=(pass+1)*4*W*H) $fatal(1,"FAIL: diagnostic pixel counts %0d",checks);
        end
        if(frames!=8) $fatal(1,"FAIL: diagnostic frame count %0d",frames);
        $display("PASS: diagnostic REAL=%0d COLOR/GRAY/GAUSS/EDGE, %0d pixels, full sync, frame-atomic switches and reset recovery",REAL,checks);
        done=1;
    end
endmodule
module tb_diagnostic_video;
    wire done;
    diagnostic_case test(done);
    initial begin wait(done);$finish;end
    initial begin #1000000;$fatal(1,"FAIL: diagnostic timeout");end
endmodule
