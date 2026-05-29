"""Fixed measurement harness. Runs target.py under powermetrics + /usr/bin/time -l,
parses results, returns one JSON line on stdout.

The agent does NOT modify this file. Energy measurement uses sudo powermetrics;
see README for sudoers setup.

Tier 2: subtracts idle baseline from total joules.
Tier 3: runs N times, returns median + run_quality flag.
"""

import json
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

N_REPEATS = 3
VARIANCE_TOLERANCE = 0.10  # 10% — energy is noisier than wall-clock
IDLE_BASELINE_SECONDS = 5
POWERMETRICS_INTERVAL_MS = 100


def run_powermetrics_for(seconds):
    """Run powermetrics for ~`seconds`, return list of combined-power samples in watts."""
    n_samples = max(2, int(seconds * 1000 / POWERMETRICS_INTERVAL_MS))
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as f:
        log_path = f.name
    try:
        subprocess.run(
            [
                "sudo", "powermetrics",
                "--samplers", "cpu_power",
                "-i", str(POWERMETRICS_INTERVAL_MS),
                "-n", str(n_samples),
                "-o", log_path,
            ],
            check=True,
            capture_output=True,
        )
        with open(log_path) as f:
            text = f.read()
        watts = []
        for m in re.finditer(r"Combined Power \(CPU \+ GPU \+ ANE\): (\d+) mW", text):
            watts.append(int(m.group(1)) / 1000.0)
        return watts
    finally:
        Path(log_path).unlink(missing_ok=True)


def measure_idle():
    """Return average idle power in watts."""
    watts = run_powermetrics_for(IDLE_BASELINE_SECONDS)
    if not watts:
        return 0.0
    return statistics.median(watts)


def run_target_once(target_path):
    """Run target.py once, with powermetrics in parallel and /usr/bin/time -l wrapping it.
    Returns a dict of metrics, or None on crash."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".pm", delete=False) as f:
        pm_log = f.name
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".time", delete=False) as f:
        time_log = f.name
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".out", delete=False) as f:
        target_out = f.name

    try:
        # Start powermetrics in background. We don't know how long target takes,
        # so we let powermetrics run with a high sample count and kill it after.
        pm_proc = subprocess.Popen(
            [
                "sudo", "powermetrics",
                "--samplers", "cpu_power",
                "-i", str(POWERMETRICS_INTERVAL_MS),
                "-n", "100000",  # large, we kill it
                "-o", pm_log,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Tiny delay so powermetrics has started a sample window.
        time.sleep(0.3)

        # Run target.py under /usr/bin/time -l. -l writes resource usage to stderr.
        wall_start = time.perf_counter()
        result = subprocess.run(
            ["/usr/bin/time", "-l", sys.executable, target_path],
            stdout=open(target_out, "w"),
            stderr=open(time_log, "w"),
        )
        wall_clock = time.perf_counter() - wall_start

        # Stop powermetrics. sudo kill needed since we started it with sudo.
        subprocess.run(["sudo", "kill", str(pm_proc.pid)], capture_output=True)
        try:
            pm_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            subprocess.run(["sudo", "kill", "-9", str(pm_proc.pid)], capture_output=True)

        if result.returncode != 0:
            with open(time_log) as f:
                err = f.read()
            return {"error": f"target crashed (rc={result.returncode}): {err[-500:]}"}

        # Parse powermetrics log: sum (power * interval) over samples.
        with open(pm_log) as f:
            pm_text = f.read()
        watts = [int(m.group(1)) / 1000.0 for m in
                 re.finditer(r"Combined Power \(CPU \+ GPU \+ ANE\): (\d+) mW", pm_text)]
        interval_s = POWERMETRICS_INTERVAL_MS / 1000.0
        # Trim to roughly the target's wall-clock window.
        n_keep = max(1, int(wall_clock / interval_s))
        watts = watts[:n_keep] if len(watts) >= n_keep else watts
        joules = sum(w * interval_s for w in watts)

        # Parse /usr/bin/time -l output.
        with open(time_log) as f:
            time_text = f.read()

        def grab(pattern, cast=float, default=0):
            m = re.search(pattern, time_text)
            return cast(m.group(1)) if m else default

        user_time = grab(r"(\d+\.\d+) user")
        sys_time = grab(r"(\d+\.\d+) sys")
        instructions = grab(r"(\d+)\s+instructions retired", int)
        cycles = grab(r"(\d+)\s+cycles elapsed", int)
        max_rss = grab(r"(\d+)\s+maximum resident set size", int)
        peak_footprint = grab(r"(\d+)\s+peak memory footprint", int)
        page_faults = grab(r"(\d+)\s+page faults", int)
        ctx_inv = grab(r"(\d+)\s+involuntary context switches", int)
        ctx_vol = grab(r"(\d+)\s+voluntary context switches", int)

        return {
            "joules": joules,
            "wall_clock_s": wall_clock,
            "user_time_s": user_time,
            "sys_time_s": sys_time,
            "instructions": instructions,
            "cycles": cycles,
            "ipc": (instructions / cycles) if cycles else 0,
            "max_rss_mb": max_rss / 1024 / 1024,
            "peak_footprint_mb": peak_footprint / 1024 / 1024,
            "page_faults": page_faults,
            "ctx_switches_involuntary": ctx_inv,
            "ctx_switches_voluntary": ctx_vol,
        }
    finally:
        for p in (pm_log, time_log, target_out):
            Path(p).unlink(missing_ok=True)


def measure(target_path):
    idle_w = measure_idle()
    runs = []
    for _ in range(N_REPEATS):
        r = run_target_once(target_path)
        if r is None or "error" in r:
            return {"error": (r or {}).get("error", "unknown"), "idle_watts": idle_w}
        runs.append(r)

    joules_list = [r["joules"] for r in runs]
    median_joules = statistics.median(joules_list)
    spread = (max(joules_list) - min(joules_list)) / median_joules if median_joules else 1.0
    quality = "clean" if spread <= VARIANCE_TOLERANCE else "noisy"

    def med(key):
        return statistics.median([r[key] for r in runs])

    out = {
        "joules": median_joules,
        "joules_above_idle": median_joules - idle_w * med("wall_clock_s"),
        "idle_watts": idle_w,
        "wall_clock_s": med("wall_clock_s"),
        "user_time_s": med("user_time_s"),
        "sys_time_s": med("sys_time_s"),
        "instructions": int(med("instructions")),
        "cycles": int(med("cycles")),
        "ipc": med("ipc"),
        "max_rss_mb": med("max_rss_mb"),
        "peak_footprint_mb": med("peak_footprint_mb"),
        "page_faults": int(med("page_faults")),
        "ctx_switches_involuntary": int(med("ctx_switches_involuntary")),
        "ctx_switches_voluntary": int(med("ctx_switches_voluntary")),
        "n_repeats": N_REPEATS,
        "joules_spread": spread,
        "run_quality": quality,
    }
    return out


def main():
    if len(sys.argv) != 2:
        print("usage: python3 measure.py target.py", file=sys.stderr)
        sys.exit(2)
    target = sys.argv[1]
    if not Path(target).exists():
        print(f"target not found: {target}", file=sys.stderr)
        sys.exit(2)
    result = measure(target)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
