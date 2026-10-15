`timescale 1ns/1ps
module tb_cnn_sequencer;
    reg clk=0,rst_n=0,ce=1,start=0,force_pause=0;
    reg [7:0] min_margin;
    reg [31:0] cycle_limit=2000000;
    wire ready,busy,done,error,low_conf;
    wire [2:0] error_layer;
    wire [31:0] cycles;
    wire [1:0] classification,read_bank,write_bank;
    wire [7:0] margin,parameter_address;
    wire [14:0] score;
    wire [23:0] logits;
    wire memory_enable,weight_enable,parameter_enable,write_enable;
    wire [15:0] read_address,weight_address,write_address;
    wire [63:0] write_data;
    reg [63:0] input_data;
    reg [1023:0] weight_data;
    reg [511:0] bias_data,multiplier_data;
    reg [95:0] shift_data;
    reg [7:0] roi [0:4095];
    reg [63:0] ping [0:4095],pong [0:2047],gap [0:7];
    reg [1023:0] weights [0:268];
    reg [31:0] biases [0:159],multipliers [0:159];
    reg [5:0] shifts [0:159];
    reg [63:0] golden [0:16392];
    reg visited [0:16392];
    integer written=0,reads=0,weight_reads=0,parameter_reads=0,tb_cycles=0,fault=0;
    integer lane,index,position,fd,fields,cls_expected,margin_expected,score_expected,low_expected,threshold;
    integer found,faults;
    reg [4095:0] model_folder,folder,filename;
    always #5 clk=~clk;
    always @(negedge clk) begin tb_cycles=tb_cycles+1; ce=!force_pause && (tb_cycles%7)!=3; end
    cnn_sequencer dut (.clk(clk),.rst_n(rst_n),.ce(ce),.start(start),.min_margin(min_margin),
        .cycle_limit(cycle_limit),.ready(ready),.busy(busy),.done(done),.error(error),.error_layer(error_layer),
        .cycles(cycles),.result_class(classification),.result_margin(margin),.result_score(score),
        .result_low_conf(low_conf),.result_logits(logits),.memory_enable(memory_enable),.weight_enable(weight_enable),
        .parameter_enable(parameter_enable),.read_bank(read_bank),.read_address(read_address),
        .weight_address(weight_address),.parameter_address(parameter_address),.input_data(input_data),
        .weight_data(weight_data),.bias_data(bias_data),.multiplier_data(multiplier_data),.shift_data(shift_data),
        .write_enable(write_enable),.write_bank(write_bank),.write_address(write_address),.write_data(write_data));
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin input_data<=0; weight_data<=0; bias_data<=0; multiplier_data<=0; shift_data<=0; end
        else begin
            if(memory_enable) begin
                case(read_bank)
                    0: begin if(read_address>=4096) $fatal(1); input_data<={56'd0,roi[read_address]}; end
                    1: begin if(read_address>=4096) $fatal(1); input_data<=ping[read_address]; end
                    2: begin if(read_address>=2048) $fatal(1); input_data<=pong[read_address]; end
                    3: begin if(read_address>=8) $fatal(1); input_data<=gap[read_address]; end
                endcase
                if(fault==3 && !weight_enable && read_bank==1) input_data<=64'h80;
                reads=reads+1;
            end
            if(weight_enable) begin
                if(weight_address>=269) $fatal(1); weight_data<=weights[weight_address]; weight_reads=weight_reads+1;
            end
            if(parameter_enable) begin
                parameter_reads=parameter_reads+1;
                if(parameter_address+15>=160) $fatal(1);
                for(lane=0;lane<16;lane=lane+1) begin
                    bias_data[lane*32 +: 32]<=biases[parameter_address+lane];
                    multiplier_data[lane*32 +: 32]<=fault==1 ? 0 : multipliers[parameter_address+lane];
                    shift_data[lane*6 +: 6]<=shifts[parameter_address+lane];
                end
            end
            if(write_enable) begin
                position=dut.layer*4096+write_address;
                if(write_bank==3) position=16384+write_address;
                else if(dut.layer==4) position=16392;
                if(position>16392 || visited[position] || fault==1
                    || write_data!==golden[position]) begin
                    $display("FAIL: network layer=%0d bank=%0d addr=%0d data=%h expected=%h",dut.layer,write_bank,write_address,write_data,golden[position]); $fatal(1);
                end
                case(write_bank)
                    1: begin if(write_address>=4096) $fatal(1); ping[write_address]=write_data; end
                    2: begin if(write_address>=2048) $fatal(1); pong[write_address]=write_data; end
                    3: begin if(write_address>=8) $fatal(1); gap[write_address]=write_data; end
                    default: $fatal(1);
                endcase
                visited[position]=1; written=written+1;
            end
        end
    end
    task launch;
        begin
            written=0; reads=0; weight_reads=0; parameter_reads=0;
            for(index=0;index<=16392;index=index+1) visited[index]=0;
            @(negedge clk); #1; while(!ready) begin @(negedge clk); #1; end
            start=1; @(posedge clk); #1; start=0;
        end
    endtask
    task finish_run;
        input expect_error;
        begin
            while(busy) begin @(posedge clk); #1; end
            if(error!==expect_error || done!==!expect_error) $fatal(1);
            if(!expect_error) begin
                if(written!=9225 || reads!=103432 || weight_reads!=101384 || parameter_reads!=10
                    || logits!==golden[16392][23:0] || classification!==cls_expected[1:0]
                    || margin!==margin_expected[7:0] || score!==score_expected[14:0] || low_conf!==low_expected[0]) begin
                    $display("FAIL: final network writes=%0d reads=%0d weight_reads=%0d class=%0d margin=%0d logits=%h",
                        written,reads,weight_reads,classification,margin,logits); $fatal(1);
                end
            end
        end
    endtask
    task check_watchdog;
        integer budget, paused, elapsed;
        begin
            for(paused=0;paused<2;paused=paused+1)
            for(budget=0;budget<=40;budget=budget+1) begin
                cycle_limit=budget; launch; force_pause=paused; cycle_limit=0; elapsed=0;
                while(busy) begin
                    if(cycles==budget-1 && (memory_enable || weight_enable || parameter_enable || write_enable)) $fatal(1);
                    @(posedge clk); #1; elapsed=elapsed+1;
                end
                if(error!==1'b1 || done || elapsed!=budget || cycles!==budget || written
                    || (budget!=0 && error_layer!=7) || (paused && (reads || weight_reads))) begin
                    $display("FAIL: network watchdog budget=%0d paused=%0d elapsed=%0d cycles=%0d",budget,paused,elapsed,cycles); $fatal(1);
                end
                force_pause=0;
            end
            cycle_limit=2000000;
            $display("PASS: cnn_sequencer watchdog 82 exact-cycle cases; CE pause, latched budget and terminal strobes");
        end
    endtask
    initial begin
        found=$value$plusargs("model=%s",model_folder); if(!found) $fatal(1);
        found=$value$plusargs("case=%s",folder); if(!found) $fatal(1); faults=$test$plusargs("fault_tests");
        $sformat(filename,"%0s/weights.hex",model_folder); $readmemh(filename,weights,0,268);
        $sformat(filename,"%0s/bias.hex",model_folder); $readmemh(filename,biases,0,159);
        $sformat(filename,"%0s/multipliers.hex",model_folder); $readmemh(filename,multipliers,0,159);
        $sformat(filename,"%0s/shifts.hex",model_folder); $readmemh(filename,shifts,0,159);
        $sformat(filename,"%0s/input.hex",folder); $readmemh(filename,roi,0,4095);
        $sformat(filename,"%0s/conv1.hex",folder); $readmemh(filename,golden,0,2047);
        $sformat(filename,"%0s/conv2.hex",folder); $readmemh(filename,golden,4096,8191);
        $sformat(filename,"%0s/conv3.hex",folder); $readmemh(filename,golden,8192,9215);
        $sformat(filename,"%0s/conv4.hex",folder); $readmemh(filename,golden,12288,14335);
        $sformat(filename,"%0s/gap.hex",folder); $readmemh(filename,golden,16384,16391);
        $sformat(filename,"%0s/logits.hex",folder); $readmemh(filename,golden,16392,16392);
        $sformat(filename,"%0s/result.txt",folder); fd=$fopen(filename,"r"); if(!fd) $fatal(1);
        fields=$fscanf(fd,"%d %d %d %d %d\n",cls_expected,margin_expected,score_expected,low_expected,threshold);
        $fclose(fd); if(fields!=5) $fatal(1); min_margin=threshold;
        repeat(3) @(negedge clk); rst_n=1;
        if($test$plusargs("watchdog_only")) begin check_watchdog; $finish; end
        launch; finish_run(0);
        $display("PASS: cnn_sequencer %0s all 9225 packed words/73795 elements match integer network; logits=%h class=%0d margin=%0d cycles=%0d",
            folder,logits,classification,margin,cycles);
        if(faults) begin
            check_watchdog;
            fault=1; launch; finish_run(1); if(written || error_layer!=0) $fatal(1);
            fault=0; cycle_limit=2; launch; finish_run(1); if(written || error_layer!=7) $fatal(1); cycle_limit=2000000;
            launch; repeat(15) @(negedge clk); rst_n=0; #1;
            if(busy || done || error || memory_enable || write_enable) $fatal(1);
            repeat(3) @(negedge clk); rst_n=1;
            fault=3; launch; finish_run(1); if(error_layer!=5 || written!=9216) $fatal(1);
            fault=0; launch; finish_run(0);
            $display("PASS: cnn_sequencer invalid parameters/watchdog/reset/invalid GAP and successful fresh run; no false DONE");
        end
        $finish;
    end
    initial begin #50000000; $display("FAIL: network test timeout"); $fatal(1); end
endmodule
