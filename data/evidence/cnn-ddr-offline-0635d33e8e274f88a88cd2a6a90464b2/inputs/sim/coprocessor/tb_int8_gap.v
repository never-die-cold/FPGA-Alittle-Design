`timescale 1ns/1ps
module tb_int8_gap;
    reg [31:0] total;
    reg [7:0] expected;
    wire signed [7:0] result;
    wire error;
    integer e, fd, fields, checks, found;
    reg [4095:0] vectors, filename;
    int8_gap dut (.total(total), .result(result), .error(error));
    initial begin
        found=$value$plusargs("vectors=%s",vectors); if (!found) $fatal(1);
        $sformat(filename,"%0s/gap.txt",vectors); fd=$fopen(filename,"r"); if (!fd) $fatal(1);
        checks=0;
        while (!$feof(fd)) begin
            fields=$fscanf(fd,"%h %h %d\n",total,expected,e); if (fields != 3) $fatal(1);
            #1;
            if (result !== expected || error !== e[0]) begin
                $display("FAIL: GAP sum=%0d result=%0d expected=%0d",total,result,expected); $fatal(1);
            end
            checks=checks+1;
        end
        $fclose(fd); if (checks != 32515) $fatal(1);
        $display("PASS: int8_gap all 32513 legal sums and invalid sums; Python golden"); $finish;
    end
endmodule
