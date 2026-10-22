`timescale 1ns/1ps
// 16-entry AXI-stream CDC FIFO for {last,keep,data}; Gray pointers cross clock domains.
module cop_axis_async_fifo (
    input wire s_clk, s_rst_n, input wire [63:0] s_data,
    input wire [7:0] s_keep, input wire s_last, s_valid, output wire s_ready,
    input wire m_clk, m_rst_n, output wire [63:0] m_data,
    output wire [7:0] m_keep, output wire m_last, output wire m_valid, input wire m_ready
);
    reg [72:0] mem [0:15];
    reg [4:0] wbin,wgray,rbin,rgray;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [4:0] rgray_s1,rgray_s2,wgray_m1,wgray_m2;
    reg [72:0] out_data; reg out_valid,full,mem_empty;
    wire write_fire=s_valid && !full;
    wire [4:0] wbin_next=wbin+write_fire;
    wire [4:0] wgray_next=(wbin_next>>1)^wbin_next;
    wire full_next=wgray_next=={~rgray_s2[4:3],rgray_s2[2:0]};
    wire read_load=(!out_valid || m_ready) && !mem_empty;
    wire [4:0] rbin_next=rbin+read_load;
    wire [4:0] rgray_next=(rbin_next>>1)^rbin_next;
    wire empty=mem_empty;
    assign s_ready=!full;
    assign {m_last,m_keep,m_data}=out_data;
    assign m_valid=out_valid;
    always @(posedge s_clk or negedge s_rst_n) begin
        if(!s_rst_n) begin wbin<=0; wgray<=0; rgray_s1<=0; rgray_s2<=0; full<=0; end
        else begin
            rgray_s1<=rgray; rgray_s2<=rgray_s1;
            if(write_fire) mem[wbin[3:0]]<={s_last,s_keep,s_data};
            wbin<=wbin_next; wgray<=wgray_next; full<=full_next;
        end
    end
    always @(posedge m_clk or negedge m_rst_n) begin
        if(!m_rst_n) begin
            rbin<=0; rgray<=0; wgray_m1<=0; wgray_m2<=0; out_data<=0; out_valid<=0; mem_empty<=1;
        end
        else begin
            wgray_m1<=wgray; wgray_m2<=wgray_m1;
            rbin<=rbin_next; rgray<=rgray_next; mem_empty<=rgray_next==wgray_m2;
            if(read_load) begin out_data<=mem[rbin[3:0]]; out_valid<=1; end
            else if(out_valid && m_ready) out_valid<=0;
        end
    end
endmodule
