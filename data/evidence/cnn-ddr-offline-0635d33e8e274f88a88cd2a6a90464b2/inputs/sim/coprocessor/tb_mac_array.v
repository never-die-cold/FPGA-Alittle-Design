`timescale 1ns/1ps
module tb_mac_array;
    reg [63:0] activation_lanes;
    reg [1023:0] weight_lanes;
    reg [511:0] accumulator_lanes;
    wire [511:0] result_lanes;
    wire [15:0] overflow;
    integer seed, trial, i, o, hot, checks;
    reg signed [63:0] expected;
    reg expected_overflow;
    mac_array dut (.activation_lanes(activation_lanes), .weight_lanes(weight_lanes),
        .accumulator_lanes(accumulator_lanes), .result_lanes(result_lanes), .overflow(overflow));
    task compare;
        begin
            #1;
            for (o=0; o<16; o=o+1) begin
                expected = $signed(accumulator_lanes[o*32 +: 32]);
                for (i=0; i<8; i=i+1)
                    expected = expected + $signed(activation_lanes[i*8 +: 8])
                                        * $signed(weight_lanes[(o*8+i)*8 +: 8]);
                expected_overflow = expected > 64'sd2147483647 || expected < -64'sd2147483648;
                if (result_lanes[o*32 +: 32] !== expected[31:0] || overflow[o] !== expected_overflow) begin
                    $display("FAIL: MAC array output=%0d expected=%0d", o, expected); $fatal(1);
                end
                checks=checks+1;
            end
        end
    endtask
    initial begin
        seed=32'h31a9; checks=0;
        // Basis inputs independently check C02's O16/I8 packed lane order.
        for (hot=0; hot<8; hot=hot+1) begin
            activation_lanes=0; activation_lanes[hot*8 +: 8]=7; accumulator_lanes=0;
            for (o=0; o<16; o=o+1)
                for (i=0; i<8; i=i+1) weight_lanes[(o*8+i)*8 +: 8]=(o-8)*(i+1);
            #1;
            for (o=0; o<16; o=o+1)
                if ($signed(result_lanes[o*32 +: 32]) !== 7*(o-8)*(hot+1) || overflow[o]) $fatal(1);
            compare;
        end
        for (trial=0; trial<256; trial=trial+1) begin
            for (i=0; i<8; i=i+1) activation_lanes[i*8 +: 8]=($random(seed)&32'h7fffffff)%255-127;
            for (o=0; o<16; o=o+1) begin
                accumulator_lanes[o*32 +: 32]=$random(seed);
                for (i=0; i<8; i=i+1) weight_lanes[(o*8+i)*8 +: 8]=($random(seed)&32'h7fffffff)%255-127;
            end
            compare;
        end
        activation_lanes={8{8'd127}}; weight_lanes={128{8'd127}};
        accumulator_lanes={16{32'h7fffffff}}; compare;
        activation_lanes={8{8'h81}}; accumulator_lanes={16{32'h80000000}}; compare;
        activation_lanes=0; compare;
        $display("PASS: mac_array %0d output vectors; O16/I8 packing, signs, overflow", checks);
        $finish;
    end
endmodule
