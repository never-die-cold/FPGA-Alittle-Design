`timescale 1ns/1ps
module tb_int8_requant_pipeline;
    reg clk=0,rst_n=0,ce=1,abort=0,in_valid=0,checking=0;
    reg signed [31:0] accumulator=0;
    reg [31:0] multiplier=1;
    reg [5:0] shift=0;
    reg relu=0;
    wire signed [7:0] result;
    wire out_valid,error;
    reg [7:0] expected,queue_value[0:9999];
    reg queue_error[0:9999];
    reg [7:0] held_result;
    reg held_valid,held_error;
    integer s,r,e,fd,fields,found,ticks=0,sent=0,received=0;
    reg [4095:0] vectors,filename;
    always #5 clk=~clk;
    int8_requant_pipeline dut (.clk(clk),.rst_n(rst_n),.ce(ce),.abort(abort),.in_valid(in_valid),
        .accumulator(accumulator),.multiplier(multiplier),.shift(shift),.relu(relu),
        .result(result),.out_valid(out_valid),.error(error));
    always @(posedge clk) begin
        if(rst_n && !abort && checking) begin
            if(ce && in_valid) begin queue_value[sent]=expected; queue_error[sent]=e[0]; sent=sent+1; end
            #1;
            if(ce && out_valid) begin
                if(received>=sent || result!==queue_value[received] || error!==queue_error[received]) begin
                    $display("FAIL: requant pipeline item=%0d got=%0d expected=%0d error=%b",received,result,$signed(queue_value[received]),error);
                    $fatal(1);
                end
                received=received+1;
            end
            if(!ce && {out_valid,error,result}!=={held_valid,held_error,held_result}) $fatal(1);
            held_result=result; held_valid=out_valid; held_error=error;
        end
    end
    initial begin
        found=$value$plusargs("vectors=%s",vectors); if(!found) $fatal(1);
        $sformat(filename,"%0s/requant.txt",vectors); fd=$fopen(filename,"r"); if(!fd) $fatal(1);
        repeat(3) @(negedge clk); rst_n=1;
        // Abort clears validity even with CE stalled; the discarded result cannot emerge.
        in_valid=1; repeat(2) @(negedge clk);
        in_valid=0; abort=1; ce=0; @(negedge clk); if(out_valid) $fatal(1);
        abort=0; ce=1; checking=1;
        while(!$feof(fd)) begin
            fields=$fscanf(fd,"%h %h %d %d %h %d\n",accumulator,multiplier,s,r,expected,e);
            if(fields!=6) $fatal(1); shift=s; relu=r;
            in_valid=0; ce=1; @(negedge clk);
            in_valid=1; ce=0; @(negedge clk);
            ce=1; @(negedge clk); in_valid=0;
        end
        $fclose(fd); repeat(6) @(negedge clk);
        if(sent!=8075 || received!=sent) $fatal(1);
        $display("PASS: requant pipeline %0d Python golden vectors, bubbles, CE stalls, abort",received);
        $finish;
    end
    initial begin #1000000; $fatal(1); end
endmodule
