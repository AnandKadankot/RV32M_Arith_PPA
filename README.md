# RV32M_Arith_PPA

Design-space exploration of RISC-V **M-extension** (multiply/divide) hardware for the
[PicoRV32](https://github.com/YosysHQ/picorv32) core: a new **radix-4 Booth multiplier** and a
**restoring divider**, each parameterised to retire 1, 2 or 4 steps per clock, compared against
PicoRV32's own three M units on

- **correctness:** a reference-model unit testbench with mutation tests, and the official riscv-tests on the full core;
- **performance:** cycle-accurate benchmarks that each stress one instruction class;
- **FPGA PPA:** Vivado place-and-route on a Zynq-7020 (xc7z020clg400-1);
- **ASIC PPA:** full RTL-to-GDS in OpenROAD-flow-scripts on **Nangate 45 nm** and **SkyWater 130 nm**.

## Units under test

| unit | source | algorithm | latency (cycles) |
|---|---|---|---|
| `pico_mul` | PicoRV32 `ENABLE_MUL` | iterative shift-and-add | 36 (MUL), 68 (MULH/MULHSU/MULHU) |
| `pico_fast_mul` | PicoRV32 `ENABLE_FAST_MUL` | single 33×33 multiply | 2 |
| `booth_d1/d2/d4` | `rtl/pcpi_mul_booth.v` | radix-4 Booth, 1/2/4 digits per cycle | 18 / 10 / 6 |
| `pico_div` | PicoRV32 `ENABLE_DIV` | iterative shift-subtract | 36 |
| `restoring_b1/b2/b4` | `rtl/pcpi_div_restoring.v` | restoring, 1/2/4 bits per cycle (radix 2/4/16) | 33 / 17 / 9 |

Latencies are measured by the testbench (`pcpi_valid` to `pcpi_ready`).

The Booth unit extends both operands to 34 bits, which turns MUL, MULH, MULHSU and MULHU into
one signed multiply of 17 Booth digits. The divider works on magnitudes and fixes the signs at
the end. The RISC-V divide-by-zero and overflow results fall out of the algorithm, apart from
one guard: the all-ones quotient of a signed divide by zero must not be negated.

## Verification

| check | result |
|---|---|
| Unit testbench (`sim/tb_unit.v`): 16×16 corner-value pairs × 4 instructions + 20,000 random operations, against an RV32M reference model; also checks PicoRV32's 16-cycle `pcpi_wait` timeout rule | **all 9 units pass 21,024 checks each** |
| Mutation test: Booth digit +2 uses +M instead of +2M | caught (14,887 errors) |
| Mutation test: signed divide by zero negates the quotient | caught (19 errors) |
| Full core (`sim/tb_soc.v`): 45 riscv-tests (37 rv32ui + 8 rv32um) | **45/45 on all 5 core configurations** |
| Benchmark checksums against an independent Python model | all match |

Details: [`results/unit_tests.md`](results/unit_tests.md), [`results/system.md`](results/system.md).

## ASIC results (OpenROAD, post-route)

![ASIC trade-off](results/asic_tradeoff.png)

Nangate 45 nm, 2.0 ns clock target, identical floorplan settings and constraints for every unit:

| unit | area (µm²) | Fmax (MHz) | latency | time/op (ns) | ADP (µm²·ns) |
|---|---:|---:|---:|---:|---:|
| pico_mul | 2,608.7 | 1,304 | 36 | 27.6 | 71,996 |
| pico_fast_mul | 8,184.6 | 556 | 2 | 3.6 | **29,433** |
| booth_d1 | **1,658.5** | 897 | 18 | 20.1 | 33,298 |
| booth_d2 | 2,206.2 | 658 | 10 | 15.2 | 33,552 |
| booth_d4 | 3,456.4 | 508 | 6 | 11.8 | 40,803 |
| pico_div | 2,902.1 | 1,074 | 36 | 33.5 | 97,314 |
| restoring_b1 | **1,905.4** | 824 | 33 | 40.1 | 76,347 |
| restoring_b2 | 2,285.7 | 718 | 17 | 23.7 | **54,125** |
| restoring_b4 | 3,834.7 | 453 | 9 | 19.9 | 76,166 |

The SkyWater 130 nm results lead to the same conclusions; see [`results/orfs.md`](results/orfs.md).

- **Booth radix-4 is the smallest multiplier:** 36% smaller than `pico_mul` and **4.9× smaller than the
  single-cycle `pico_fast_mul`**, with **2.2× lower area-delay product (ADP) than `pico_mul`**
  (1.5× on 130 nm). Counting MULH latency (68 cycles), `pico_mul` falls further behind.
- `pico_fast_mul` has the best multiplier ADP: it is fast, but it costs almost 5× the area.
- **The 2-bit-per-cycle restoring divider has 1.8× lower ADP than `pico_div`** (1.7× on 130 nm).
  The 1-bit version is 34% smaller than `pico_div`.
- **Unrolling has diminishing returns.** Each extra step per cycle chains another 33–36-bit adder
  into the critical path. Going from 2 to 4 steps per cycle makes ADP worse for both units, on both processes.

ADP = area × latency × (clock period − WNS). Power figures in `results/orfs.md` are OpenROAD
vectorless estimates and are not used for any conclusion here.

## FPGA results (Vivado, Zynq-7020, out-of-context, best of 3 clock targets)

| unit | LUT | FF | DSP | Fmax (MHz) | time/op (ns) |
|---|---:|---:|---:|---:|---:|
| pico_mul | 225 | 255 | 0 | 414.9 | 86.8 |
| pico_fast_mul | 73 | 37 | 4 | 175.7 | 11.4 |
| booth_d1 | 217 | 110 | 0 | 230.6 | 78.1 |
| booth_d2 | 321 | 117 | 0 | 163.6 | 61.1 |
| booth_d4 | 533 | 116 | 0 | 105.8 | 56.7 |
| pico_div | 342 | 201 | 0 | 209.1 | 172.2 |
| restoring_b1 | 233 | 107 | 0 | 246.0 | 134.1 |
| restoring_b2 | 282 | 106 | 0 | 148.5 | 114.5 |
| restoring_b4 | 378 | 105 | 0 | 74.7 | 120.5 |

| core (PicoRV32 RV32IMC +) | LUT | FF | DSP | Fmax (MHz) |
|---|---:|---:|---:|---:|
| stock_seq: pico_mul + pico_div | 1,884 | 1,087 | 0 | 151.1 |
| stock_fast: pico_fast_mul + pico_div | 1,706 | 955 | 4 | 149.6 |
| booth1: booth_d1 + restoring_b1 | 1,729 | 854 | 0 | 146.4 |
| booth2: booth_d2 + restoring_b2 | 1,859 | 849 | 0 | 141.7 |
| booth4: booth_d4 + restoring_b4 | 2,201 | 851 | 0 | **73.7** |

On FPGA, `pico_fast_mul` maps onto four hard DSP48 multipliers, so its LUT count hides its real cost.
The ASIC flow, which has only standard cells, is the technology-neutral comparison.

## Benchmarks: cycles are not the whole story

| kernel | instructions | stock_seq | stock_fast | booth1 | booth2 | booth4 |
|---|---|---:|---:|---:|---:|---:|
| matmul32: 16×16 int32 matrix multiply | MUL | 312,363 | 173,099 | 238,635 | 205,867 | 189,483 |
| fixmul: 1,024 Q16.16 products | MUL + MULH | 171,061 | 68,661 | 101,429 | 85,045 | 76,853 |
| radix: 256 values printed in a run-time base | DIVU + REMU | 254,016 | 254,016 | 239,748 | 163,652 | 125,604 |
| sdiv: 1,024 signed quotient + remainder | DIV + REM | 126,003 | 126,003 | 119,859 | 87,091 | 70,707 |

Cycle counts from xsim, measured with `rdcycle`. Wall-clock time = cycles / core Fmax:

![Benchmark speedup](results/bench_speedup.png)

- **In cycles, `booth4` is the fastest design without DSPs:** radix 2.02× and sdiv 1.78× vs. stock.
  **In wall-clock time it is the slowest.** Its radix-16 divider chains four 33-bit subtractors
  (41 logic levels, 36 of them CARRY4) and halves the core clock to 73.7 MHz.
- **`booth2` is the best design without DSPs:** 1.36–1.89× faster than stock PicoRV32 on every kernel.
- `booth1` replaces both stock units with 155 fewer LUTs and 233 fewer flip-flops, at nearly
  the same clock.
- For multiply-heavy code on FPGA, the DSP-based `stock_fast` is still the fastest (fixmul 2.47×).

## Repository layout

```
rtl/      pcpi_mul_booth.v, pcpi_div_restoring.v, core_top.v (selectable M units)
sim/      tb_unit.v (unit testbench), tb_soc.v (full-core testbench)
sw/       riscv-tests harness, benchmark kernels, linker script, Makefile
scripts/  run_unit_tests.py, run_system.py, run_vivado.py + vivado_impl.tcl,
          run_orfs.py, make_plots.py, bin2hex.py
results/  all numbers above as .json/.md, plus the plots
```

## Reproducing

```sh
git clone https://github.com/YosysHQ/picorv32 third_party/picorv32   # tested at ef203c2
python3 scripts/run_unit_tests.py         # 9 units + 2 mutants (Vivado xsim)
python3 scripts/run_system.py             # riscv-tests + benchmarks on 5 cores
JOBS=6 python3 scripts/run_vivado.py      # FPGA implementation
JOBS=3 python3 scripts/run_orfs.py        # ASIC flow (needs OpenROAD-flow-scripts in $ORFS)
python3 scripts/make_plots.py
```

Tools used: Vivado 2025.2 (xsim and implementation), the RISC-V GCC from Vitis 2025.2, and OpenROAD-flow-scripts.

## Notes and limitations

- FPGA numbers come from implementation reports (out-of-context, reg-to-reg); no board was used.
- ASIC Fmax is post-route (clock period − WNS) at one fixed target per process. Units that met the
  target with large slack were not pushed harder by the tools, so their Fmax is conservative.
- One residual routing DRC remains in the stock `pico_div` on sky130hd; every other run is DRC-clean.
- PicoRV32 is not pipelined, so every multi-cycle operation stalls the core. In a pipelined
  core, part of this latency would overlap with independent instructions.

PicoRV32 is by Claire Xenia Wolf and is ISC-licensed. It is fetched separately and not included here.
