#!/usr/bin/env python3
"""RTL-to-GDS of every M unit with OpenROAD-flow-scripts on two PDKs.

All units in one PDK get the same clock target and floorplan settings; the
achieved critical-path delay is (T - WNS), so Fmax = 1/(T - WNS) whether the
target was met or not. Area is placed standard-cell area after the final
(finish) stage. Area-delay product (ADP) = area x time per operation, where
time per operation = latency_cycles x (T - WNS).

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
# clock target per PDK (ns), chosen so most units are near their limit
PDKS = {"nangate45": 2.0, "sky130hd": 6.0}

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
    name, pdk = job
    top, params, _ = UNITS[name]
    work = ROOT / "build/orfs" / pdk / name
    metrics = work / "metrics.json"
    if metrics.exists():
        return job, work
    work.mkdir(parents=True, exist_ok=True)
    (work / "constraint.sdc").write_text(SDC.format(top=top, period=PDKS[pdk]))
    files = " ".join(str(ROOT / f) for f in ("third_party/picorv32/picorv32.v",
                                             "rtl/pcpi_mul_booth.v", "rtl/pcpi_div_restoring.v"))
    (work / "config.mk").write_text(CONFIG.format(
        top=top, name=name, pdk=pdk, files=files, sdc=work / "constraint.sdc",
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


def main():
    jobs = [(n, p) for p in PDKS for n in UNITS]
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        done = list(ex.map(run, jobs))

    res = {}
    for (name, pdk), work in done:
        mf = work / "metrics.json"
        if not mf.exists():
            print(f"FAILED {pdk}/{name}: see {work}/make.log")
            continue
        m = json.loads(mf.read_text())
        T = PDKS[pdk]
        wns = m.get("finish__timing__setup__ws", 0.0)
        delay = T - wns
        lat = UNITS[name][2][0]
        area = m["finish__design__instance__area"]
        res.setdefault(pdk, {})[name] = {
            "clock_target_ns": T, "wns_ns": round(wns, 4), "crit_delay_ns": round(delay, 4),
            "fmax_mhz": round(1000 / delay, 1), "area_um2": round(area, 1),
            "stdcells": m.get("finish__design__instance__count__stdcell"),
            "power_mw": round(1000 * m.get("finish__power__total", 0), 3),
            "latency_cycles": lat, "op_time_ns": round(lat * delay, 2),
            "adp_um2_ns": round(area * lat * delay, 0),
            "drc_errors": m.get("detailedroute__route__drc_errors"),
        }
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "orfs.json").write_text(json.dumps(res, indent=2))
    lines = []
    for pdk in PDKS:
        lines += [f"### {pdk} (target {PDKS[pdk]} ns)", "",
                  "| unit | area (um^2) | cells | Fmax (MHz) | latency | op time (ns) | ADP (um^2*ns) | power (mW) |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for n in UNITS:
            r = res.get(pdk, {}).get(n)
            if r:
                lines.append(f"| {n} | {r['area_um2']} | {r['stdcells']} | {r['fmax_mhz']} | {r['latency_cycles']} | "
                             f"{r['op_time_ns']} | {r['adp_um2_ns']:.0f} | {r['power_mw']} |")
        lines.append("")
    (out / "orfs.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0 if all(len(res.get(p, {})) == len(UNITS) for p in PDKS) else 1


if __name__ == "__main__":
    sys.exit(main())
