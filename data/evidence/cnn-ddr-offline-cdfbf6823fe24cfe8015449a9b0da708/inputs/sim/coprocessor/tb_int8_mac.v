`timescale 1ns/1ps
module tb_int8_mac;
    reg signed [7:0] activation, weight;
    reg signed [31:0] accumulator;
    wire signed [31:0] result;
    wire overflow;
    integer a, w, checks;
    int8_mac dut (.activation(activation), .weight(weight),
        .accumulator(accumulator), .result(result), .overflow(overflow));
    task check;
        input integer av, wv;
        input signed [31:0] bias;
        reg signed [63:0] expected;
        reg expected_overflow;
        begin
            activation = av; weight = wv; accumulator = bias;
            expected = bias;
            expected = expected + av * wv;
            expected_overflow = expected > 64'sd2147483647 || expected < -64'sd2147483648;
            #1;
            if (result !== expected[31:0] || overflow !== expected_overflow) begin
                $display("FAIL: MAC a=%0d w=%0d acc=%0d result=%0d overflow=%b expected=%0d",
                    av, wv, bias, result, overflow, expected);
                $fatal(1);
            end
            checks = checks + 1;
        end
    endtask
    initial begin
        checks = 0;
        // Independent wide oracle; exhaust all legal input/weight pairs.
        for (a = -127; a <= 127; a = a + 1)
            for (w = -127; w <= 127; w = w + 1)
                check(a, w, (a ^ w) * 1048576);
        check(127, 127, 0); check(127, -127, 0);
        check(-127, -127, -19); check(-127, 127, 19);
        check(1, 1, 32'sh7fffffff); check(-1, 1, 32'sh80000000);
        check(127, 127, 32'sh7fffffff); check(-127, 127, 32'sh80000000);
        check(0, 127, 32'sh80000000); check(-1, -1, 32'sh80000000);
        $display("PASS: int8_mac %0d vectors; signed product/addition and overflow", checks);
        $finish;
    end
endmodule
