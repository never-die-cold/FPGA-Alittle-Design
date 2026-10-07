`timescale 1ns/1ps
module tb_diagnostic_720;
    wire done;
    diagnostic_case #(.W(1280),.H(720),.HT(1650),.REAL(1)) test(done);
    initial begin wait(done);$finish;end
    initial begin #170000000;$fatal(1,"FAIL: diagnostic 720 timeout");end
endmodule
