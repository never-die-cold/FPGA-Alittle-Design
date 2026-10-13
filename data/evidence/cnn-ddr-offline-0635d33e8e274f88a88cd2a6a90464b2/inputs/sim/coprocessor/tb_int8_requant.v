`timescale 1ns/1ps
module tb_int8_requant;
    reg signed [31:0] accumulator;
    reg [31:0] multiplier;
    reg [5:0] shift;
    reg relu;
    wire signed [7:0] result;
    wire error;
    reg [7:0] expected;
    integer s, r, e, fd, fields, checks, found;
    reg [4095:0] vectors, filename;
    int8_requant dut (.accumulator(accumulator), .multiplier(multiplier), .shift(shift),
        .relu(relu), .result(result), .error(error));
    initial begin
        found=$value$plusargs("vectors=%s", vectors); if (!found) $fatal(1);
        $sformat(filename, "%0s/requant.txt", vectors); fd=$fopen(filename,"r"); if (!fd) $fatal(1);
        checks=0;
        while (!$feof(fd)) begin
            fields=$fscanf(fd,"%h %h %d %d %h %d\n", accumulator, multiplier, s, r, expected, e);
            if (fields != 6) $fatal(1);
            shift=s; relu=r; #1;
            if (result !== expected || error !== e[0]) begin
                $display("FAIL: requant acc=%0d mult=%0d shift=%0d relu=%0d got=%0d expected=%0d",
                    accumulator, multiplier, s, r, result, $signed(expected)); $fatal(1);
            end
            checks=checks+1;
        end
        $fclose(fd); if (checks < 8000) $fatal(1);
        $display("PASS: int8_requant %0d Python-golden vectors; rounding, saturation, ReLU, invalid params", checks);
        $finish;
    end
endmodule
