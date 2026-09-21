// muldiv.v —— RV32M 多拍乘除单元：启动握手与操作数锁存
// 接口见 src/riscv/design_v0.md §5.6、§6.6
module muldiv (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [2:0]  op,
    input  wire        start,
    input  wire [31:0] a,
    input  wire [31:0] b,
    output reg  [31:0] result,
    output reg         busy,
    output reg         done
);

    reg [2:0]  op_r;
    reg [31:0] a_r;
    reg [31:0] b_r;
    reg [4:0]  count;
    reg [63:0] product_acc;
    reg [63:0] multiplicand;
    reg [31:0] multiplier;
    reg        product_neg;

    wire a_signed = (op == 3'b001) || (op == 3'b010);
    wire b_signed = (op == 3'b001);
    wire [31:0] a_magnitude = (a_signed && a[31]) ? (~a + 32'd1) : a;
    wire [31:0] b_magnitude = (b_signed && b[31]) ? (~b + 32'd1) : b;
    wire [63:0] product_sum = multiplier[0] ?
                              (product_acc + multiplicand) : product_acc;
    wire [63:0] final_product = product_neg ?
                                (~product_sum + 64'd1) : product_sum;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            op_r   <= 3'b000;
            a_r    <= 32'd0;
            b_r    <= 32'd0;
            count  <= 5'd0;
            product_acc <= 64'd0;
            multiplicand <= 64'd0;
            multiplier   <= 32'd0;
            product_neg  <= 1'b0;
            result <= 32'd0;
            busy   <= 1'b0;
            done   <= 1'b0;
        end else begin
            done <= 1'b0;

            if (start && !busy) begin
                op_r  <= op;
                a_r   <= a;
                b_r   <= b;
                count <= 5'd0;
                busy  <= 1'b1;
                product_acc <= 64'd0;
                multiplicand <= {32'd0, a_magnitude};
                multiplier   <= b_magnitude;
                product_neg  <= (a_signed && a[31]) ^ (b_signed && b[31]);
            end else if (busy) begin
                product_acc <= product_sum;
                multiplicand <= multiplicand << 1;
                multiplier   <= multiplier >> 1;
                if (count == 5'd31) begin
                    if (!op_r[2])
                        result <= (op_r == 3'b000) ?
                                  final_product[31:0] : final_product[63:32];
                    else
                        result <= 32'd0; // 第 6 步接入除法/取余结果
                    busy   <= 1'b0;
                    done   <= 1'b1;
                end else begin
                    count <= count + 5'd1;
                end
            end
        end
    end

endmodule
