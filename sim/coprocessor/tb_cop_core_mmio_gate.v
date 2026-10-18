`timescale 1ns/1ps
module tb_cop_core_mmio_gate;
    reg [31:0] addr,wdata,status;
    reg [3:0] be;
    reg we,busy,pending;
    wire hit,request;
    wire [11:0] offset;
    wire [31:0] request_data,rdata;
    integer checks;
    cop_core_mmio_gate dut (.addr_i(addr),.wdata_i(wdata),.status_i(status),.be_i(be),
        .we_i(we),.busy_i(busy),.mailbox_pending_i(pending),.cop_hit_o(hit),
        .write_request_o(request),.write_offset_o(offset),.write_data_o(request_data),.rdata_o(rdata));
    task expect;
        input expected_hit,expected_request;
        input [31:0] expected_rdata;
        begin #1;
            if(hit!==expected_hit || request!==expected_request || rdata!==expected_rdata) begin
                $display("FAIL: addr=%h be=%b we=%b busy=%b pending=%b hit=%b req=%b rdata=%h",
                    addr,be,we,busy,pending,hit,request,rdata); $fatal(1);
            end
            checks=checks+1;
        end
    endtask
    initial begin
        checks=0; addr=32'h8001000c; wdata=1; status=32'h00000002;
        be=4'b1111; we=1; busy=0; pending=0; expect(1,1,0);
        be=4'b0011; expect(1,0,0);
        be=4'b1111; addr=32'h8001000d; expect(1,0,0);
        addr=32'h8001100c; expect(0,0,0);
        addr=32'h80010010; expect(1,0,0);
        addr=32'h8001000c; busy=1; expect(1,0,0);
        busy=0; pending=1; expect(1,0,0);
        we=0; addr=32'h80010010; expect(1,0,32'h00000402);
        addr=32'h8001000c; expect(1,0,0);
        pending=0; we=1; wdata=32'h00000002; expect(1,0,0);
        wdata=32'h00000008; busy=1; expect(1,1,0);
        if(offset!==12'h00c || request_data!==32'h00000008) $fatal(1);
        $display("PASS: cop_core_mmio_gate %0d window/alignment/permission/busy/pending checks",checks);
        $finish;
    end
endmodule
