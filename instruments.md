# instruments.md

Catalog of physical observables available on this Mac (Apple Silicon, macOS), organized by **the question each measurement answers**. The default dashboard from `measure.py` covers most questions. Use this when you need more.

Do not collect a signal because it exists. Collect it because a specific hypothesis requires it.

---

## Default dashboard (collected on every run by `measure.py`)

| Signal | What it answers |
|---|---|
| `joules` | Total energy spent. The optimization target. |
| `joules_above_idle` | Energy minus the steady idle baseline. Closer to "energy your code caused." |
| `wall_clock_s` | How long the run took, today, at the frequencies the chip happened to use. |
| `instructions_retired` | How many machine instructions the CPU completed. Independent of frequency. |
| `cycles_elapsed` | How many clock ticks. |
| `ipc` | instructions / cycles. Measures how efficiently the pipeline was utilized. |
| `peak_footprint_mb` | Peak memory in use during the run. |
| `page_faults` | Page faults — memory hierarchy events. |
| `ctx_switches_involuntary` | Times the scheduler preempted the process. High = noisy run or contention. |
| `sys_time_s` / `user_time_s` | Kernel vs user-mode CPU time. |
| `run_quality` | `clean` if multiple runs agreed within tolerance, else `noisy`. |

---

## Q: Is the workload CPU-bound or memory-bound?

**Read:** `ipc` (default dashboard).

- IPC > 3 → CPU-bound. The chip is feeding execution units fast. Hot loops, math-heavy code.
- IPC < 1 → memory-bound. The chip is stalling, waiting for data. Pointer chasing, large working sets.
- IPC 1–3 → mixed.

A change that lowers IPC while joules drops anyway = you reduced *amount* of work. A change that raises IPC = you made the existing work more efficient.

**Important caveat about absolute IPC on Apple Silicon:** the `instructions retired` counter from `/usr/bin/time -l` on M-series chips appears to count differently than on x86 — typical Python workloads report IPC in the 5–7 range. Do NOT form hypotheses based on the absolute value being high or low. Only relative changes between runs are meaningful. A drop in instructions retired from run A to run B is real; concluding "IPC of 6 means we're CPU-bound" is not.

---

## Q: Where is the time going — user code or kernel?

**Read:** `sys_time_s / wall_clock_s`.

- > 20% in sys time → your code is making heavy syscalls. File I/O, allocations hitting the kernel, sleeps. Often the biggest energy win on Python code is removing syscalls.
- < 5% in sys time → pure compute. Optimize the algorithm or data layout.

---

## Q: Is the program touching too much memory?

**Read:** `peak_footprint_mb` and `page_faults`.

- High `page_faults` → memory pressure, working set exceeds RAM, swapping. Catastrophic for energy.
- High `peak_footprint_mb` relative to working data size → unnecessary copies, intermediate allocations.

---

## Q: Was this run noisy?

**Read:** `ctx_switches_involuntary`, `run_quality`.

- High involuntary switches → other processes contended for CPU. Run is suspect.
- `run_quality == noisy` → measure.py's repeat-and-compare flagged inconsistency. Do not theorize from this data.

---

## Beyond the default dashboard (requires extra setup)

These are **not** collected by default. Ask the human if you want them.

### Q: Which functions burned the most CPU?

Tool: `python3 -m cProfile -o profile.out target.py`, then `python3 -c "import pstats; pstats.Stats('profile.out').sort_stats('tottime').print_stats(20)"`.

Cost: ~2x slowdown of the run, distorts energy measurement. Use as a diagnostic, not during a measured run.

### Q: Which lines allocate memory?

Tool: `python3 -X tracemalloc target.py`. Cost: heavy, distorts measurement.

### Q: Cache miss rates, branch mispredictions?

Tool: `xcrun xctrace record --template 'CPU Counters' --launch -- python3 target.py`. Cost: produces binary `.trace` bundle; parsing is non-trivial. Skip unless absolutely necessary.

### Q: Which syscalls and how many?

Tool: `sudo dtruss -c python3 target.py`. Cost: blocked for Apple-signed Python by SIP; use a Homebrew Python if needed.

### Q: Per-core / per-frequency residency?

Tool: full `powermetrics` output (already collected by `measure.py` but only `cpu_power` is summarized). The raw output has E-core vs P-core residency at each frequency state.

---

## Lessons from prior runs (Apple Silicon / numpy workloads)

These were discovered empirically and cost real experiment budget to learn. Read them before forming hypotheses.

### Scatter pattern: check index structure before choosing method

When accumulating a weighted sum into an output array (scatter-add), the right tool depends on the index array structure:

| Index array structure | Best method | Why |
|---|---|---|
| Sorted, contiguous segments (e.g. `triu_indices` `ii`) | `np.add.reduceat` | 15x faster than bincount — sums segments directly without random access |
| Unsorted or irregular (e.g. `triu_indices` `jj`) | `np.add.at` | Fastest available for non-contiguous scatter writes |
| Any | `np.bincount` | General-purpose but slower than reduceat for sorted inputs |

**Always inspect your index arrays before choosing.** `np.triu_indices(n, k=1)` returns `ii` sorted in contiguous blocks — body k appears n-1-k times consecutively. Precompute segment starts with `np.concatenate([[0], np.cumsum(np.arange(n-1, 1, -1))])` and use `reduceat`.

### float32 is not faster than float64 on Apple M-series for numpy workloads

Do not form hypotheses like "float32 halves bandwidth therefore joules will drop ≥15%." In practice, on M-series chips:
- numpy ufuncs dispatch through the same infrastructure regardless of dtype
- float32 arrays may cause implicit type promotion in accumulation operations, adding hidden cost
- Measured result across 3 separate experiments: float32 was either noisier or measurably worse than float64

**Only try float32 if you have a microbenchmark showing it is faster for your specific operation before running `measure.py`.**

### The measurement floor

`measure.py` uses powermetrics at 100ms intervals with 3 repeats. When `wall_clock_s < 0.3s`, each repeat gets only 1-3 samples — not enough to average out variance. Symptoms: repeated noisy runs even for unchanged code, `joules_spread > 0.15`. At this point the harness cannot distinguish a 10% energy difference from noise. Shift strategy: search for JIT libraries (Numba, Taichi) that reduce energy-per-instruction rather than wall time.

### Microbenchmark first

Before committing any change involving scatter, gather, or data layout, benchmark the candidate implementation in a throwaway script:
```bash
python3 -c "
import numpy as np, time
# ... setup ...
def time_it(fn, reps=2000):
    t = time.perf_counter()
    for _ in range(reps): fn()
    return (time.perf_counter()-t)*1000/reps
print(f'candidate: {time_it(candidate):.3f}ms')
print(f'current:   {time_it(current):.3f}ms')
"
```
If the microbenchmark shows no improvement, skip the experiment. This saves a full 3-minute `measure.py` run.

---

## Discipline

When you propose collecting a non-default signal, state in your hypothesis **what specific causal claim it would test that the default dashboard cannot**. If you can't name the claim, you don't need the signal.
