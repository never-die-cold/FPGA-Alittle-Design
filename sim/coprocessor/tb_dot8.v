`timescale 1ns / 1ps
module tb_dot8;
    reg  [63:0] act_i;
    reg  [63:0] weight_i;
    wire signed [18:0] sum_o;
    integer lane;
    integer checks;

    dot8 dut (.act_i(act_i), .weight_i(weight_i), .sum_o(sum_o));

    task set_lane;
        input integer index;
        input signed [7:0] act;
        input signed [7:0] weight;
        begin
            act_i[8*index +: 8] = act;
            weight_i[8*index +: 8] = weight;
        end
    endtask

    task check_sum;
        input signed [18:0] expected;
        begin
            #1;
            if (sum_o !== expected)
                $fatal(1, "dot8 sum=%0d expected=%0d", sum_o, expected);
            checks = checks + 1;
        end
    endtask

    initial begin
        checks = 0;
        act_i = 0; weight_i = 0;
        check_sum(19'sd0);
        for (lane = 0; lane < 8; lane = lane + 1)
            set_lane(lane, 8'sd127, 8'sd127);
        check_sum(19'sd129032);
        for (lane = 0; lane < 8; lane = lane + 1)
            set_lane(lane, -8'sd127, 8'sd127);
        check_sum(-19'sd129032);
        for (lane = 0; lane < 8; lane = lane + 1)
            set_lane(lane, 8'h80, 8'h80);
        check_sum(19'sd131072);
        for (lane = 0; lane < 8; lane = lane + 1)
            set_lane(lane, 8'h80, 8'sd127);
        check_sum(-19'sd130048);
        set_lane(0, 8'sd1, 8'sd1);     set_lane(1, -8'sd2, 8'sd3);
        set_lane(2, 8'sd4, -8'sd5);    set_lane(3, -8'sd6, -8'sd7);
        set_lane(4, 8'sd8, 8'sd9);     set_lane(5, -8'sd10, 8'sd11);
        set_lane(6, 8'sd12, -8'sd13);  set_lane(7, -8'sd14, -8'sd15);
        check_sum(19'sd33);
        $display("PASS: dot8 balanced signed reduction (%0d vectors)", checks);
        $finish;
    end
endmodule
