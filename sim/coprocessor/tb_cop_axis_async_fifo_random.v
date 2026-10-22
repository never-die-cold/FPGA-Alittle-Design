`timescale 1ns/1ps
module tb_cop_axis_async_fifo_random;
    reg s_clk=0,m_clk=0,s_rst_n=0,m_rst_n=0,s_valid=0,m_ready=0;
    reg [63:0] s_data=0; reg [7:0] s_keep=0; reg s_last=0;
    wire s_ready,m_valid; wire [63:0] m_data; wire [7:0] m_keep; wire m_last;
    integer s_half=5,m_half=7,seed_tx=32'h1badf00d,seed_rx=32'h31415926;
    always begin #(s_half) s_clk=~s_clk; end
    always begin #(m_half) m_clk=~m_clk; end
    cop_axis_async_fifo dut(.s_clk(s_clk),.s_rst_n(s_rst_n),.s_data(s_data),.s_keep(s_keep),
        .s_last(s_last),.s_valid(s_valid),.s_ready(s_ready),.m_clk(m_clk),.m_rst_n(m_rst_n),
        .m_data(m_data),.m_keep(m_keep),.m_last(m_last),.m_valid(m_valid),.m_ready(m_ready));
    task produce; input integer words; integer i,gap;
        begin
            for(i=0;i<words;i=i+1) begin
                gap=($random(seed_tx)&3); repeat(gap) @(negedge s_clk);
                s_data={32'hd15ea5e0,i[31:0]}; s_keep=8'h5a^i[7:0]; s_last=(i%17)==16; s_valid=1;
                while(!s_ready) @(negedge s_clk);
                @(posedge s_clk); @(negedge s_clk); s_valid=0;
            end
        end
    endtask
    task consume; input integer words; integer i;
        begin
            i=0;
            while(i<words) begin
                @(negedge m_clk); m_ready=(($random(seed_rx)&3)!=0);
                if(m_valid && m_ready) begin
                    if(m_data!=={32'hd15ea5e0,i[31:0]} || m_keep!==(8'h5a^i[7:0]) || m_last!==((i%17)==16))
                        $fatal(1,"FIFO duplicate/drop/reorder expected=%0d got=%0d",i,m_data[31:0]);
                    i=i+1;
                end
            end
            @(posedge m_clk); @(negedge m_clk); m_ready=0;
        end
    endtask
    task run_ratio; input integer sh,mh,tag;
        begin
            s_rst_n=0; m_rst_n=0; s_valid=0; m_ready=0; s_half=sh; m_half=mh;
            repeat(5) @(negedge s_clk); repeat(5) @(negedge m_clk); s_rst_n=1; m_rst_n=1;
            fork produce(257); consume(257); join
            $display("PASS: axis_fifo_random ratio%0d Ts:Tm=%0d:%0d preserves 257 beats",tag,2*sh,2*mh);
        end
    endtask
    initial begin
        run_ratio(5,13,0); run_ratio(13,5,1); run_ratio(7,11,2); run_ratio(11,7,3);
        $display("PASS: axis_fifo_random all ratios no duplicate, loss, or reorder"); $finish;
    end
    initial begin #2000000; $fatal(1,"axis_fifo_random timeout"); end
endmodule
