`timescale 1ns/1ps
module tb_cop_payload_adapter;
    reg clk=0,rst_n=0,start=0,commit=0,abort=0,write=0;
    reg [31:0] base=0,bytes=36032,address=0; reg [63:0] data=0; reg [7:0] strb=8'hff;
    wire ready,init_we,init_bank,commit_pulse,error,loading,active,valid;
    wire [2:0] init_kind; wire [15:0] init_address; wire [63:0] init_data;
    wire [1023:0] weight_data; wire [511:0] bias_data,mult_data; wire [95:0] shift_data;
    integer index,total_writes=0,weight_writes=0,bias_writes=0,mult_writes=0,shift_writes=0;
    integer before_writes,error_count=0;
    always #5 clk=~clk;
    cop_payload_adapter dut(.clk(clk),.rst_n(rst_n),.start_i(start),.commit_i(commit),.abort_i(abort),
        .payload_base_i(base),.payload_bytes_i(bytes),.store_write_i(write),.store_addr_i(address),
        .store_data_i(data),.store_strb_i(strb),.active_bank_i(active),.store_ready_o(ready),
        .init_we_o(init_we),.init_bank_o(init_bank),.init_kind_o(init_kind),
        .init_address_o(init_address),.init_data_o(init_data),.shadow_bank_o(),
        .commit_o(commit_pulse),.error_o(error),.loading_o(loading));
    cop_model_storage store(.clk(clk),.rst_n(rst_n),.init_we_i(init_we),.init_bank_i(init_bank),
        .commit_i(commit_pulse),.commit_bank_i(init_bank),.init_kind_i(init_kind),
        .init_address_i(init_address),.init_data_i(init_data),.weight_enable_i(1'b0),
        .parameter_enable_i(1'b0),.weight_address_i(16'd0),.parameter_address_i(8'd0),
        .active_bank_o(active),.model_valid_o(valid),.weight_data_o(weight_data),
        .bias_data_o(bias_data),.multiplier_data_o(mult_data),.shift_data_o(shift_data));
    always @(posedge clk) begin
        if(init_we) begin
            total_writes=total_writes+1;
            case(init_kind)
                1: weight_writes=weight_writes+1; 2: bias_writes=bias_writes+1;
                3: mult_writes=mult_writes+1; 4: shift_writes=shift_writes+1;
                default: $fatal(1);
            endcase
        end
        if(error) error_count=error_count+1;
    end
    task begin_load; input [31:0] test_base,test_bytes; input expect_error;
        begin
            @(negedge clk); base=test_base; bytes=test_bytes; start=1;
            @(posedge clk); #1; if(error!==expect_error) $fatal(1);
            @(negedge clk); start=0;
        end
    endtask
    task send_beat; input [31:0] test_address;
        begin
            while(!ready) @(negedge clk);
            address=test_address; data=0; strb=8'hff; write=1;
            @(posedge clk); #1; if(error) $fatal(1);
            @(negedge clk); write=0;
        end
    endtask
    initial begin
        repeat(3) @(negedge clk); rst_n=1;
        begin_load(0,36032,0);
        for(index=0;index<36032;index=index+8) send_beat(index);
        while(!ready) @(negedge clk);
        commit=1; @(posedge clk); #1; if(!commit_pulse) $fatal(1);
        @(negedge clk); commit=0; @(posedge clk); #1;
        if(!valid || active!=1 || total_writes!=4745 || weight_writes!=4304 ||
           bias_writes!=147 || mult_writes!=147 || shift_writes!=147) $fatal(1);
        $display("PASS: payload_adapter normal 36032-byte path writes 4304/147/147/147 and atomically activates shadow bank");
        before_writes=total_writes; begin_load(1,36032,1);
        if(active!=1 || !valid || total_writes!=before_writes) $fatal(1);
        $display("PASS: payload_adapter misaligned manifest rejected; active-state diff empty");
        begin_load(0,36024,1);
        if(active!=1 || !valid || total_writes!=before_writes) $fatal(1);
        $display("PASS: payload_adapter length mismatch rejected; active-state diff empty");
        begin_load(0,36032,0);
        while(!ready) @(negedge clk); address=36032; write=1;
        @(posedge clk); #1; if(!error) $fatal(1);
        @(negedge clk); write=0; @(posedge clk); #1;
        if(active!=1 || !valid || total_writes!=before_writes || error_count!=3) $fatal(1);
        $display("PASS: payload_adapter out-of-range write rejected; active-state diff empty; three visible error pulses");
        $finish;
    end
    initial begin #2000000; $display("FAIL: payload adapter timeout"); $fatal(1); end
endmodule
