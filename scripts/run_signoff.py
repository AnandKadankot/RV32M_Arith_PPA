#!/usr/bin/env python3
"""Detailed physical-design metrics for every ORFS run (after run_orfs.py).

Per unit and PDK:
  * area after synthesis, placement, CTS and routing (standard-cell area)
  * setup WNS/TNS, hold WNS/TNS, Fmax after placement, CTS and routing
  * clock-tree synthesis: setup skew, clock buffers/inverters, timing-repair buffers
  * global-routing congestion: usage per metal layer, overflow
  * routed signal-metal area per layer (wire length x drawn width, from the final DEF)
  * critical path: start/end points, logic depth, cell mix, data arrival time
  * gate-level simulation of the routed netlist (functional check), and power with
    switching activity measured on every net in that simulation; energy per operation

Power flow: Yosys turns the PDK liberty file into simulation models of the cells; the
routed netlist (6_final.v) is simulated zero-delay in xsim with tb_unit (N_RANDOM random
operations, results checked as usual) and a VCD of all its nets is dumped;
vcd_activity.py turns that into activity/duty per net; power_gls.tcl annotates the
driver of every net in OpenSTA, with the extracted parasitics (SPEF).

Writes results/signoff.json and results/signoff.md.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_orfs import UNITS, PDKS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ORFS = Path(os.environ.get("ORFS", Path.home() / "OpenROAD-flow-scripts"))
OPENROAD = ORFS / "tools/install/OpenROAD/bin/openroad"
SETTINGS = Path(os.environ.get("VIVADO_SETTINGS", Path.home() / "AMD/2025.2/Vivado/settings64.sh"))
N_RANDOM = 1000
TB_PERIOD_NS = 10.0
SIM = {  # unit -> (tb_unit UNIT, P)
    "pico_mul": (0, 1), "pico_fast_mul": (1, 1), "booth_d1": (2, 1), "booth_d2": (2, 2),
    "booth_d4": (2, 4), "pico_div": (3, 1), "restoring_b1": (4, 1), "restoring_b2": (4, 2),
    "restoring_b4": (4, 4),
}
PLAT = {
    "nangate45": {"tlef": "lef/NangateOpenCellLibrary.tech.lef",
                  "lib": ["lib/NangateOpenCellLibrary_typical.lib"]},
    "sky130hd": {"tlef": "lef/sky130_fd_sc_hd.tlef",
                 "lib": ["lib/sky130_fd_sc_hd__tt_025C_1v80.lib"]},
}


# ------------------------------------------------------------------ gate-level simulation + power
YOSYS = ORFS / "tools/install/yosys/bin/yosys"


def cell_models(pdk, init=None):
    """Simulation models of the PDK cells. init=None leaves flip-flops at X after
    power-up (strict); init=0/1 starts every flip-flop at that value."""
    tag = "x" if init is None else str(init)
    out = ROOT / f"build/gls/{pdk}_cells_{tag}.v"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        raw = ROOT / f"build/gls/{pdk}_cells_raw.v"
        if not raw.exists():
            libs = " ".join(str(ORFS / "flow/platforms" / pdk / l) for l in PLAT[pdk]["lib"])
            subprocess.run([str(YOSYS), "-q", "-p",
                            f"read_liberty -ignore_miss_func {libs}; write_verilog -noattr {raw}"], check=True)
        txt = raw.read_text()
        if init is not None:
            txt = re.sub(r"^(\s*)reg (\w+);", rf"\1reg \2 = 1'b{init};", txt, flags=re.M)
        out.write_text(txt)
    return out


def gls_run(pdk, name, init, vcd):
    """Gate-level simulation of the routed netlist with tb_unit; returns (result, checks, errors)."""
    tag = "x" if init is None else str(init)
    work = ROOT / "build/gls" / pdk / name / f"init_{tag}"
    work.mkdir(parents=True, exist_ok=True)
    base = ROOT / f"build/orfs/{pdk}/{name}/results/{pdk}/{name}/base"
    log = work / "sim.log"
    if not log.exists() or "UNIT TEST" not in log.read_text():
        unit, p = SIM[name]
        cmd = (f"source {SETTINGS} >/dev/null 2>&1; unset LIBRARY_PATH; "
               f"xvlog -sv {cell_models(pdk, init)} {base}/6_final.v > xvlog.log 2>&1 && "
               f"xvlog -sv -d GLS {ROOT}/sim/tb_unit.v >> xvlog.log 2>&1 && "
               f"xelab -debug off --timescale 1ns/1ps -generic_top UNIT={unit} -generic_top P={p} "
               f"-generic_top N_RANDOM={N_RANDOM} tb_unit -s t > xelab.log 2>&1 && "
               f"xsim t -R {'-testplusarg VCD' if vcd else ''} > sim.log 2>&1")
        subprocess.run(["bash", "-c", cmd], cwd=work)
    txt = log.read_text() if log.exists() else ""
    if "UNIT TEST PASS" in txt:
        return {"result": "PASS", "checks": int(re.search(r"(\d+) checks", txt).group(1)), "errors": 0}, work
    m = re.search(r"(\d+) errors in (\d+) checks", txt)
    first = re.search(r"^FAIL .*$", txt, re.M)
    return {"result": "FAIL" if m else "ERROR", "checks": int(m.group(2)) if m else 0,
            "errors": int(m.group(1)) if m else 0, "first_failure": first.group(0) if first else ""}, work


def gls_power(job):
    pdk, name = job
    gls = {}
    gls["x"], _ = gls_run(pdk, name, None, False)
    gls["1"], _ = gls_run(pdk, name, 1, False)
    gls["0"], work = gls_run(pdk, name, 0, True)      # power activity from the all-0 run
    base = ROOT / f"build/orfs/{pdk}/{name}/results/{pdk}/{name}/base"
    act, out = work / "act.tcl", work / "power"
    if not act.exists() and (work / "activity.vcd").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/vcd_activity.py"), str(work / "activity.vcd"),
                        str(TB_PERIOD_NS), str(act)], check=True, stdout=subprocess.DEVNULL)
        (work / "activity.vcd").unlink()
    w = re.search(r"POWER_WINDOW ops=(\d+) cycles=(\d+)", (work / "sim.log").read_text())
    if not w or not act.exists():
        return job, gls, None, None
    ops, cyc = map(int, w.groups())
    if not Path(str(out) + ".rpt").exists():
        plat = ORFS / "flow/platforms" / pdk
        tcl = work / "power.tcl"
        tcl.write_text(
            f"set ::db {base}/6_final.odb\nset ::lib {{{' '.join(str(plat / l) for l in PLAT[pdk]['lib'])}}}\n"
            f"set ::sdc {base}/6_final.sdc\nset ::spef {base}/6_final.spef\nset ::act {act}\n"
            f"set ::out {out}\nsource {ROOT}/scripts/power_gls.tcl\n")
        subprocess.run([str(OPENROAD), "-no_init", "-exit", str(tcl)], cwd=work,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
    rpt = Path(str(out) + ".rpt").read_text()
    tot = re.search(r"^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", rpt, re.M).groups()
    clk = re.search(r"^Clock\s+\S+\s+\S+\s+\S+\s+(\S+)", rpt, re.M).group(1)
    ann = out.read_text().split()
    pw = {"internal_mw": float(tot[0]) * 1e3, "switching_mw": float(tot[1]) * 1e3,
          "leakage_uw": float(tot[2]) * 1e6, "total_mw": float(tot[3]) * 1e3,
          "clock_tree_mw": float(clk) * 1e3, "nets": int(ann[1]), "nets_annotated": int(ann[3])}
    return job, gls, pw, (ops, cyc)


# ------------------------------------------------------------------ layout parsing
def layer_widths(tlef):
    w, layer, routing = {}, None, False
    for line in tlef.read_text().splitlines():
        t = line.split("#")[0].split()
        if not t:
            continue
        if t[0] == "LAYER":
            layer, routing = t[1], False
        elif t[0] == "TYPE" and layer:
            routing = t[1] == "ROUTING"
        elif t[0] == "WIDTH" and len(t) == 3 and t[2] == ";" and routing and layer and layer not in w:
            w[layer] = float(t[1])
        elif t[0] == "END" and len(t) > 1 and t[1] == layer:
            layer = None
    return w


def metal_area(def_file, widths):
    """Routed wire length and area per layer for signal and clock nets."""
    txt = def_file.read_text()
    dbu = float(re.search(r"UNITS DISTANCE MICRONS (\d+)", txt).group(1))
    nets = txt[txt.index("\nNETS "):txt.index("END NETS")]
    res = {"signal": Counter(), "clock": Counter()}
    for net in nets.split("\n    - ")[1:]:
        kind = "clock" if "+ USE CLOCK" in net else "signal"
        for seg in re.split(r"\+ ROUTED|\bNEW\b", net)[1:]:
            seg = seg.split("RECT")[0].split("+ USE")[0]
            m = re.match(r"\s*(\S+)", seg)
            if not m or m.group(1) not in widths:
                continue
            layer = m.group(1)
            pts, x, y = [], None, None
            for px, py in re.findall(r"\(\s*(\S+)\s+(\S+)(?:\s+\S+)?\s*\)", seg):
                x = x if px == "*" else float(px)
                y = y if py == "*" else float(py)
                pts.append((x, y))
            length = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:])) / dbu
            res[kind][layer] += length
    out = {}
    for kind, c in res.items():
        out[kind] = {"length_um": round(sum(c.values()), 1),
                     "area_um2": round(sum(l * widths[ly] for ly, l in c.items()), 2),
                     "by_layer_um2": {ly: round(l * widths[ly], 2) for ly, l in sorted(c.items()) if l > 0}}
    return out


def congestion(grt_log):
    txt = grt_log.read_text()
    blk = txt[txt.rindex("Final congestion report"):]
    layers = {}
    for ly, res, dem, use, oh, ov, ot in re.findall(
            r"^(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", blk, re.M):
        layers[ly] = {"usage_pct": float(use), "overflow": int(ot)}
    total = layers.pop("Total")
    busiest = max(layers.items(), key=lambda kv: kv[1]["usage_pct"])
    return {"total_usage_pct": total["usage_pct"], "total_overflow": total["overflow"],
            "busiest_layer": busiest[0], "busiest_usage_pct": busiest[1]["usage_pct"],
            "by_layer_pct": {k: v["usage_pct"] for k, v in layers.items() if v["usage_pct"] > 0}}


def critical_path(rpt):
    txt = rpt.read_text()
    blk = txt[txt.index("report_checks -path_delay max"):]
    blk = blk[:blk.index("data arrival time")]
    start = re.search(r"Startpoint: (\S+)", blk).group(1)
    end = re.search(r"Endpoint: (\S+)", blk).group(1)
    arrival = float(re.findall(r"([\d.]+)\s+[\^v] \S+/\S+ \(\S+\)", blk)[-1])
    # output pins carry a fanout count at the start of the line
    outs = re.findall(r"^\s+\d+\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s+[\^v] (\S+)/(\S+) \((\S+)\)", blk, re.M)
    data = [(float(d), inst, cell) for d, _, inst, _, cell in outs
            if not inst.startswith(("clkbuf", "clkinv", "clkload"))]
    launch = data[0]                      # clock-to-Q of the launching flip-flop
    logic = data[1:]
    kinds = Counter(re.sub(r"_X\d+$|_\d+$", "", c.split("__")[-1]) for _, _, c in logic)
    return {"start": start, "end": end, "arrival_ns": arrival, "clk_to_q_ns": launch[0],
            "logic_depth": len(logic), "logic_delay_ns": round(sum(d for d, _, _ in logic), 3),
            "cell_mix": dict(kinds.most_common(6))}


# ------------------------------------------------------------------ per run
def collect(pdk, name, gls, pw, window):
    run = ROOT / f"build/orfs/{pdk}/{name}"
    base_r = run / f"reports/{pdk}/{name}/base"
    base_l = run / f"logs/{pdk}/{name}/base"
    base_res = run / f"results/{pdk}/{name}/base"
    m = json.loads((run / "metrics.json").read_text())
    T = PDKS[pdk]
    g = lambda k, d=0.0: m.get(k, d)
    widths = layer_widths(ORFS / "flow/platforms" / pdk / PLAT[pdk]["tlef"])
    ops, cyc = window
    cyc_per_op = cyc / ops
    r = {
        "area_um2": {"synth": g("synth__design__instance__area"),
                     "placed": g("detailedplace__design__instance__area"),
                     "cts": g("cts__design__instance__area"),
                     "routed": g("finish__design__instance__area"),
                     "core": g("finish__design__core__area")},
        "utilization_pct": round(100 * g("finish__design__instance__utilization"), 1),
        "timing": {stage: {"setup_wns": g(f"{k}__timing__setup__ws"), "setup_tns": g(f"{k}__timing__setup__tns"),
                           "hold_wns": g(f"{k}__timing__hold__ws"), "hold_tns": g(f"{k}__timing__hold__tns"),
                           "fmax_mhz": round(g(f"{k}__timing__fmax") / 1e6, 1)}
                   for stage, k in (("placed", "detailedplace"), ("cts", "cts"), ("routed", "finish"))},
        "cts": {"setup_skew_ps": round(1000 * g("finish__clock__skew__setup"), 1),
                "hold_skew_ps": round(1000 * g("finish__clock__skew__hold"), 1),
                "clock_buffers": int(g("finish__design__instance__count__class:clock_buffer")),
                "clock_inverters": int(g("finish__design__instance__count__class:clock_inverter")),
                "clock_cell_area_um2": round(g("finish__design__instance__area__class:clock_buffer")
                                             + g("finish__design__instance__area__class:clock_inverter"), 2),
                "timing_repair_buffers": int(g("finish__design__instance__count__class:timing_repair_buffer")),
                "timing_repair_area_um2": round(g("finish__design__instance__area__class:timing_repair_buffer"), 2),
                "hold_buffers": int(g("cts__design__instance__count__hold_buffer"))},
        "routing": {"wirelength_um": g("detailedroute__route__wirelength"), "vias": g("detailedroute__route__vias"),
                    "drc_errors": g("detailedroute__route__drc_errors")},
        "congestion": congestion(base_l / "5_1_grt.log"),
        "metal": metal_area(base_res / "6_final.def", widths),
        "critical_path": critical_path(base_r / "6_finish.rpt"),
        "gate_level_sim": gls,
        "power": {k: round(v, 6 if k == "leakage_uw" else 4) if isinstance(v, float) else v for k, v in pw.items()},
        "power_workload": {"ops": ops, "cycles": cyc, "cycles_per_op": round(cyc_per_op, 2)},
        "clock_ns": T,
    }
    # energy per operation at the PDK's clock target: P x T x cycles/op
    r["energy_pj_per_op"] = round(pw["total_mw"] * T * cyc_per_op, 2)
    return (pdk, name), r


def main():
    for p in PDKS:
        for i in (None, 0, 1):
            cell_models(p, i)
    jobs = [(p, n) for p in PDKS for n in UNITS]
    with ThreadPoolExecutor(max_workers=int(os.environ.get("JOBS", "6"))) as ex:
        sims = {j: (g, pw, w) for j, g, pw, w in ex.map(gls_power, jobs)}
    bad = [f"{p}/{n}: {sims[(p, n)][0]}" for p, n in jobs if sims[(p, n)][1] is None]
    if bad:
        sys.exit("gate-level simulation failed:\n" + "\n".join(bad))
    res = dict(collect(p, n, *sims[(p, n)]) for p, n in jobs)
    out = {p: {n: res[(p, n)] for n in UNITS} for p in PDKS}
    (ROOT / "results/signoff.json").write_text(json.dumps(out, indent=2))

    L = []
    for p in PDKS:
        d = out[p]
        L += [f"## {p} (clock target {PDKS[p]} ns)", "",
              "### Area by stage (standard-cell µm²) and timing after routing", "",
              "| unit | synth | placed | CTS | routed | util % | setup WNS (ns) | setup TNS (ns) | hold WNS (ns) | Fmax placed → routed (MHz) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for n, r in d.items():
            a, t = r["area_um2"], r["timing"]
            L.append(f"| {n} | {a['synth']:.1f} | {a['placed']:.1f} | {a['cts']:.1f} | {a['routed']:.1f} | "
                     f"{r['utilization_pct']} | {t['routed']['setup_wns']:+.3f} | {t['routed']['setup_tns']:.3f} | "
                     f"{t['routed']['hold_wns']:+.3f} | {t['placed']['fmax_mhz']} → {t['routed']['fmax_mhz']} |")
        L += ["", "### Clock tree, routing and congestion", "",
              "| unit | skew (ps) | clk bufs+invs | clk cell area (µm²) | repair bufs | wirelength (µm) | vias | "
              "GR usage % | busiest layer | overflow | DRC |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|"]
        for n, r in d.items():
            c, ro, g = r["cts"], r["routing"], r["congestion"]
            L.append(f"| {n} | {c['setup_skew_ps']} | {c['clock_buffers']}+{c['clock_inverters']} | "
                     f"{c['clock_cell_area_um2']} | {c['timing_repair_buffers']} | {ro['wirelength_um']:.0f} | "
                     f"{ro['vias']:.0f} | {g['total_usage_pct']} | {g['busiest_layer']} {g['busiest_usage_pct']}% | "
                     f"{g['total_overflow']} | {ro['drc_errors']:.0f} |")
        L += ["", "### Routed metal area (wire length × drawn width, from the final DEF)", "",
              "| unit | signal wire (µm) | signal metal (µm²) | signal metal / cell area | clock wire (µm) | clock metal (µm²) | signal metal by layer (µm²) |",
              "|---|---:|---:|---:|---:|---:|---|"]
        for n, r in d.items():
            s, ck = r["metal"]["signal"], r["metal"]["clock"]
            bl = ", ".join(f"{k} {v:.0f}" for k, v in s["by_layer_um2"].items())
            L.append(f"| {n} | {s['length_um']:.0f} | {s['area_um2']:.1f} | "
                     f"{s['area_um2'] / r['area_um2']['routed']:.2f} | {ck['length_um']:.0f} | {ck['area_um2']:.1f} | {bl} |")
        L += ["", "### Power (simulation-annotated) and energy per operation", "",
              "| unit | internal (mW) | switching (mW) | leakage (µW) | total (mW) | clock tree (mW) | nets annotated | cycles/op | energy/op (pJ) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for n, r in d.items():
            pw = r["power"]
            L.append(f"| {n} | {pw['internal_mw']:.3f} | {pw['switching_mw']:.3f} | {pw['leakage_uw']:.4g} | "
                     f"{pw['total_mw']:.3f} | {pw['clock_tree_mw']:.3f} | {pw['nets_annotated']}/{pw['nets']} | "
                     f"{r['power_workload']['cycles_per_op']} | {r['energy_pj_per_op']} |")
        L += ["", "### Gate-level simulation of the routed netlist (tb_unit, zero delay)", "",
              "| unit | flip-flops start at X | all start at 0 | all start at 1 | note |", "|---|---|---|---|---|"]
        for n, r in d.items():
            g = r["gate_level_sim"]
            cell = lambda k: f"{g[k]['result']} ({g[k]['checks']} checks" + (f", {g[k]['errors']} errors)" if g[k]['errors'] else ")")
            note = ""
            if g["x"]["result"] != "PASS" and g["0"]["result"] == "PASS" and g["1"]["result"] == "PASS":
                note = "X-pessimism only: passes with any defined power-up state (" + g["x"].get("first_failure", "") + ")"
            L.append(f"| {n} | {cell('x')} | {cell('0')} | {cell('1')} | {note} |")
        L += ["", "### Critical path (after routing)", "",
              "| unit | start → end | logic depth | clk→Q (ns) | logic (ns) | arrival (ns) | main cells on path |",
              "|---|---|---:|---:|---:|---:|---|"]
        for n, r in d.items():
            cp = r["critical_path"]
            mix = ", ".join(f"{k}×{v}" for k, v in cp["cell_mix"].items())
            L.append(f"| {n} | `{cp['start']}` → `{cp['end']}` | {cp['logic_depth']} | {cp['clk_to_q_ns']} | "
                     f"{cp['logic_delay_ns']} | {cp['arrival_ns']} | {mix} |")
        L.append("")
    (ROOT / "results/signoff.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
