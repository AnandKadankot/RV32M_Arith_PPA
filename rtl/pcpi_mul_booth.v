// pcpi_mul_booth.v - Sequential radix-4 Booth multiplier for PicoRV32 (PCPI)
//
// Implements the RV32M multiply instructions: MUL, MULH, MULHSU, MULHU.
//
// Algorithm (radix-4 Booth, shift-right form)
//   Operands are extended to 34 bits (sign- or zero-extended per instruction),
//   which turns all four signedness cases into one signed 34x34 multiply.
//   The multiplier Q is scanned two bits at a time together with the bit to
//   their right (q_m1). Each 3-bit group selects a partial product from
//   {0, +-M, +-2M}:
//
//     {q1,q0,q_m1}  000 001 010 011 100 101 110 111
//     digit          0  +1  +1  +2  -2  -1  -1   0
//
//   Each step adds digit*M to the high half H of the {H, L} product register
//   and shifts {H, L} right arithmetically by 2. A 34-bit multiplier needs 17
//   digits, versus 32-34 steps for radix-2 shift-and-add.
//
// Parameter DIGITS = Booth digits retired per clock cycle (1, 2 or 4). The
// loop is unrolled DIGITS times inside one cycle; the multiplier is
// sign-extended to a whole number of cycles (extra digits are always 0).
//
//   DIGITS   compute cycles   latency (pcpi_valid -> pcpi_ready)
//     1           17               18
//     2            9               10
//     4            5                6

`default_nettype none

module pcpi_mul_booth #(
	parameter DIGITS = 1
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
	localparam CYCLES = (17 + DIGITS - 1) / DIGITS;   // compute cycles
	localparam NDIG   = CYCLES * DIGITS;              // digits incl. padding
	localparam LW     = 2 * NDIG;                     // multiplier register width
	localparam HW     = 36;                           // high half: 34 bits + 2 guard bits

	// ---------------- decode ----------------
	wire insn_mul = pcpi_valid && pcpi_insn[6:0] == 7'b0110011
	             && pcpi_insn[31:25] == 7'b0000001 && !pcpi_insn[14];
	wire [1:0] f3 = pcpi_insn[13:12];          // 00 mul, 01 mulh, 10 mulhsu, 11 mulhu
	wire rs1_signed = f3 == 2'b01 || f3 == 2'b10;
	wire rs2_signed = f3 == 2'b01;

	// ---------------- state ----------------
	reg                 busy, done;
	reg  [$clog2(CYCLES+1)-1:0] count;
	reg                 want_high;              // MULH*: return product[63:32]
	reg  signed [33:0]  m;                      // multiplicand
	reg  signed [HW-1:0] h;                     // high half of product register
	reg  [LW-1:0]       l;                      // low half (multiplier, shifted out)
	reg                 q_m1;                   // bit to the right of the current pair

	wire start = resetn && insn_mul && !busy && !done;

	// ---------------- DIGITS Booth steps (combinational) ----------------
	reg  signed [HW-1:0] h_n;
	reg  [LW-1:0]        l_n;
	reg                  q_n;
	reg  signed [HW-1:0] pp;
	integer i;
	always @* begin
		h_n = h; l_n = l; q_n = q_m1;
		for (i = 0; i < DIGITS; i = i + 1) begin
			case ({l_n[1:0], q_n})
				3'b001, 3'b010: pp =  m;
				3'b011:         pp =  m <<< 1;
				3'b100:         pp = -(m <<< 1);
				3'b101, 3'b110: pp = -m;
				default:        pp = 0;
			endcase
			h_n = h_n + pp;
			q_n = l_n[1];
			l_n = {h_n[1:0], l_n[LW-1:2]};
			h_n = h_n >>> 2;
		end
	end

	// product bits [63:0] are the low 64 bits of {h, l}
	wire [HW+LW-1:0] prod = {h, l};

	always @(posedge clk) begin
		if (!resetn) begin
			busy <= 1'b0;
			done <= 1'b0;
		end else if (start) begin
			m         <= rs1_signed ? {{2{pcpi_rs1[31]}}, pcpi_rs1} : {2'b00, pcpi_rs1};
			l         <= rs2_signed ? {{(LW-32){pcpi_rs2[31]}}, pcpi_rs2} : {{(LW-32){1'b0}}, pcpi_rs2};
			h         <= 0;
			q_m1      <= 1'b0;
			want_high <= f3 != 2'b00;
			count     <= CYCLES;
			busy      <= 1'b1;
		end else if (busy) begin
			h     <= h_n;
			l     <= l_n;
			q_m1  <= q_n;
			count <= count - 1'b1;
			if (count == 1) begin
				busy <= 1'b0;
				done <= 1'b1;
			end
		end else if (done) begin
			done <= 1'b0;                 // result is presented during the done cycle
		end
	end

	assign pcpi_ready = done;
	assign pcpi_rd    = want_high ? prod[63:32] : prod[31:0];

	assign pcpi_wr   = pcpi_ready;
	assign pcpi_wait = insn_mul;   // keep the core's 16-cycle PCPI timeout from firing
endmodule

`default_nettype wire
