// tb_unit.v - self-checking testbench for any RV32M PCPI unit.
//
//   UNIT = 0  picorv32_pcpi_mul       (PicoRV32 iterative multiplier)
//   UNIT = 1  picorv32_pcpi_fast_mul  (PicoRV32 single-stage multiplier)
//   UNIT = 2  pcpi_mul_booth #(P)     (radix-4 Booth, P digits/cycle)
//   UNIT = 3  picorv32_pcpi_div       (PicoRV32 iterative divider)
//   UNIT = 4  pcpi_div_restoring #(P) (restoring, P bits/cycle)
//
// Drives the PCPI handshake like PicoRV32 (valid held until ready), checks each
// result against a reference model of the RISC-V spec (including divide by zero
// and signed overflow), and reports min/max latency per instruction.

`timescale 1ns/1ps
`default_nettype none

// Gate-level simulation (+define+GLS): the routed netlist has its parameters
// already applied, so the parameter override must be left out.
`ifdef GLS
  `define UNIT_PARAMS(name)
`else
  `define UNIT_PARAMS(name) #(.name(P))
`endif

module tb_unit;
	parameter UNIT = 2;
	parameter P = 1;
	parameter N_RANDOM = 20000;

	localparam IS_DIV = UNIT >= 3;

	reg clk = 0, resetn = 0;
	always #5 clk = ~clk;

	reg         pcpi_valid = 0;
	reg  [31:0] pcpi_insn = 0, pcpi_rs1 = 0, pcpi_rs2 = 0;
	wire        pcpi_wr, pcpi_wait, pcpi_ready;
	wire [31:0] pcpi_rd;

	generate
		if (UNIT == 0) begin : u
			picorv32_pcpi_mul dut (.clk(clk), .resetn(resetn), .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
				.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2), .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd),
				.pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready));
		end else if (UNIT == 1) begin : u
			picorv32_pcpi_fast_mul dut (.clk(clk), .resetn(resetn), .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
				.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2), .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd),
				.pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready));
		end else if (UNIT == 2) begin : u
			pcpi_mul_booth `UNIT_PARAMS(DIGITS) dut (.clk(clk), .resetn(resetn), .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
				.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2), .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd),
				.pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready));
		end else if (UNIT == 3) begin : u
			picorv32_pcpi_div dut (.clk(clk), .resetn(resetn), .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
				.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2), .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd),
				.pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready));
		end else begin : u
			pcpi_div_restoring `UNIT_PARAMS(BITS) dut (.clk(clk), .resetn(resetn), .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
				.pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2), .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd),
				.pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready));
		end
	endgenerate

	// ---------------- reference model (RISC-V M spec) ----------------
	// NOTE: signed / and % are computed into separate signed variables. Inside a
	// ?: expression that also contains unsigned constants, Verilog would evaluate
	// $signed(a) / $signed(b) as UNSIGNED (the whole expression's signedness is
	// the context), silently giving wrong answers for negative operands.
	function [31:0] model(input [2:0] f3, input [31:0] a, input [31:0] b);
		reg [63:0] p;
		reg signed [31:0] sa, sb, sq, sr;
		begin
			sa = a; sb = b;
			// guard divide-by-zero and INT_MIN / -1: the simulator evaluates these
			// with host-CPU division, which traps on both (results set below)
			if (sb == 0 || (sa == 32'sh8000_0000 && sb == -1)) begin
				sq = 0; sr = 0;
			end else begin
				sq = sa / sb; sr = sa % sb;
			end
			case (f3)
				3'd0: begin p = a * b; model = p[31:0]; end
				3'd1: begin p = $signed({{32{a[31]}}, a}) * $signed({{32{b[31]}}, b}); model = p[63:32]; end
				3'd2: begin p = $signed({{32{a[31]}}, a}) * $signed({32'b0, b});       model = p[63:32]; end
				3'd3: begin p = {32'b0, a} * {32'b0, b};                               model = p[63:32]; end
				3'd4: model = (b == 0) ? 32'hFFFF_FFFF :
				              (a == 32'h8000_0000 && b == 32'hFFFF_FFFF) ? 32'h8000_0000 :
				              sq;
				3'd5: model = (b == 0) ? 32'hFFFF_FFFF : a / b;
				3'd6: model = (b == 0) ? a :
				              (a == 32'h8000_0000 && b == 32'hFFFF_FFFF) ? 32'd0 :
				              sr;
				3'd7: model = (b == 0) ? a : a % b;
			endcase
		end
	endfunction

	integer errors = 0, checks = 0, lat, i, j, k;
	integer cyc = 0, cyc0 = 0;
	always @(posedge clk) cyc = cyc + 1;
	integer lat_min [0:7], lat_max [0:7];

	task issue(input [2:0] f3, input [31:0] a, input [31:0] b);
		reg [31:0] exp;
		begin
			@(negedge clk);
			pcpi_insn  = {7'b0000001, 5'd2, 5'd1, f3, 5'd3, 7'b0110011};
			pcpi_rs1 = a; pcpi_rs2 = b; pcpi_valid = 1;
			lat = 0;
			while (!pcpi_ready && lat < 200) begin
				// a unit that is not done must hold off the core's 16-cycle timeout
				if (lat >= 12 && !pcpi_wait && !pcpi_ready) begin
					errors = errors + 1;
					if (errors < 10) $display("FAIL: pcpi_wait low while busy (f3=%0d)", f3);
				end
				@(posedge clk); #1; lat = lat + 1;
			end
			exp = model(f3, a, b);
			checks = checks + 1;
			if (!pcpi_ready || !pcpi_wr || pcpi_rd !== exp) begin
				errors = errors + 1;
				if (errors < 10)
					$display("FAIL f3=%0d a=%h b=%h got=%h exp=%h ready=%b lat=%0d", f3, a, b, pcpi_rd, exp, pcpi_ready, lat);
			end
			if (lat < lat_min[f3]) lat_min[f3] = lat;
			if (lat > lat_max[f3]) lat_max[f3] = lat;
			@(negedge clk);
			pcpi_valid = 0;
			repeat (1 + ($unsigned($random) % 3)) @(negedge clk);
		end
	endtask

	reg [31:0] corner [0:15];
	reg [2:0]  f3_base;

	initial begin
		corner[0]  = 32'h0000_0000; corner[1]  = 32'h0000_0001; corner[2]  = 32'hFFFF_FFFF;
		corner[3]  = 32'h0000_0002; corner[4]  = 32'hFFFF_FFFE; corner[5]  = 32'h8000_0000;
		corner[6]  = 32'h7FFF_FFFF; corner[7]  = 32'h8000_0001; corner[8]  = 32'h0000_FFFF;
		corner[9]  = 32'hFFFF_0000; corner[10] = 32'h5555_5555; corner[11] = 32'hAAAA_AAAB;
		corner[12] = 32'h0000_0007; corner[13] = 32'hFFFF_FFF9; corner[14] = 32'h0001_0000;
		corner[15] = 32'h1234_5678;
		for (k = 0; k < 8; k = k + 1) begin lat_min[k] = 1000; lat_max[k] = 0; end
		f3_base = IS_DIV ? 3'd4 : 3'd0;

		repeat (4) @(posedge clk);
		resetn = 1;

		// every corner pair, every instruction of this unit (16*16*4 = 1024)
		for (i = 0; i < 16; i = i + 1)
			for (j = 0; j < 16; j = j + 1)
				for (k = 0; k < 4; k = k + 1)
					issue(f3_base + k[2:0], corner[i], corner[j]);

		// optional switching-activity dump for power analysis (+VCD): covers the
		// random phase only, and reports its length so energy/op can be computed
		if ($test$plusargs("VCD")) begin
			$dumpfile("activity.vcd");
			$dumpvars(1, u.dut);   // nets of the unit itself (not inside library cells)
			cyc0 = cyc;
		end

		// random operands; every 4th divisor small so quotients are large
		for (i = 0; i < N_RANDOM; i = i + 1)
			issue(f3_base + ($unsigned($random) % 4), $random,
			      (i % 4 == 0) ? ($random % 64) : $random);

		if ($test$plusargs("VCD")) begin
			$dumpoff;
			$display("POWER_WINDOW ops=%0d cycles=%0d", N_RANDOM, cyc - cyc0);
		end
		if (errors == 0)
			$display("UNIT TEST PASS (UNIT=%0d P=%0d): %0d checks", UNIT, P, checks);
		else
			$display("UNIT TEST FAIL (UNIT=%0d P=%0d): %0d errors in %0d checks", UNIT, P, errors, checks);
		for (k = 0; k < 4; k = k + 1)
			$display("LATENCY f3=%0d min=%0d max=%0d", f3_base + k, lat_min[f3_base + k], lat_max[f3_base + k]);
		$finish;
	end
endmodule

`default_nettype wire
