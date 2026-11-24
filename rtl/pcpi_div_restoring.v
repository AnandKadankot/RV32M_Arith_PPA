// pcpi_div_restoring.v - Sequential restoring divider for PicoRV32 (PCPI)
//
// Implements the RV32M divide instructions: DIV, DIVU, REM, REMU.
//
// Algorithm
//   Signed operands are converted to magnitudes, an unsigned 32/32 restoring
//   division produces quotient and remainder, and the signs are fixed at the
//   end. Each restoring step shifts the next dividend bit into the partial
//   remainder R and subtracts the divisor if it fits:
//
//       R' = {R, next bit};  if (R' >= D) { R' -= D; q = 1 } else q = 0
//
// Parameter BITS = quotient bits produced per clock cycle (1, 2 or 4): the
// step is unrolled BITS times in one cycle (radix 2, 4 or 16).
//
//   BITS   compute cycles   latency (pcpi_valid -> pcpi_ready)
//     1          32               33
//     2          16               17
//     4           8                9
//
// RISC-V corner cases (no traps on divide errors):
//   x / 0            -> quotient = all ones (-1), remainder = x
//   INT_MIN / -1     -> quotient = INT_MIN,       remainder = 0
// Both fall out of the unsigned algorithm; the only special handling needed
// is to *not* negate the all-ones quotient of a divide by zero.

`default_nettype none

module pcpi_div_restoring #(
	parameter BITS = 1
) (
	input  wire        clk,
	input  wire        resetn,

	input  wire        pcpi_valid,
	input  wire [31:0] pcpi_insn,
	input  wire [31:0] pcpi_rs1,
	input  wire [31:0] pcpi_rs2,
	output wire        pcpi_wr,
	output wire [31:0] pcpi_rd,
	output wire        pcpi_wait,
	output wire        pcpi_ready
);
	localparam CYCLES = 32 / BITS;

	// ---------------- decode ----------------
	wire insn_div = pcpi_valid && pcpi_insn[6:0] == 7'b0110011
	             && pcpi_insn[31:25] == 7'b0000001 && pcpi_insn[14];
	wire [1:0] f3 = pcpi_insn[13:12];          // 00 div, 01 divu, 10 rem, 11 remu
	wire is_signed = !f3[0];

	// ---------------- state ----------------
	reg         busy, done;
	reg  [$clog2(CYCLES+1)-1:0] count;
	reg         want_rem, neg_q, neg_r;
	reg  [31:0] d;      // divisor magnitude
	reg  [31:0] r;      // partial remainder
	reg  [31:0] q;      // dividend bits shifting out, quotient bits shifting in

	wire start = resetn && insn_div && !busy && !done;

	wire a_neg = is_signed && pcpi_rs1[31];
	wire b_neg = is_signed && pcpi_rs2[31];

	// ---------------- BITS restoring steps (combinational) ----------------
	reg  [31:0] r_n, q_n;
	reg  [32:0] r_sh;
	reg  [33:0] diff;
	integer i;
	always @* begin
		r_n = r; q_n = q;
		for (i = 0; i < BITS; i = i + 1) begin
			r_sh = {r_n, q_n[31]};
			diff = {1'b0, r_sh} - {2'b00, d};
			q_n  = {q_n[30:0], ~diff[33]};          // 1 if no borrow (R' >= D)
			r_n  = diff[33] ? r_sh[31:0] : diff[31:0];
		end
	end

	always @(posedge clk) begin
		if (!resetn) begin
			busy <= 1'b0;
			done <= 1'b0;
		end else if (start) begin
			q        <= a_neg ? -pcpi_rs1 : pcpi_rs1;
			d        <= b_neg ? -pcpi_rs2 : pcpi_rs2;
			r        <= 32'd0;
			want_rem <= f3[1];
			neg_q    <= (a_neg ^ b_neg) && pcpi_rs2 != 32'd0;
			neg_r    <= a_neg;
			count    <= CYCLES;
			busy     <= 1'b1;
		end else if (busy) begin
			r     <= r_n;
			q     <= q_n;
			count <= count - 1'b1;
			if (count == 1) begin
				busy <= 1'b0;
				done <= 1'b1;
			end
		end else if (done) begin
			done <= 1'b0;                 // result is presented during the done cycle
		end
	end

	wire [31:0] res = want_rem ? r : q;
	wire        neg = want_rem ? neg_r : neg_q;

	assign pcpi_ready = done;
	assign pcpi_wr    = done;
	assign pcpi_rd    = neg ? -res : res;
	assign pcpi_wait  = insn_div;   // keep the core's 16-cycle PCPI timeout from firing
endmodule

`default_nettype wire
