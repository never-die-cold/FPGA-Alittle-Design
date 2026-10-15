`timescale 1ns / 1ps
module tb_mac_lane;
    reg  signed [7:0]  act_i;
    reg  signed [7:0]  weight_i;
    wire signed [15:0] product_o;
    integer checks;

    mac_lane dut (
        .act_i(act_i),
        .weight_i(weight_i),
        .product_o(product_o)
    );

    task check_product;
        input signed [7:0] test_act;
        input signed [7:0] test_weight;
        input signed [15:0] expected;
        begin
            act_i = test_act;
            weight_i = test_weight;
            #1;
            if (product_o !== expected)
                $fatal(1, "mac_lane: %0d * %0d = %0d, expected %0d",
                       test_act, test_weight, product_o, expected);
            checks = checks + 1;
        end
    endtask

    initial begin
        checks = 0;
        check_product(8'sd0,    -8'sd127,  16'sd0);
        check_product(8'sd127,   8'sd127,  16'sd16129);
        check_product(-8'sd127,  8'sd127, -16'sd16129);
        check_product(-8'sd127, -8'sd127,  16'sd16129);
        check_product(8'h80,     8'h80,     16'sd16384);
        check_product(8'h80,     8'sd127,  -16'sd16256);
        check_product(8'sd1,    -8'sd1,    -16'sd1);
        $display("PASS: mac_lane signed INT8 products (%0d vectors)", checks);
        $finish;
    end
endmodule
