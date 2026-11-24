// tb_soc.v - minimal system around core_top for running benchmark firmware.
//
// Memory map:
//   0x0000_0000 .. 0x0001_FFFF  128 KiB RAM (firmware loaded from FIRMWARE hex)
//   0x1000_0000                 console: write a byte to print it
//   0x2000_0000                 exit: write a value to end the simulation
//
// RAM answers one cycle after mem_valid (same as PicoRV32's testbench_ez), so
// cycle counts reflect the core plus a single-cycle memory.

`timescale 1ns/1ps
`default_nettype none

module tb_soc;
	parameter MUL   = 1;
	parameter MUL_P = 1;
	parameter DIV   = 1;
	parameter DIV_P = 1;
	parameter       MAX_CYCLES      = 50_000_000;

	reg clk = 0, resetn = 0;
	always #5 clk = ~clk;

	wire        trap, mem_valid, mem_instr;
	reg         mem_ready = 0;
	wire [31:0] mem_addr, mem_wdata;
	wire [3:0]  mem_wstrb;
	reg  [31:0] mem_rdata = 0;

	core_top #(
		.MUL(MUL), .MUL_P(MUL_P), .DIV(DIV), .DIV_P(DIV_P)
	) dut (
		.clk(clk), .resetn(resetn), .trap(trap),
		.mem_valid(mem_valid), .mem_instr(mem_instr), .mem_ready(mem_ready),
		.mem_addr(mem_addr), .mem_wdata(mem_wdata), .mem_wstrb(mem_wstrb),
		.mem_rdata(mem_rdata)
	);

	reg [31:0] memory [0:32767];
	reg [1023:0] firmware;
	initial begin
		if (!$value$plusargs("FIRMWARE=%s", firmware))
			firmware = "firmware.hex";
		$readmemh(firmware, memory);
	end

	integer cycles = 0;
	always @(posedge clk) begin
		mem_ready <= 0;
		if (resetn && mem_valid && !mem_ready) begin
			mem_ready <= 1;
			if (mem_addr < 32'h0002_0000) begin
				mem_rdata <= memory[mem_addr >> 2];
				if (mem_wstrb[0]) memory[mem_addr >> 2][ 7: 0] <= mem_wdata[ 7: 0];
				if (mem_wstrb[1]) memory[mem_addr >> 2][15: 8] <= mem_wdata[15: 8];
				if (mem_wstrb[2]) memory[mem_addr >> 2][23:16] <= mem_wdata[23:16];
				if (mem_wstrb[3]) memory[mem_addr >> 2][31:24] <= mem_wdata[31:24];
			end else if (mem_addr == 32'h1000_0000 && |mem_wstrb) begin
				$write("%c", mem_wdata[7:0]);
				$fflush;
			end else if (mem_addr == 32'h2000_0000 && |mem_wstrb) begin
				$display("\nEXIT code=%0d cycles=%0d", mem_wdata, cycles);
				$finish;
			end else begin
				$display("\nERROR: bad access addr=%h wstrb=%b", mem_addr, mem_wstrb);
				$finish;
			end
		end
	end

	always @(posedge clk) begin
		cycles <= cycles + 1;
		if (cycles == 10) resetn <= 1;
		if (resetn && trap) begin
			$display("\nTRAP at cycle %0d", cycles);
			$finish;
		end
		if (cycles >= MAX_CYCLES) begin
			$display("\nTIMEOUT");
			$finish;
		end
	end
endmodule

`default_nettype wire
