`timescale 1ns/1ps
// 720p60 adapter: retain the full HDMI raster, replace only active RGB.
// Three raster lines cover both filters' row latency. The extra clocks cover
// arithmetic pipelines. All modes share the same delay and frame-start gate.
module diagnostic_display #(parameter WIDTH=1280,H_TOTAL=1650,VS_POL=1'b1)(
    input wire clk,rst_n,raw_vs,raw_hs,raw_de,diagnostic_en,frame_epoch,
    input wire [23:0] raw_rgb,
    input wire processed_vs,processed_de,
    input wire [7:0] processed_y,
    output reg video_vs,video_hs,video_de,
    output reg [23:0] video_rgb
);
    localparam XW=(WIDTH>1)?$clog2(WIDTH):1;
    wire [28:0] delayed;
    wire valid;
    wire dvs=delayed[26],dhs=delayed[25],dde=delayed[24];
    reg previous_vs,started;
    reg [XW-1:0] x;
    reg [15:0] row;
    wire [7:0] gray;
    wire gray_valid;
    reg q_vs,q_hs,q_de,q_mode,q_started;
    reg [23:0] q_rgb;
    wire frame_start=valid && dvs==VS_POL && previous_vs!=VS_POL;
    raster_delay #(.WIDTH(29),.DEPTH(3*H_TOTAL+16)) u_delay(
        .clk(clk),.rst_n(rst_n),.in_data({frame_epoch,diagnostic_en,raw_vs,raw_hs,raw_de,raw_rgb}),
        .out_data(delayed),.out_valid(valid));
    diagnostic_rows #(.WIDTH(WIDTH)) u_rows(.clk(clk),.rst_n(rst_n),
        .write_vs(processed_vs),.write_de(processed_de),.write_y(processed_y),.write_epoch(frame_epoch),
        .read_row(row),.read_x(x),.read_epoch(delayed[28]),.read_y(gray),.read_valid(gray_valid));
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            previous_vs<=VS_POL;started<=0;x<=0;row<=0;
            q_vs<=!VS_POL;q_hs<=0;q_de<=0;q_mode<=0;q_rgb<=0;q_started<=0;
            video_vs<=!VS_POL;video_hs<=0;video_de<=0;video_rgb<=0;
        end else begin
            if(valid) previous_vs<=dvs;
            if(frame_start) begin started<=1;x<=0;row<=0;end
            else if(valid && dde) begin
                if(x==WIDTH-1) begin x<=0;row<=row+1'b1;end
                else x<=x+1'b1;
            end
            q_vs<=dvs;q_hs<=dhs;q_de<=dde;q_mode<=delayed[27];q_rgb<=delayed[23:0];
            q_started<=valid && (started || frame_start);
            video_vs<=q_started?q_vs:!VS_POL;
            video_hs<=q_started?q_hs:0;video_de<=q_started && q_de;
            video_rgb<=q_started && q_de ? (q_mode ? (gray_valid?{3{gray}}:24'b0) : q_rgb) : 24'b0;
        end
    end
endmodule
