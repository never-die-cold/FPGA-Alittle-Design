`timescale 1ns/1ps
// K3 synchronous storage: one registered read beat; contents are loaded through a narrow service port.
module cop_bram_storage (
    input wire clk, rst_n, init_we_i, read_enable_i, weight_enable_i, parameter_enable_i,
    input wire [2:0] init_kind_i, input wire [15:0] init_address_i,
    input wire [63:0] init_data_i, input wire [1:0] read_bank_i, write_bank_i,
    input wire [15:0] read_address_i, weight_address_i, write_address_i,
    input wire [7:0] parameter_address_i, input wire write_enable_i,
    input wire [63:0] write_data_i, output reg [63:0] input_data_o,
    output wire [1023:0] weight_data_o,
    output reg [511:0] bias_data_o, multiplier_data_o, output reg [95:0] shift_data_o
);
    (* ram_style="block" *) reg [7:0] roi [0:4095];
    (* ram_style="block" *) reg [63:0] ping [0:4095];
    (* ram_style="block" *) reg [63:0] pong [0:2047];
    (* ram_style="block" *) reg [63:0] gap [0:7];
    (* ram_style="block" *) reg [31:0] biases [0:159], multipliers [0:159];
    (* ram_style="block" *) reg [5:0] shifts [0:159];
    integer lane;
    genvar bank;
    generate for(bank=0;bank<16;bank=bank+1) begin: weight_bank
        (* ram_style="block" *) reg [63:0] mem [0:268]; reg [63:0] q;
        assign weight_data_o[bank*64 +: 64]=q;
        always @(posedge clk) begin
            if(init_we_i && init_kind_i==1 && init_address_i[3:0]==bank)
                mem[init_address_i[15:4]]<=init_data_i;
            if(weight_enable_i) q<=mem[weight_address_i];
        end
    end endgenerate
    always @(posedge clk) begin
        if(init_we_i) case(init_kind_i)
            0: for(lane=0;lane<8;lane=lane+1)
                roi[{init_address_i[8:0],3'b0}+lane]<=init_data_i[lane*8 +: 8];
            2: biases[init_address_i]<=init_data_i[31:0];
            3: multipliers[init_address_i]<=init_data_i[31:0];
            4: shifts[init_address_i]<=init_data_i[5:0];
            default: begin end
        endcase
        if(write_enable_i) case(write_bank_i)
            1: ping[write_address_i]<=write_data_i;
            2: pong[write_address_i]<=write_data_i;
            3: gap[write_address_i]<=write_data_i;
            default: begin end
        endcase
        if(!rst_n) begin input_data_o<=0; bias_data_o<=0; multiplier_data_o<=0; shift_data_o<=0; end
        else begin
            if(read_enable_i) case(read_bank_i)
                0: input_data_o<={56'd0,roi[read_address_i]};
                1: input_data_o<=ping[read_address_i];
                2: input_data_o<=pong[read_address_i];
                3: input_data_o<=gap[read_address_i];
            endcase
            if(parameter_enable_i) for(lane=0;lane<16;lane=lane+1) begin
                bias_data_o[lane*32 +: 32]<=biases[parameter_address_i+lane];
                multiplier_data_o[lane*32 +: 32]<=multipliers[parameter_address_i+lane];
                shift_data_o[lane*6 +: 6]<=shifts[parameter_address_i+lane];
            end
        end
    end
endmodule
