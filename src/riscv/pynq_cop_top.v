// Production PL integration boundary. Zynq PS/AXI DMA are instantiated by the Vivado block-design Tcl.
module pynq_cop_top #(
    parameter IMEM_INIT_FILE="src/riscv_fw/cop_job.hex",
    parameter DMEM_INIT_FILE="src/riscv_fw/cop_job.hex"
) (
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 PS_CLK CLK", X_INTERFACE_PARAMETER="ASSOCIATED_BUSIF S_AXI:S_AXIS, ASSOCIATED_RESET ps_rst_n_i, FREQ_HZ 100000000" *)
    input wire ps_clk_100_i,
    (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 PS_RST RST", X_INTERFACE_PARAMETER="POLARITY ACTIVE_LOW" *)
    input wire ps_rst_n_i,
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 COP_CLK CLK", X_INTERFACE_PARAMETER="ASSOCIATED_RESET cop_rst_n_i, FREQ_HZ 40000000" *)
    input wire cop_clk_40_i,
    (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 COP_RST RST", X_INTERFACE_PARAMETER="POLARITY ACTIVE_LOW" *)
    input wire cop_rst_n_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWADDR", X_INTERFACE_PARAMETER="PROTOCOL AXI4LITE, DATA_WIDTH 32, ADDR_WIDTH 12, FREQ_HZ 100000000" *) input wire [11:0] s_axi_awaddr_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWVALID" *) input wire s_axi_awvalid_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWREADY" *) output wire s_axi_awready_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WDATA" *) input wire [31:0] s_axi_wdata_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WSTRB" *) input wire [3:0] s_axi_wstrb_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WVALID" *) input wire s_axi_wvalid_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WREADY" *) output wire s_axi_wready_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI BRESP" *) output wire [1:0] s_axi_bresp_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI BVALID" *) output wire s_axi_bvalid_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI BREADY" *) input wire s_axi_bready_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARADDR" *) input wire [11:0] s_axi_araddr_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARVALID" *) input wire s_axi_arvalid_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARREADY" *) output wire s_axi_arready_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RDATA" *) output wire [31:0] s_axi_rdata_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RRESP" *) output wire [1:0] s_axi_rresp_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RVALID" *) output wire s_axi_rvalid_o,
    (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RREADY" *) input wire s_axi_rready_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TDATA", X_INTERFACE_PARAMETER="TDATA_NUM_BYTES 8, HAS_TKEEP 1, HAS_TLAST 1, FREQ_HZ 100000000" *) input wire [63:0] s_axis_tdata_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TKEEP" *) input wire [7:0] s_axis_tkeep_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TLAST" *) input wire s_axis_tlast_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TVALID" *) input wire s_axis_tvalid_i,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TREADY" *) output wire s_axis_tready_o,
    input wire dma_start_ps_i, dma_kind_ps_i, output wire dma_start_ready_o,
    output wire payload_error_o, output wire [3:0] led
);
    wire [11:0] cop_awaddr,cop_araddr; wire cop_awvalid,cop_awready,cop_wvalid,cop_wready;
    wire [31:0] cop_wdata,cop_rdata; wire [3:0] cop_wstrb; wire [1:0] cop_bresp,cop_rresp;
    wire cop_bvalid,cop_bready,cop_arvalid,cop_arready,cop_rvalid,cop_rready;
    cop_axi_lite_cdc axil_cdc(.s_clk(ps_clk_100_i),.s_rst_n(ps_rst_n_i),
        .s_awaddr(s_axi_awaddr_i),.s_awvalid(s_axi_awvalid_i),.s_awready(s_axi_awready_o),
        .s_wdata(s_axi_wdata_i),.s_wstrb(s_axi_wstrb_i),.s_wvalid(s_axi_wvalid_i),.s_wready(s_axi_wready_o),
        .s_bresp(s_axi_bresp_o),.s_bvalid(s_axi_bvalid_o),.s_bready(s_axi_bready_i),
        .s_araddr(s_axi_araddr_i),.s_arvalid(s_axi_arvalid_i),.s_arready(s_axi_arready_o),
        .s_rdata(s_axi_rdata_o),.s_rresp(s_axi_rresp_o),.s_rvalid(s_axi_rvalid_o),.s_rready(s_axi_rready_i),
        .m_clk(cop_clk_40_i),.m_rst_n(cop_rst_n_i),.m_awaddr(cop_awaddr),.m_awvalid(cop_awvalid),
        .m_awready(cop_awready),.m_wdata(cop_wdata),.m_wstrb(cop_wstrb),.m_wvalid(cop_wvalid),
        .m_wready(cop_wready),.m_bresp(cop_bresp),.m_bvalid(cop_bvalid),.m_bready(cop_bready),
        .m_araddr(cop_araddr),.m_arvalid(cop_arvalid),.m_arready(cop_arready),
        .m_rdata(cop_rdata),.m_rresp(cop_rresp),.m_rvalid(cop_rvalid),.m_rready(cop_rready));
    wire [63:0] dma_data; wire [7:0] dma_keep; wire dma_last,dma_valid,dma_ready;
    cop_axis_async_fifo axis_cdc(.s_clk(ps_clk_100_i),.s_rst_n(ps_rst_n_i),
        .s_data(s_axis_tdata_i),.s_keep(s_axis_tkeep_i),.s_last(s_axis_tlast_i),
        .s_valid(s_axis_tvalid_i),.s_ready(s_axis_tready_o),.m_clk(cop_clk_40_i),.m_rst_n(cop_rst_n_i),
        .m_data(dma_data),.m_keep(dma_keep),.m_last(dma_last),.m_valid(dma_valid),.m_ready(dma_ready));
    reg dma_req_ps,dma_kind_hold; reg dma_ack_cop,dma_req_seen;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg dma_req_c1,dma_req_c2,dma_kind_c1,dma_kind_c2;
    reg cop_dma_start,cop_dma_kind;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg dma_ack_s1,dma_ack_s2;
    assign dma_start_ready_o=dma_ack_s2==dma_req_ps;
    always @(posedge ps_clk_100_i or negedge ps_rst_n_i) begin
        if(!ps_rst_n_i) begin dma_req_ps<=0; dma_kind_hold<=0; dma_ack_s1<=0; dma_ack_s2<=0; end
        else begin
            dma_ack_s1<=dma_ack_cop; dma_ack_s2<=dma_ack_s1;
            if(dma_start_ps_i && dma_start_ready_o) begin dma_kind_hold<=dma_kind_ps_i; dma_req_ps<=!dma_req_ps; end
        end
    end
    always @(posedge cop_clk_40_i or negedge cop_rst_n_i) begin
        if(!cop_rst_n_i) begin
            dma_req_c1<=0; dma_req_c2<=0; dma_req_seen<=0; dma_kind_c1<=0; dma_kind_c2<=0;
            dma_ack_cop<=0; cop_dma_start<=0; cop_dma_kind<=0;
        end else begin
            dma_req_c1<=dma_req_ps; dma_req_c2<=dma_req_c1;
            dma_kind_c1<=dma_kind_hold; dma_kind_c2<=dma_kind_c1; cop_dma_start<=0;
            if(dma_req_c2!=dma_req_seen) begin
                dma_req_seen<=dma_req_c2; cop_dma_kind<=dma_kind_c2; cop_dma_start<=1; dma_ack_cop<=dma_req_c2;
            end
        end
    end
    wire core_hit,core_we; wire [31:0] core_addr,core_wdata,core_read; wire [3:0] core_be;
    soc_top #(.IMEM_INIT_FILE(IMEM_INIT_FILE),.DMEM_INIT_FILE(DMEM_INIT_FILE),.ENABLE_COP(1'b1)) soc(
        .clk(cop_clk_40_i),.rst_n(cop_rst_n_i),.led(led),.cop_rdata_i(core_read),.cop_hit_o(core_hit),
        .cop_we_o(core_we),.cop_addr_o(core_addr),.cop_wdata_o(core_wdata),.cop_be_o(core_be));
    wire store_write; wire [31:0] store_addr; wire [63:0] store_data; wire [7:0] store_strb;
    wire memory_read,weight_read,param_read,memory_write; wire [1:0] read_bank,write_bank;
    wire [15:0] read_addr,weight_addr,write_addr; wire [7:0] param_addr; wire [63:0] memory_wdata;
    wire [31:0] status; wire [63:0] memory_rdata; wire [1023:0] weight_rdata;
    wire [511:0] bias_rdata,mult_rdata; wire [95:0] shift_rdata;
    wire adapter_ready,adapter_we,adapter_bank,adapter_commit,adapter_error,model_active,model_valid;
    wire [2:0] adapter_kind; wire [15:0] adapter_addr; wire [63:0] adapter_data;
    reg status_model_q;
    wire model_commit=status[6] && !status_model_q;
    assign payload_error_o=adapter_error;
    always @(posedge cop_clk_40_i or negedge cop_rst_n_i)
        if(!cop_rst_n_i) status_model_q<=0; else status_model_q<=status[6];
    cop_payload_adapter adapter(.clk(cop_clk_40_i),.rst_n(cop_rst_n_i),
        .start_i(cop_dma_start && !cop_dma_kind),.commit_i(model_commit),.abort_i(1'b0),
        .payload_base_i(32'd0),.payload_bytes_i(32'd36032),.store_write_i(store_write && !cop_dma_kind),
        .store_addr_i(store_addr),.store_data_i(store_data),.store_strb_i(store_strb),
        .active_bank_i(model_active),.store_ready_o(adapter_ready),.init_we_o(adapter_we),
        .init_bank_o(adapter_bank),.init_kind_o(adapter_kind),.init_address_o(adapter_addr),
        .init_data_o(adapter_data),.shadow_bank_o(),.commit_o(adapter_commit),
        .error_o(adapter_error),.loading_o());
    cop_model_storage models(.clk(cop_clk_40_i),.rst_n(cop_rst_n_i),.init_we_i(adapter_we),
        .init_bank_i(adapter_bank),.commit_i(adapter_commit),.commit_bank_i(adapter_bank),
        .init_kind_i(adapter_kind),.init_address_i(adapter_addr),.init_data_i(adapter_data),
        .weight_enable_i(weight_read),.parameter_enable_i(param_read),.weight_address_i(weight_addr),
        .parameter_address_i(param_addr),.active_bank_o(model_active),.model_valid_o(model_valid),
        .weight_data_o(weight_rdata),.bias_data_o(bias_rdata),.multiplier_data_o(mult_rdata),
        .shift_data_o(shift_rdata));
    cop_bram_storage activations(.clk(cop_clk_40_i),.rst_n(cop_rst_n_i),
        .init_we_i(store_write && cop_dma_kind),.init_kind_i(3'd0),.init_address_i(store_addr[18:3]),
        .init_data_i(store_data),.read_enable_i(memory_read),.read_bank_i(read_bank),.read_address_i(read_addr),
        .weight_enable_i(1'b0),.weight_address_i(16'd0),.parameter_enable_i(1'b0),.parameter_address_i(8'd0),
        .write_enable_i(memory_write),.write_bank_i(write_bank),.write_address_i(write_addr),
        .write_data_i(memory_wdata),.input_data_o(memory_rdata),.weight_data_o(),
        .bias_data_o(),.multiplier_data_o(),.shift_data_o());
    cop_top cop(.core_clk(cop_clk_40_i),.cop_clk(cop_clk_40_i),.rst_n(cop_rst_n_i),
        .core_addr_i(core_addr),.core_wdata_i(core_wdata),.core_be_i(core_be),.core_we_i(core_we),
        .core_hit_o(),.core_rdata_o(core_read),.s_axi_awaddr_i(cop_awaddr),.s_axi_awvalid_i(cop_awvalid),
        .s_axi_awready_o(cop_awready),.s_axi_wdata_i(cop_wdata),.s_axi_wstrb_i(cop_wstrb),
        .s_axi_wvalid_i(cop_wvalid),.s_axi_wready_o(cop_wready),.s_axi_bresp_o(cop_bresp),
        .s_axi_bvalid_o(cop_bvalid),.s_axi_bready_i(cop_bready),.s_axi_araddr_i(cop_araddr),
        .s_axi_arvalid_i(cop_arvalid),.s_axi_arready_o(cop_arready),.s_axi_rdata_o(cop_rdata),
        .s_axi_rresp_o(cop_rresp),.s_axi_rvalid_o(cop_rvalid),.s_axi_rready_i(cop_rready),
        .dma_start_i(cop_dma_start),.dma_kind_i(cop_dma_kind),.dma_data_i(dma_data),
        .dma_keep_i(dma_keep),.dma_valid_i(dma_valid),.dma_last_i(dma_last),
        .store_ready_i(cop_dma_kind ? 1'b1 : adapter_ready),.dma_ready_o(dma_ready),
        .store_write_o(store_write),.store_addr_o(store_addr),.store_data_o(store_data),.store_strb_o(store_strb),
        .target_id_i(16'd0),.memory_data_i(memory_rdata),.weight_data_i(weight_rdata),
        .bias_data_i(bias_rdata),.multiplier_data_i(mult_rdata),.shift_data_i(shift_rdata),
        .memory_enable_o(memory_read),.weight_enable_o(weight_read),.parameter_enable_o(param_read),
        .read_bank_o(read_bank),.write_bank_o(write_bank),.read_address_o(read_addr),
        .weight_address_o(weight_addr),.write_address_o(write_addr),.parameter_address_o(param_addr),
        .memory_write_o(memory_write),.memory_write_data_o(memory_wdata),.irq_pending_i(adapter_error),
        .engine_start_o(),.result_write_o(),.task_result_index_o(),.result_seq_o(),.result_data_o(),
        .status_o(status),.fw_counts_o(),.fw_decision_o(),.result_index_o());
endmodule
