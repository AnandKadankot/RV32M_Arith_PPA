#!/usr/bin/env python3
"""Plots from results/*.json:

  results/asic_tradeoff.png  area vs. time per operation, per PDK (ORFS)
  results/bench_speedup.png  wall-clock speedup of each core vs. stock PicoRV32
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
orfs = json.loads((R / "orfs.json").read_text())
system = json.loads((R / "system.json").read_text())
cores = json.loads((R / "vivado_cores.json").read_text())

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#6b6a64", "#e4e3de"
MUL_C, DIV_C, NEUTRAL = "#2a78d6", "#eb6834", "#b9b8b0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.edgecolor": GRID})

LABEL = {"pico_mul": "pico_mul", "pico_fast_mul": "pico_fast_mul", "booth_d1": "Booth ×1",
         "booth_d2": "Booth ×2", "booth_d4": "Booth ×4", "pico_div": "pico_div",
         "restoring_b1": "restoring ×1", "restoring_b2": "restoring ×2", "restoring_b4": "restoring ×4"}
MULS = ["pico_mul", "pico_fast_mul", "booth_d1", "booth_d2", "booth_d4"]
DIVS = ["pico_div", "restoring_b1", "restoring_b2", "restoring_b4"]
# label offsets (points) where neighbours would collide
OFFSET = {("nangate45", "booth_d2"): (-7, 0, "right"), ("nangate45", "restoring_b2"): (-7, 7, "right"),
          ("nangate45", "pico_mul"): (-7, -7, "right"),
          ("sky130hd", "pico_mul"): (7, 7, "left"), ("sky130hd", "booth_d2"): (-7, 0, "right"),
          ("sky130hd", "pico_div"): (7, 4, "left"), ("sky130hd", "restoring_b1"): (7, -8, "left"),
          ("sky130hd", "booth_d1"): (-7, 0, "right")}
PDK_TITLE = {"nangate45": "Nangate 45 nm", "sky130hd": "SkyWater 130 nm"}

# ---------------------------------------------------------------- 1. ASIC trade-off
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), facecolor=SURFACE)
for ax, pdk in zip(axes, ["nangate45", "sky130hd"]):
    ax.set_facecolor(SURFACE)
    d = orfs[pdk]
    for names, col, fam in ((MULS, MUL_C, "multipliers (MUL)"), (DIVS, DIV_C, "dividers (DIV)")):
        # every clock target of the sweep, faint and joined per unit
        for n in names:
            runs = d[n]["runs"]
            ax.plot([r["op_time_ns"] for r in runs], [r["area_um2"] for r in runs], color=col,
                    alpha=0.25, linewidth=1, marker="o", markersize=3, zorder=2)
        xs = [d[n]["best_adp"]["op_time_ns"] for n in names]
        ys = [d[n]["best_adp"]["area_um2"] for n in names]
        ax.scatter(xs, ys, s=64, color=col, edgecolor=SURFACE, linewidth=2, zorder=3, label=fam)
        for n, x, y in zip(names, xs, ys):
            dx, dy, ha = OFFSET.get((pdk, n), (7, 3, "left"))
            ax.annotate(LABEL[n], (x, y), xytext=(dx, dy), textcoords="offset points",
                        fontsize=8.5, color=INK, ha=ha, va="center")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("time per operation (ns)  =  latency × critical-path delay")
    ax.set_ylabel("standard-cell area (µm²)")
    ax.set_title(PDK_TITLE[pdk], loc="left", fontsize=11)
    ax.grid(True, which="major", color=GRID, linewidth=0.8, zorder=0)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
axes[0].legend(frameon=False, loc="upper right", fontsize=9)
fig.suptitle("RV32M units after place-and-route (OpenROAD): large dots = each unit at its best "
             "area-delay point; faint = clock-target sweep. Lower-left is better.",
             x=0.01, ha="left", fontsize=10.5)
fig.tight_layout()
fig.savefig(R / "asic_tradeoff.png", dpi=160, facecolor=SURFACE)

# ---------------------------------------------------------------- 2. benchmark speedup
CFG = ["stock_seq", "stock_fast", "booth1", "booth2", "booth4"]
CFG_LABEL = ["stock\niter.", "stock\nfast", "new\n×1", "new\n×2", "new\n×4"]
KERN = [("matmul32", "matmul32 (MUL)"), ("fixmul", "fixmul (MUL+MULH)"),
        ("radix", "radix (DIVU+REMU)"), ("sdiv", "sdiv (DIV+REM)")]
fig, axes = plt.subplots(1, 4, figsize=(13, 4.0), facecolor=SURFACE, sharey=True)
for ax, (k, title) in zip(axes, KERN):
    ax.set_facecolor(SURFACE)
    t = [system[c]["kernels"][k]["cycles"] / cores[c]["best"]["fmax_mhz"] for c in CFG]  # µs
    sp = [t[0] / x for x in t]
    cols = [NEUTRAL, NEUTRAL, MUL_C, MUL_C, MUL_C]
    bars = ax.bar(range(5), sp, color=cols, width=0.64, zorder=2)
    for b, v in zip(bars, sp):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.04, f"{v:.2f}×", ha="center",
                va="bottom", fontsize=8.5, color=INK)
    ax.axhline(1, color=MUTED, linewidth=0.8, zorder=1)
    ax.set_xticks(range(5)); ax.set_xticklabels(CFG_LABEL, fontsize=8.5)
    ax.set_title(title, loc="left", fontsize=10)
    ax.grid(True, axis="y", color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_ylabel("wall-clock speedup vs. stock iterative")
fig.suptitle("Benchmark wall-clock time = cycles (xsim) / core Fmax (Vivado, xc7z020)",
             x=0.01, ha="left", fontsize=12)
fig.text(0.01, 0.005, "stock iter. = PicoRV32 iterative MUL + DIV   ·   stock fast = PicoRV32 DSP multiplier + "
         "iterative DIV   ·   new ×N = Booth radix-4 multiplier + restoring divider, N steps/cycle",
         fontsize=8.5, color=MUTED)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(R / "bench_speedup.png", dpi=160, facecolor=SURFACE)
print("wrote", R / "asic_tradeoff.png", R / "bench_speedup.png")
