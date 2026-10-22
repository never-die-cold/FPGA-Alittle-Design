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
    reg [63:0] gap [0:7], gap_q;
    (* ram_style="block" *) reg [31:0] biases [0:159], multipliers [0:159];
    (* ram_style="block" *) reg [5:0] shifts [0:159];
    wire [63:0] roi_q, ping_q, pong_q;
    reg [1:0] read_bank_q;
    reg [2:0] roi_lane_q;
    integer lane;
    cop_sync_ram_1r1w #(.AW(9)) roi_ram(.clk(clk),
        .we_i(init_we_i && init_kind_i==0),.re_i(read_enable_i && read_bank_i==0),
        .write_address_i(init_address_i[8:0]),.read_address_i(read_address_i[11:3]),
        .write_data_i(init_data_i),.read_data_o(roi_q));
    cop_sync_ram_1r1w #(.AW(12)) ping_ram(.clk(clk),
        .we_i(write_enable_i && write_bank_i==1),.re_i(read_enable_i && read_bank_i==1),
        .write_address_i(write_address_i[11:0]),.read_address_i(read_address_i[11:0]),
        .write_data_i(write_data_i),.read_data_o(ping_q));
    cop_sync_ram_1r1w #(.AW(11)) pong_ram(.clk(clk),
        .we_i(write_enable_i && write_bank_i==2),.re_i(read_enable_i && read_bank_i==2),
        .write_address_i(write_address_i[10:0]),.read_address_i(read_address_i[10:0]),
        .write_data_i(write_data_i),.read_data_o(pong_q));
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
    always @* begin
        case(read_bank_q)
            0: input_data_o={56'd0,roi_q[roi_lane_q*8 +: 8]};
            1: input_data_o=ping_q;
            2: input_data_o=pong_q;
            3: input_data_o=gap_q;
        endcase
    end
    always @(posedge clk) begin
        if(init_we_i) case(init_kind_i)
            2: biases[init_address_i]<=init_data_i[31:0];
            3: multipliers[init_address_i]<=init_data_i[31:0];
            4: shifts[init_address_i]<=init_data_i[5:0];
            default: begin end
        endcase
        if(write_enable_i && write_bank_i==3) gap[write_address_i]<=write_data_i;
        if(read_enable_i && read_bank_i==3) gap_q<=gap[read_address_i];
        if(!rst_n) begin read_bank_q<=0; roi_lane_q<=0;
            bias_data_o<=0; multiplier_data_o<=0; shift_data_o<=0; end
        else begin
            if(read_enable_i) begin read_bank_q<=read_bank_i; roi_lane_q<=read_address_i[2:0]; end
            if(parameter_enable_i) for(lane=0;lane<16;lane=lane+1) begin
                bias_data_o[lane*32 +: 32]<=biases[parameter_address_i+lane];
                multiplier_data_o[lane*32 +: 32]<=multipliers[parameter_address_i+lane];
                shift_data_o[lane*6 +: 6]<=shifts[parameter_address_i+lane];
            end
        end
    end
endmodule
