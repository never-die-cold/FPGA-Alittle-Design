`timescale 1ns/1ps
module tb_conv_engine;
    reg clk=0, rst_n=0, ce=1, start=0;
    reg [6:0] cfg_ci, cfg_co, cfg_width, cfg_height;
    reg [1:0] cfg_kernel, cfg_stride, cfg_padding;
    reg cfg_relu;
    reg [31:0] cfg_cycle_limit;
    wire ready, busy, done, error, memory_enable, parameter_enable, write_enable;
    wire [31:0] cycles;
    wire [15:0] input_address, weight_address, write_address;
    wire [1:0] output_block;
    wire [63:0] write_data;
    reg [63:0] input_data;
    reg [1023:0] weight_data;
    reg [511:0] bias_data, multiplier_data;
    reg [95:0] shift_data;
    reg [63:0] input_memory [0:32767], expected_memory [0:32767];
    reg [1023:0] weight_memory [0:1023];
    reg [31:0] biases [0:63], multipliers [0:63];
    reg [5:0] shifts [0:63];
    reg visited [0:32767];
    integer tb_cycles=0, written=0, reads=0, fault=0;
    integer ci, co, h, w, k, s, p, r, in_words, weight_words, out_words;
    integer fd, fields, lane, index, found, faults;
    reg [4095:0] folder, filename;
    always #5 clk=~clk;
    always @(negedge clk) begin tb_cycles=tb_cycles+1; ce=(tb_cycles%7)!=3; end
    conv_engine dut (.clk(clk), .rst_n(rst_n), .ce(ce), .start(start), .abort(1'b0),
        .cfg_ci(cfg_ci), .cfg_co(cfg_co), .cfg_width(cfg_width), .cfg_height(cfg_height),
        .cfg_kernel(cfg_kernel), .cfg_stride(cfg_stride), .cfg_padding(cfg_padding),
        .cfg_relu(cfg_relu), .cfg_cycle_limit(cfg_cycle_limit), .ready(ready),
        .busy(busy), .done(done), .error(error), .cycles(cycles),
        .memory_enable(memory_enable), .input_address(input_address), .weight_address(weight_address),
        .input_data(input_data), .weight_data(weight_data), .parameter_enable(parameter_enable),
        .output_block(output_block), .bias_data(bias_data), .multiplier_data(multiplier_data),
        .shift_data(shift_data), .write_enable(write_enable), .write_address(write_address), .write_data(write_data));
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin input_data<=0; weight_data<=0; bias_data<=0; multiplier_data<=0; shift_data<=0; end
        else begin
            if (memory_enable) begin
                if (input_address >= in_words || weight_address >= weight_words) begin
                    $display("FAIL: address input=%0d weight=%0d",input_address,weight_address); $fatal(1);
                end
                input_data<=fault==2 ? {8{8'd127}} : input_memory[input_address];
                weight_data<=fault==2 ? {128{8'd127}} : weight_memory[weight_address];
                reads=reads+1;
            end
            if (parameter_enable) for (lane=0; lane<16; lane=lane+1) begin
                bias_data[lane*32 +: 32]<=fault==2 ? 32'h7fffffff : biases[output_block*16+lane];
                multiplier_data[lane*32 +: 32]<=fault==1 ? 0 : multipliers[output_block*16+lane];
                shift_data[lane*6 +: 6]<=shifts[output_block*16+lane];
            end
            if (write_enable) begin
                if (fault || write_address>=out_words || visited[write_address]
                    || write_data !== expected_memory[write_address]) begin
                    $display("FAIL: output address=%0d got=%h expected=%h fault=%0d",
                        write_address,write_data,expected_memory[write_address],fault); $fatal(1);
                end
                visited[write_address]=1; written=written+1;
            end
        end
    end
    task launch;
        begin
            written=0; reads=0;
            for (index=0; index<out_words; index=index+1) visited[index]=0;
            @(negedge clk); #1;
            while (!ready) begin @(negedge clk); #1; end
            start=1; @(posedge clk); #1; start=0;
        end
    endtask
    task finish_run;
        input expect_error;
        begin
            while (busy) begin @(posedge clk); #1; end
            if (error !== expect_error || done !== !expect_error) begin
                $display("FAIL: completion error=%b done=%b expected_error=%b",error,done,expect_error); $fatal(1);
            end
            if (!expect_error && written != out_words) $fatal(1);
            if (expect_error && written != 0) $fatal(1);
        end
    endtask
    initial begin
        found=$value$plusargs("case=%s",folder); if (!found) $fatal(1);
        faults=$test$plusargs("fault_tests");
        $sformat(filename,"%0s/config.txt",folder); fd=$fopen(filename,"r"); if (!fd) $fatal(1);
        fields=$fscanf(fd,"%d %d %d %d %d %d %d %d %d %d %d\n",
            ci,co,h,w,k,s,p,r,in_words,weight_words,out_words); $fclose(fd); if (fields!=11) $fatal(1);
        cfg_ci=ci; cfg_co=co; cfg_height=h; cfg_width=w; cfg_kernel=k;
        cfg_stride=s; cfg_padding=p; cfg_relu=r; cfg_cycle_limit=1000000;
        $sformat(filename,"%0s/input.hex",folder); $readmemh(filename,input_memory,0,in_words-1);
        $sformat(filename,"%0s/weights.hex",folder); $readmemh(filename,weight_memory,0,weight_words-1);
        $sformat(filename,"%0s/expected.hex",folder); $readmemh(filename,expected_memory,0,out_words-1);
        $sformat(filename,"%0s/bias.hex",folder); $readmemh(filename,biases,0,63);
        $sformat(filename,"%0s/multipliers.hex",folder); $readmemh(filename,multipliers,0,63);
        $sformat(filename,"%0s/shifts.hex",folder); $readmemh(filename,shifts,0,63);
        repeat(3) @(negedge clk); rst_n=1;
        launch; finish_run(0);
        $display("PASS: conv_engine case=%0s words=%0d read_transactions=%0d cycles=%0d; every pixel/lane matches Python",folder,written,reads,cycles);
        if (faults) begin
            fault=1; launch; finish_run(1);
            fault=2; launch; finish_run(1);
            fault=0; cfg_ci=2; launch; finish_run(1); if (reads) $fatal(1); cfg_ci=ci;
            cfg_cycle_limit=2; launch; finish_run(1); cfg_cycle_limit=1000000;
            launch; repeat(10) @(negedge clk); rst_n=0; #1;
            if (busy || done || error || write_enable || memory_enable) $fatal(1);
            repeat(2) @(negedge clk); rst_n=1; launch; finish_run(0);
            $display("PASS: conv_engine bad requant/overflow/config/watchdog/reset recovery; ce stalls tested");
        end
        $finish;
    end
    initial begin #30000000; $display("FAIL: conv_engine simulation timeout"); $fatal(1); end
endmodule
