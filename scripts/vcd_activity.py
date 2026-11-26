#!/usr/bin/env python3
"""Per-bit switching activity from a VCD file.

Usage: vcd_activity.py <activity.vcd> <clock_period_ns> <out.tcl>

For every bit of every variable in the (single) design scope, computes
  activity = transitions per clock cycle
  duty     = fraction of time at logic 1
and writes them as a Tcl dict (name -> {activity duty}) for power_annotate.tcl.
Bus bits are named like the netlist registers, e.g. "h[17]".
"""
import sys

vcd, period, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
ids = {}          # vcd id -> list of bit names (MSB first)
state = {}        # bit name -> [value, last_change_time, toggles, time_high]
t = 0
t0 = None          # first timestamp (dumping starts mid-simulation)
in_defs = True

with open(vcd) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if in_defs:
            if line.startswith("$var"):
                p = line.split()
                width, vid, name = int(p[2]), p[3], p[4].lstrip("\\")   # escaped identifiers
                if width == 1:
                    bits = [name]
                else:
                    msb, lsb = (int(x) for x in p[5].strip("[]").split(":"))
                    step = -1 if msb >= lsb else 1
                    bits = [f"{name}[{i}]" for i in range(msb, lsb + step, step)]
                ids[vid] = bits
                for b in bits:
                    state[b] = [None, 0, 0, 0]
            elif line.startswith("$enddefinitions"):
                in_defs = False
            continue
        c = line[0]
        if c == "#":
            t = int(line[1:])
            if t0 is None:
                t0 = t
            continue
        if c in "$":
            continue
        if c == "b":
            val, vid = line[1:].split()
            bits = ids.get(vid)
            if bits is None:
                continue
            val = val.rjust(len(bits), "0" if val[0] in "01" else val[0])
            pairs = zip(bits, val[-len(bits):])
        else:
            bits = ids.get(line[1:])
            if bits is None:
                continue
            pairs = [(bits[0], c)]
        for b, v in pairs:
            s = state[b]
            if s[0] == "1":
                s[3] += t - s[1]
            if s[0] is not None and s[0] != v and s[0] in "01" and v in "01":
                s[2] += 1
            s[0], s[1] = v, t

t_end = t
for s in state.values():
    if s[0] == "1":
        s[3] += t_end - s[1]

# VCD timescale is 1 ps in xsim; period in ns
cycles = (t_end - t0) / (period * 1000.0)
with open(out, "w") as f:
    f.write("set act [dict create]\n")
    for b, (_, _, tog, hi) in state.items():
        f.write("dict set act {%s} {%.6f %.6f}\n" % (b, tog / cycles, hi / max(t_end - t0, 1)))
print(f"{len(state)} bits, {cycles:.0f} cycles -> {out}")
