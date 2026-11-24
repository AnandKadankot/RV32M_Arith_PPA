// core_top.v - PicoRV32 RV32IMC with a selectable M-extension implementation.
//
//   MUL = 0  none
//   MUL = 1  PicoRV32 picorv32_pcpi_mul       (stock iterative, ENABLE_MUL)
//   MUL = 2  PicoRV32 picorv32_pcpi_fast_mul  (stock single-stage, ENABLE_FAST_MUL)
//   MUL = 3  pcpi_mul_booth #(MUL_P)          (radix-4 Booth, MUL_P digits/cycle)
//
//   DIV = 0  none
//   DIV = 1  PicoRV32 picorv32_pcpi_div       (stock iterative, ENABLE_DIV)
//   DIV = 2  pcpi_div_restoring #(DIV_P)      (restoring, DIV_P bits/cycle)
//
// Stock units are enabled through PicoRV32's own parameters; the new units sit
// on the external PCPI port. Each unit decodes only its own instructions, so
// their outputs can simply be OR-combined.
//
// The same module is the simulation DUT and the Vivado/ORFS synthesis top.

`default_nettype none

module core_top #(
	parameter MUL   = 1,
	parameter MUL_P = 1,
	parameter DIV   = 1,
	parameter DIV_P = 1
) (
	input  wire        clk,
	input  wire        resetn,
	output wire        trap,

	output wire        mem_valid,
	output wire        mem_instr,
	input  wire        mem_ready,
	output wire [31:0] mem_addr,
	output wire [31:0] mem_wdata,
	output wire [ 3:0] mem_wstrb,
	input  wire [31:0] mem_rdata
);
	localparam EXT_MUL = (MUL == 3);
	localparam EXT_DIV = (DIV == 2);

	wire        pcpi_valid;
	wire [31:0] pcpi_insn, pcpi_rs1, pcpi_rs2;

	wire        m_wr, m_wait, m_ready;  wire [31:0] m_rd;
	wire        d_wr, d_wait, d_ready;  wire [31:0] d_rd;

	picorv32 #(
		.COMPRESSED_ISA  (1),
		.ENABLE_COUNTERS (1),
		.CATCH_ILLINSN   (1),
		.ENABLE_PCPI     (EXT_MUL || EXT_DIV),
		.ENABLE_MUL      (MUL == 1),
		.ENABLE_FAST_MUL (MUL == 2),
		.ENABLE_DIV      (DIV == 1)
	) cpu (
		.clk        (clk),
		.resetn     (resetn),
		.trap       (trap),
		.mem_valid  (mem_valid),
		.mem_instr  (mem_instr),
		.mem_ready  (mem_ready),
		.mem_addr   (mem_addr),
		.mem_wdata  (mem_wdata),
		.mem_wstrb  (mem_wstrb),
		.mem_rdata  (mem_rdata),
		.pcpi_valid (pcpi_valid),
		.pcpi_insn  (pcpi_insn),
		.pcpi_rs1   (pcpi_rs1),
		.pcpi_rs2   (pcpi_rs2),
		.pcpi_wr    (m_wr | d_wr),
		.pcpi_rd    ((m_ready ? m_rd : 32'b0) | (d_ready ? d_rd : 32'b0)),
		.pcpi_wait  (m_wait | d_wait),
		.pcpi_ready (m_ready | d_ready),
		.irq        (32'b0),
		.eoi        (),
		.mem_la_read (), .mem_la_write (), .mem_la_addr (),
		.mem_la_wdata (), .mem_la_wstrb (),
		.trace_valid (), .trace_data ()
	);

	generate if (EXT_MUL) begin : g_mul
		pcpi_mul_booth #(.DIGITS(MUL_P)) mul (
			.clk(clk), .resetn(resetn),
			.pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
			.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2),
			.pcpi_wr(m_wr), .pcpi_rd(m_rd), .pcpi_wait(m_wait), .pcpi_ready(m_ready));
	end else begin : g_nomul
		assign {m_wr, m_wait, m_ready} = 3'b000;
		assign m_rd = 32'b0;
	end endgenerate

	generate if (EXT_DIV) begin : g_div
		pcpi_div_restoring #(.BITS(DIV_P)) div (
			.clk(clk), .resetn(resetn),
			.pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
			.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2),
			.pcpi_wr(d_wr), .pcpi_rd(d_rd), .pcpi_wait(d_wait), .pcpi_ready(d_ready));
	end else begin : g_nodiv
		assign {d_wr, d_wait, d_ready} = 3'b000;
		assign d_rd = 32'b0;
	end endgenerate
endmodule

`default_nettype wire
