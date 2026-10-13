`timescale 1ns/1ps
module tb_mac_array_pipeline;
    reg clk=0,rst_n=0,ce=1,abort=0,in_valid=0;
    reg [63:0] activation_lanes=0;
    reg [1023:0] weight_lanes=0;
    reg [511:0] accumulator_lanes=0;
    wire [511:0] result_lanes;
    wire [15:0] overflow;
    wire out_valid;
    reg [511:0] expected[0:299],held_result;
    reg [15:0] expected_overflow[0:299],held_overflow;
    reg held_valid;
    reg signed [63:0] total;
    integer seed=32'h31a9,trial,i,o,sent=0,received=0;
    always #5 clk=~clk;
    mac_array_pipeline dut (.clk(clk),.rst_n(rst_n),.ce(ce),.abort(abort),.in_valid(in_valid),
        .activation_lanes(activation_lanes),.weight_lanes(weight_lanes),.accumulator_lanes(accumulator_lanes),
        .result_lanes(result_lanes),.overflow(overflow),.out_valid(out_valid));
    always @(posedge clk) if(rst_n && !abort) begin
        if(ce && in_valid) begin
            for(o=0;o<16;o=o+1) begin
                total=$signed(accumulator_lanes[o*32 +: 32]);
                for(i=0;i<8;i=i+1) total=total+$signed(activation_lanes[i*8 +: 8])*$signed(weight_lanes[(o*8+i)*8 +: 8]);
                expected[sent][o*32 +: 32]=total[31:0];
                expected_overflow[sent][o]=total>64'sd2147483647 || total < -64'sd2147483648;
            end
            sent=sent+1;
        end
        #1;
        if(ce && out_valid) begin
            if(received>=sent || result_lanes!==expected[received] || overflow!==expected_overflow[received]) begin
                $display("FAIL: MAC pipeline item=%0d",received); $fatal(1);
            end
            received=received+1;
        end
        if(!ce && {out_valid,overflow,result_lanes}!=={held_valid,held_overflow,held_result}) $fatal(1);
        held_valid=out_valid; held_overflow=overflow; held_result=result_lanes;
    end
    integer a,b;
    initial begin
        repeat(3) @(negedge clk); rst_n=1;
        for(trial=0;trial<267;trial=trial+1) begin
            for(a=0;a<8;a=a+1) activation_lanes[a*8 +: 8]=($random(seed)&32'h7fffffff)%255-127;
            for(a=0;a<16;a=a+1) begin
                accumulator_lanes[a*32 +: 32]=$random(seed);
                for(b=0;b<8;b=b+1) weight_lanes[(a*8+b)*8 +: 8]=($random(seed)&32'h7fffffff)%255-127;
            end
            if(trial<8) begin
                activation_lanes=0; activation_lanes[trial*8 +: 8]=7; accumulator_lanes=0;
                for(a=0;a<16;a=a+1) for(b=0;b<8;b=b+1) weight_lanes[(a*8+b)*8 +: 8]=(a-8)*(b+1);
            end
            if(trial>=264) begin
                activation_lanes={8{trial==265 ? 8'h81 : trial==266 ? 8'd0 : 8'd127}};
                weight_lanes={128{8'd127}};
                accumulator_lanes={16{trial==264 ? 32'h7fffffff : 32'h80000000}};
            end
            ce=trial%5!=2; in_valid=1;
            if(!ce) begin @(negedge clk); ce=1; end
            @(negedge clk);
            if(trial%7==0) begin in_valid=0; @(negedge clk); end
        end
        in_valid=0; repeat(6) @(negedge clk);
        if(received!=267 || sent!=received) $fatal(1);
        in_valid=1; @(negedge clk); @(negedge clk); in_valid=0; abort=1; ce=0;
        @(negedge clk); if(out_valid) $fatal(1); abort=0; ce=1;
        repeat(6) @(negedge clk); if(out_valid) $fatal(1);
        $display("PASS: MAC pipeline 4272 lane results, streaming, signs, overflow, stalls and abort");
        $finish;
    end
endmodule
