#!/usr/bin/env python3
"""Vivado OOC implementation of every M unit alone and every full core.

Each design is implemented at three clock targets; Fmax = 1000/(T - WNS) and
the best run is kept. Note: the clock constrains register-to-register paths
only (no I/O delays in OOC mode).

Writes results/vivado_units.json, results/vivado_cores.json (+ .md).
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = Path(os.environ.get("VIVADO_SETTINGS", Path.home() / "AMD/2025.2/Vivado/settings64.sh"))
JOBS = int(os.environ.get("JOBS", "6"))

# name: (top, generics, latency MUL / MULH or DIV in cycles, from tb_unit)
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
CORES = {
    "stock_seq":  {"MUL": 1, "DIV": 1},
    "stock_fast": {"MUL": 2, "DIV": 1},
    "booth1":     {"MUL": 3, "MUL_P": 1, "DIV": 2, "DIV_P": 1},
    "booth2":     {"MUL": 3, "MUL_P": 2, "DIV": 2, "DIV_P": 2},
    "booth4":     {"MUL": 3, "MUL_P": 4, "DIV": 2, "DIV_P": 4},
}
UNIT_PERIODS = [2.5, 3.5, 5.0]
CORE_PERIODS = [4.0, 5.0, 6.0]


def run(job):
    kind, name, top, gens, period = job
    out = ROOT / "build/vivado" / kind / f"{name}_p{period:.1f}"
    if not (out / "summary.txt").exists():
        out.mkdir(parents=True, exist_ok=True)
        g = " ".join(f"{k}={v}" for k, v in gens.items())
        cmd = (f"source {SETTINGS} >/dev/null 2>&1; unset LIBRARY_PATH; "
               f"vivado -mode batch -nojournal -log {out}/vivado.log "
               f"-source {ROOT}/scripts/vivado_impl.tcl -tclargs {out} {period} {top} {g} > /dev/null 2>&1")
        subprocess.run(["bash", "-c", cmd], cwd=out)
    return job, out


def parse(out):
    s = dict(l.split(" ", 1) for l in (out / "summary.txt").read_text().splitlines())
    u = (out / "util.rpt").read_text()
    num = lambda pat: int(re.search(pat, u).group(1))
    period, wns = float(s["period"]), float(s["wns"])
    return {"period_ns": period, "wns_ns": wns, "fmax_mhz": round(1000 / (period - wns), 1),
            "lut": num(r"\|\s*Slice LUTs\s*\|\s*(\d+)"), "ff": num(r"\|\s*Slice Registers\s*\|\s*(\d+)"),
            "dsp": num(r"\|\s*DSPs\s*\|\s*(\d+)"), "crit_end": s["crit_end"],
            "crit_levels": int(s["crit_levels"])}


def collect(kind, table, done):
    res = {}
    for (k, name, top, gens, period), out in done:
        if k != kind:
            continue
        if not (out / "summary.txt").exists():
            print(f"FAILED {kind}/{name} @ {period}: see {out}/vivado.log")
            continue
        res.setdefault(name, {"top": top, "generics": gens, "runs": []})["runs"].append(parse(out))
    for name, r in res.items():
        r["best"] = max(r["runs"], key=lambda x: x["fmax_mhz"])
        if kind == "units":
            r["latency_cycles"] = table[name][2]
    return res


def main():
    jobs = [("units", n, t, g, p) for n, (t, g, _) in UNITS.items() for p in UNIT_PERIODS]
    jobs += [("cores", n, "core_top", g, p) for n, g in CORES.items() for p in CORE_PERIODS]
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        done = list(ex.map(run, jobs))
    units, cores = collect("units", UNITS, done), collect("cores", CORES, done)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "vivado_units.json").write_text(json.dumps(units, indent=2))
    (out / "vivado_cores.json").write_text(json.dumps(cores, indent=2))

    lines = ["| unit | LUT | FF | DSP | Fmax (MHz) | latency (cyc) | op time (ns) |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for n in UNITS:
        if n in units:
            b, lat = units[n]["best"], units[n]["latency_cycles"][0]
            lines.append(f"| {n} | {b['lut']} | {b['ff']} | {b['dsp']} | {b['fmax_mhz']} | {lat} | "
                         f"{lat * 1000 / b['fmax_mhz']:.1f} |")
    lines += ["", "| core | LUT | FF | DSP | Fmax (MHz) | critical path end |", "|---|---:|---:|---:|---:|---|"]
    for n in CORES:
        if n in cores:
            b = cores[n]["best"]
            lines.append(f"| {n} | {b['lut']} | {b['ff']} | {b['dsp']} | {b['fmax_mhz']} | {b['crit_end']} |")
    (out / "vivado.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if len(units) == len(UNITS) and len(cores) == len(CORES) else 1


if __name__ == "__main__":
    sys.exit(main())
