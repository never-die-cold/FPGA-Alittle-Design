`timescale 1ns/1ps
// Two model slots: loading never changes the active model; commit switches slots atomically.
module cop_model_storage (
    input wire clk, rst_n, init_we_i, init_bank_i, commit_i, commit_bank_i,
    input wire [2:0] init_kind_i, input wire [15:0] init_address_i,
    input wire [63:0] init_data_i, input wire weight_enable_i, parameter_enable_i,
    input wire [15:0] weight_address_i, input wire [7:0] parameter_address_i,
    output reg active_bank_o, model_valid_o,
    output wire [1023:0] weight_data_o,
    output reg [511:0] bias_data_o, multiplier_data_o, output reg [95:0] shift_data_o
);
    (* ram_style="block" *) reg [31:0] bias0 [0:159], bias1 [0:159];
    (* ram_style="block" *) reg [31:0] mult0 [0:159], mult1 [0:159];
    (* ram_style="block" *) reg [5:0] shift0 [0:159], shift1 [0:159];
    integer lane;
    genvar bank;
    generate for(bank=0;bank<16;bank=bank+1) begin: weight_bank
        (* ram_style="block" *) reg [63:0] mem0 [0:268], mem1 [0:268];
        reg [63:0] q0,q1;
        assign weight_data_o[bank*64 +: 64]=active_bank_o ? q1 : q0;
        always @(posedge clk) begin
            if(init_we_i && init_kind_i==1 && init_address_i[3:0]==bank) begin
                if(init_bank_i) mem1[init_address_i[15:4]]<=init_data_i;
                else mem0[init_address_i[15:4]]<=init_data_i;
            end
            if(weight_enable_i) begin
                if(active_bank_o) q1<=mem1[weight_address_i];
                else q0<=mem0[weight_address_i];
            end
        end
    end endgenerate
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            active_bank_o<=0; model_valid_o<=0;
            bias_data_o<=0; multiplier_data_o<=0; shift_data_o<=0;
        end else begin
            if(commit_i) begin active_bank_o<=commit_bank_i; model_valid_o<=1; end
            if(init_we_i) case(init_kind_i)
                2: if(init_bank_i) bias1[init_address_i]<=init_data_i[31:0];
                   else bias0[init_address_i]<=init_data_i[31:0];
                3: if(init_bank_i) mult1[init_address_i]<=init_data_i[31:0];
                   else mult0[init_address_i]<=init_data_i[31:0];
                4: if(init_bank_i) shift1[init_address_i]<=init_data_i[5:0];
                   else shift0[init_address_i]<=init_data_i[5:0];
                default: begin end
            endcase
            if(parameter_enable_i) for(lane=0;lane<16;lane=lane+1) begin
                if(active_bank_o) begin
                    bias_data_o[lane*32 +: 32]<=bias1[parameter_address_i+lane];
                    multiplier_data_o[lane*32 +: 32]<=mult1[parameter_address_i+lane];
                    shift_data_o[lane*6 +: 6]<=shift1[parameter_address_i+lane];
                end else begin
                    bias_data_o[lane*32 +: 32]<=bias0[parameter_address_i+lane];
                    multiplier_data_o[lane*32 +: 32]<=mult0[parameter_address_i+lane];
                    shift_data_o[lane*6 +: 6]<=shift0[parameter_address_i+lane];
                end
            end
        end
    end
endmodule
