# vivado_impl.tcl - out-of-context synthesis + place & route of one module.
# Usage: vivado -mode batch -source vivado_impl.tcl -tclargs <outdir> <period_ns> <top> [GENERIC=VALUE ...]

set outdir   [lindex $argv 0]
set period   [lindex $argv 1]
set top      [lindex $argv 2]
set generics [lrange $argv 3 end]
set part     xc7z020clg400-1
set root     [file normalize [file dirname [info script]]/..]

file mkdir $outdir
set_param general.maxThreads 2

read_verilog [list \
	$root/third_party/picorv32/picorv32.v \
	$root/rtl/pcpi_mul_booth.v \
	$root/rtl/pcpi_div_restoring.v \
	$root/rtl/core_top.v]

set gen_args {}
foreach g $generics { lappend gen_args -generic $g }

synth_design -top $top -part $part -mode out_of_context {*}$gen_args
create_clock -name clk -period $period [get_ports clk]

opt_design
place_design
phys_opt_design
route_design

report_utilization                -file $outdir/util.rpt
report_utilization -hierarchical  -file $outdir/util_hier.rpt
report_timing_summary -max_paths 5 -file $outdir/timing.rpt

set crit [get_timing_paths -max_paths 1 -setup]
set fh [open $outdir/summary.txt w]
puts $fh "period $period"
puts $fh "wns [get_property SLACK $crit]"
puts $fh "crit_start [get_property STARTPOINT_PIN $crit]"
puts $fh "crit_end [get_property ENDPOINT_PIN $crit]"
puts $fh "crit_levels [get_property LOGIC_LEVELS $crit]"
close $fh
