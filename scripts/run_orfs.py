#!/usr/bin/env python3
"""RTL-to-GDS of every M unit with OpenROAD-flow-scripts on two PDKs.

Every unit is implemented at seven clock targets per PDK (same floorplan settings
for all). For each run the achieved critical-path delay is (T - WNS), so
Fmax = 1/(T - WNS) whether the target was met or not; area is the standard-cell
area after the final (finish) stage. Area-delay product (ADP) = area x time per
operation, with time per operation = latency_cycles x (T - WNS).

Two views are reported:
  * common target  - all units at the same clock target (PDKS), the like-for-like
                     comparison used for the detailed sign-off metrics;
  * best ADP       - each unit at the target that gives its lowest ADP, i.e. each
                     architecture at its own best operating point.

Writes results/orfs.json and results/orfs.md.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORFS = Path(os.environ.get("ORFS", Path.home() / "OpenROAD-flow-scripts"))
JOBS = int(os.environ.get("JOBS", "3"))
CORES_PER_JOB = int(os.environ.get("CORES_PER_JOB", "4"))

# same unit table as run_vivado.py: name -> (top, params, (MUL latency, MULH latency) or DIV latency)
UNITS = {
    "pico_mul":      ("picorv32_pcpi_mul",      {},             (36, 68)),
    "pico_fast_mul": ("picorv32_pcpi_fast_mul", {},             (2, 2)),
    "booth_d1":      ("pcpi_mul_booth",         {"DIGITS": 1},  (18, 18)),
    "booth_d2":      ("pcpi_mul_booth",         {"DIGITS": 2},  (10, 10)),
    "booth_d4":      ("pcpi_mul_booth",         {"DIGITS": 4},  (6, 6)),
    "pico_div":      ("picorv32_pcpi_div",      {},             (36, 36)),
    "restoring_b1":  ("pcpi_div_restoring",     {"BITS": 1},    (33, 33)),
    "restoring_b2":  ("pcpi_div_restoring",     {"BITS": 2},    (17, 17)),
    "restoring_b4":  ("pcpi_div_restoring",     {"BITS": 4},    (9, 9)),
}
# common clock target per PDK (ns) and the full sweep
PDKS = {"nangate45": 2.0, "sky130hd": 6.0}
SWEEP = {"nangate45": [0.35, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5], "sky130hd": [1.5, 2.0, 2.5, 3.5, 4.5, 6.0, 9.0]}


def workdir(pdk, name, period):
    """Common-target runs keep the plain name; other targets get a _T suffix."""
    tag = name if period == PDKS[pdk] else f"{name}_T{period:g}"
    return ROOT / "build/orfs" / pdk / tag

SDC = """current_design {top}
set clk_period {period}
set clk_io_pct 0.2
set clk_port [get_ports clk]
create_clock -name core_clock -period $clk_period $clk_port
set non_clock_inputs [all_inputs -no_clocks]
set_input_delay  [expr $clk_period * $clk_io_pct] -clock core_clock $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock core_clock [all_outputs]
"""

CONFIG = """export DESIGN_NAME     = {top}
export DESIGN_NICKNAME = {name}
export PLATFORM        = {pdk}
export VERILOG_FILES   = {files}
export SDC_FILE        = {sdc}
export VERILOG_TOP_PARAMS = {params}
export CORE_UTILIZATION = 40
export PLACE_DENSITY_LB_ADDON = 0.20
export TNS_END_PERCENT = 100
export SYNTH_REPEATABLE_BUILD = 1
export NUM_CORES = {cores}
"""


def run(job):
    name, pdk, period = job
    top, params, _ = UNITS[name]
    work = workdir(pdk, name, period)
    metrics = work / "metrics.json"
    if metrics.exists():
        return job, work
    work.mkdir(parents=True, exist_ok=True)
    (work / "constraint.sdc").write_text(SDC.format(top=top, period=period))
    files = " ".join(str(ROOT / f) for f in ("third_party/picorv32/picorv32.v",
                                             "rtl/pcpi_mul_booth.v", "rtl/pcpi_div_restoring.v"))
    (work / "config.mk").write_text(CONFIG.format(
        top=top, name=work.name, pdk=pdk, files=files, sdc=work / "constraint.sdc",
        params=" ".join(f"{k} {v}" for k, v in params.items()), cores=CORES_PER_JOB))
    cmd = (f"source {ORFS}/env.sh >/dev/null; "
           f"make -C {ORFS}/flow DESIGN_CONFIG={work}/config.mk WORK_HOME={work} "
           f"> {work}/make.log 2>&1")
    subprocess.run(["bash", "-c", cmd])
    # collect the final-stage metrics from the per-stage JSON logs
    m = {}
    for f in sorted((work / "logs").rglob("*.json")):
        try:
            m.update(json.loads(f.read_text()))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    if "finish__design__instance__area" in m:
        metrics.write_text(json.dumps(m, indent=1))
    return job, work


def summarize(name, pdk, period, work):
    m = json.loads((work / "metrics.json").read_text())
    wns = m.get("finish__timing__setup__ws", 0.0)
    delay = period - wns
    lat = UNITS[name][2][0]
    area = m["finish__design__instance__area"]
    return {"clock_target_ns": period, "wns_ns": round(wns, 4), "crit_delay_ns": round(delay, 4),
            "fmax_mhz": round(1000 / delay, 1), "area_um2": round(area, 1),
            "stdcells": m.get("finish__design__instance__count__stdcell"),
            "latency_cycles": lat, "latency_mulh_cycles": UNITS[name][2][1],
            "op_time_ns": round(lat * delay, 2), "adp_um2_ns": round(area * lat * delay, 0),
            "drc_errors": m.get("detailedroute__route__drc_errors")}


def main():
    jobs = [(n, p, t) for p in PDKS for t in SWEEP[p] for n in UNITS]
    # longest-first keeps the pool busy
    jobs.sort(key=lambda j: (j[2] != PDKS[j[1]], j[1] == "nangate45", j[2]))
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        done = list(ex.map(run, jobs))

    res, failed = {}, []
    for (name, pdk, period), work in done:
        if not (work / "metrics.json").exists():
            failed.append(f"{pdk}/{work.name}")
            continue
        r = res.setdefault(pdk, {}).setdefault(name, {"runs": []})
        r["runs"].append(summarize(name, pdk, period, work))
    for pdk, units in res.items():
        for name, r in units.items():
            r["runs"].sort(key=lambda x: x["clock_target_ns"])
            r["common"] = next((x for x in r["runs"] if x["clock_target_ns"] == PDKS[pdk]), None)
            r["best_adp"] = min(r["runs"], key=lambda x: x["adp_um2_ns"])
            r["best_fmax"] = max(r["runs"], key=lambda x: x["fmax_mhz"])
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "orfs.json").write_text(json.dumps(res, indent=2))

    lines = []
    for pdk in PDKS:
        u = res.get(pdk, {})
        lines += [f"## {pdk}", "",
                  f"### Common clock target ({PDKS[pdk]} ns), all units", "",
                  "| unit | area (µm²) | cells | WNS (ns) | Fmax (MHz) | latency | time/op (ns) | ADP (µm²·ns) |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for n in UNITS:
            r = u.get(n, {}).get("common")
            if r:
                lines.append(f"| {n} | {r['area_um2']} | {r['stdcells']} | {r['wns_ns']:+.3f} | {r['fmax_mhz']} | "
                             f"{r['latency_cycles']} | {r['op_time_ns']} | {r['adp_um2_ns']:.0f} |")
        lines += ["", f"### Each unit at its best-ADP clock target (sweep {SWEEP[pdk]} ns)", "",
                  "| unit | best target (ns) | area (µm²) | Fmax (MHz) | time/op (ns) | ADP (µm²·ns) | highest Fmax in sweep (MHz) |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for n in UNITS:
            if n in u:
                b, f = u[n]["best_adp"], u[n]["best_fmax"]
                lines.append(f"| {n} | {b['clock_target_ns']} | {b['area_um2']} | {b['fmax_mhz']} | {b['op_time_ns']} | "
                             f"{b['adp_um2_ns']:.0f} | {f['fmax_mhz']} (at {f['clock_target_ns']} ns, {f['area_um2']} µm²) |")
        lines += ["", "### All runs", "", "| unit | target (ns) | area (µm²) | WNS (ns) | Fmax (MHz) | ADP (µm²·ns) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for n in UNITS:
            for r in u.get(n, {}).get("runs", []):
                lines.append(f"| {n} | {r['clock_target_ns']} | {r['area_um2']} | {r['wns_ns']:+.3f} | "
                             f"{r['fmax_mhz']} | {r['adp_um2_ns']:.0f} |")
        lines.append("")
    if failed:
        lines += ["Failed runs: " + ", ".join(failed), ""]
    (out / "orfs.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
