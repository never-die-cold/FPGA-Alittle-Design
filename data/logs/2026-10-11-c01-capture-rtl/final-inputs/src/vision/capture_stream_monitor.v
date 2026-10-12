`timescale 1ns/1ps
// Observer only: never drives AXIS ready/valid or the HDMI display path.
// Complete means stream geometry, not completion/ownership of a DDR buffer.
module capture_stream_monitor #(parameter WIDTH=1280, HEIGHT=720)(
    input wire clk, rst_n, locked, fault,
    input wire tvalid, tready, tuser, tlast,
    output reg active,
    output reg [31:0] stream_seq, rejected_frames, error_epoch,
    output reg frame_complete
);
    reg [15:0] x, y;
    reg locked_q, fault_q;
    wire fire = tvalid && tready;
    wire tracked = locked && fire && (active || tuser);
    wire [15:0] cx = tuser ? 16'd0 : x;
    wire [15:0] cy = tuser ? 16'd0 : y;
    wire geometry_bad = tracked && (tlast != (cx == WIDTH-1));
    wire restart = tracked && tuser && active;
    wire source_bad = (fault && !fault_q) || (locked_q && !locked);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x<=0; y<=0; active<=0; locked_q<=0; fault_q<=0;
            stream_seq<=0; rejected_frames<=0; error_epoch<=0;
            frame_complete<=0;
        end else begin
            locked_q<=locked; fault_q<=fault;
            frame_complete<=0;
            if (source_bad || geometry_bad || restart)
                error_epoch<=error_epoch+1;
            if ((source_bad && (active || tracked)) || geometry_bad || restart)
                rejected_frames<=rejected_frames+1;
            if (!locked || fault || geometry_bad) begin
                active<=0; x<=0; y<=0;
            end else if (tracked) begin
                active<=1;
                if (cx == WIDTH-1) begin
                    x<=0;
                    if (cy == HEIGHT-1) begin
                        active<=0; y<=0;
                        stream_seq<=stream_seq+1; frame_complete<=1;
                    end else y<=cy+1;
                end else begin x<=cx+1; y<=cy; end
            end
        end
    end
endmodule
