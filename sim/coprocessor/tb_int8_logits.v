`timescale 1ns/1ps
module tb_int8_logits;
    reg [23:0] logits;
    reg [7:0] min_margin;
    wire [1:0] class_id;
    wire [7:0] margin_q;
    wire [14:0] score_q15;
    wire low_conf, error;
    reg [7:0] a, b, c;
    integer threshold, cls, margin, score, low, e, fd, fields, checks, found;
    reg [4095:0] vectors, filename;
    int8_logits dut (.logits(logits), .min_margin(min_margin), .class_id(class_id),
        .margin_q(margin_q), .score_q15(score_q15), .low_conf(low_conf), .error(error));
    initial begin
        found=$value$plusargs("vectors=%s",vectors); if (!found) $fatal(1);
        $sformat(filename,"%0s/logits.txt",vectors); fd=$fopen(filename,"r"); if (!fd) $fatal(1);
        checks=0;
        while (!$feof(fd)) begin
            fields=$fscanf(fd,"%h %h %h %d %d %d %d %d %d\n",a,b,c,threshold,cls,margin,score,low,e);
            if (fields != 9) $fatal(1);
            logits={c,b,a}; min_margin=threshold; #1;
            if (class_id !== cls[1:0] || margin_q !== margin[7:0] || score_q15 !== score[14:0]
                || low_conf !== low[0] || error !== e[0]) begin
                $display("FAIL: logits %0d/%0d/%0d threshold=%0d",$signed(a),$signed(b),$signed(c),threshold); $fatal(1);
            end
            checks=checks+1;
        end
        $fclose(fd); if (checks < 2800) $fatal(1);
        $display("PASS: int8_logits %0d Python-golden vectors; ties, all margins, low confidence, invalid INT8", checks);
        $finish;
    end
endmodule
