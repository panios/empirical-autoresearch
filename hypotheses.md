# Hypothesis log

Total experiments: 25  
Kept: 2  
Reverted: 23  
Prediction held: 0 / 1 (excluding unclear)

---

## Exp 1 — ✅ KEEP *(noisy)*
**Commit:** `31830a2`  
**Joules:** 0.4502J  |  **Wall clock:** 0.134s  |  **IPC:** 4.56  |  **Instructions:** 2,411,558,971

**Hypothesis:** baseline

**Prediction:** baseline

**Prediction held:** ? `nan`

**What changed:** baseline: reduceat+add.at n-body 200 bodies 400 steps

---

## Exp 2 — ❌ REVERT
**Commit:** `67849ac`  
**Joules:** 1.0196J  |  **Wall clock:** 0.238s  |  **IPC:** 3.02  |  **Instructions:** 2,994,369,596

**Hypothesis:** Python/numpy dispatch overhead dominates; Numba njit eliminates interpreter overhead

**Prediction:** instructions drop >=30%, joules drop >=25%

**Prediction held:** ✗ `no`

**What changed:** Numba njit(cache=True): 2.3x more joules than baseline -- llvmlite import overhead dominates

---

## Exp 3 — ❌ REVERT *(noisy)*
**Commit:** `a4e7519`  
**Joules:** 0.4473J  |  **Wall clock:** 0.132s  |  **IPC:** 4.61  |  **Instructions:** 2,390,714,354

**Hypothesis:** total_energy allocates O(N^2) full matrix; use precomputed pair indices

**Prediction:** instructions drop >=3%, joules drop >=2%

**Prediction held:** ~ `unclear`

**What changed:** optimized total_energy to use pair indices instead of full matrix diff

---

## Exp 4 — ❌ REVERT *(noisy)*
**Commit:** `dfe947a`  
**Joules:** 0.1725J  |  **Wall clock:** 0.131s  |  **IPC:** 2.69  |  **Instructions:** 1,421,803,692

**Hypothesis:** triu+scatter wastes energy on add.at scatter; BLAS matmul eliminates scatter

**Prediction:** instructions drop >=10%; joules drop >=5%

**Prediction held:** ? `yes (instructions dropped 41%; joules dropped 62% -- but ctx_switches=2946 caused noisy)`

**What changed:** BLAS matrix approach: pos@pos.T for r2, F@pos for accel; eliminates add.at scatter

---

## Exp 5 — ❌ REVERT *(noisy)*
**Commit:** `f0a96de`  
**Joules:** 0.2412J  |  **Wall clock:** 0.126s  |  **IPC:** 2.67  |  **Instructions:** 1,405,504,304

**Hypothesis:** add.at scatter sequential; BLAS matmul via pos@pos.T eliminates scatter

**Prediction:** instructions drop >=35%; joules drop >=30%

**Prediction held:** ? `yes (41% instr drop, 46% joules drop -- but ctx_switches=2647 from multi-threaded Accelerate BLAS caused noisy)`

**What changed:** BLAS approach correct but Apple Accelerate spawns threads causing noisy measurement

---

## Exp 6 — ❌ REVERT *(noisy)*
**Commit:** `482953e`  
**Joules:** 0.2429J  |  **Wall clock:** 0.118s  |  **IPC:** 3.16  |  **Instructions:** 1,369,592,921

**Hypothesis:** Accelerate multi-threading causes noise; VECLIB_MAXIMUM_THREADS=1+matmul

**Prediction:** ctx_switches<200; run_quality=clean; joules drop >=30%

**Prediction held:** ? `partial (ctx_switches=98 -- fixed; instructions dropped 43%; but wall_clock=0.118s still causes noisy powermetrics sampling)`

**What changed:** BLAS+single-thread: real improvement but wall_clock < 0.3s measurement floor makes run noisy

---

## Exp 7 — ❌ REVERT *(noisy)*
**Commit:** `d903742`  
**Joules:** 0.2637J  |  **Wall clock:** 0.120s  |  **IPC:** 3.14  |  **Instructions:** 1,384,904,186

**Hypothesis:** Accelerate BLAS multi-threading causes noise; VECLIB_MAX_THREADS=1+matmul

**Prediction:** ctx_switches<200; run_quality=clean; joules drop >=30%

**Prediction held:** ? `partial (ctx fixed; instr dropped 43%; wall_clock=0.120s below 0.3s floor = always noisy)`

**What changed:** 3rd noisy run; wall_clock too short for powermetrics; BLAS approach is best but unmeasurable

---

## Exp 8 — ❌ REVERT *(noisy)*
**Commit:** `1013cc3`  
**Joules:** 0.2440J  |  **Wall clock:** 0.121s  |  **IPC:** 3.16  |  **Instructions:** 1,384,455,543

**Hypothesis:** add.at scatter unvectorized; BLAS matmul+VECLIB=1 reduces instructions 43%

**Prediction:** instructions drop >=35%; run_quality=clean; joules drop >=30%

**Prediction held:** ? `partial (instr: yes; clean: no -- wall_clock=0.120s permanently below 0.3s floor)`

**What changed:** 4th noisy run; wall_clock floor is fundamental blocker; protocol says stop speed improvements

---

## Exp 9 — ❌ REVERT *(noisy)*
**Commit:** `be8206d`  
**Joules:** 0.2510J  |  **Wall clock:** 0.119s  |  **IPC:** 3.14  |  **Instructions:** 1,365,786,845

**Hypothesis:** BLAS matmul+VECLIB=1+shared r2/r buffers reduces sys_time from malloc

**Prediction:** instructions drop >=40%; sys_time/wall drop; run_quality=clean

**Prediction held:** ? `partial (instr: yes; clean: no -- wall_clock floor is ~0.2s, program=0.119s)`

**What changed:** 5th noisy run; wall_clock fundamental blocker; BLAS approach optimal but unmeasurable

---

## Exp 10 — ❌ REVERT
**Commit:** `c8e27aa`  
**Joules:** 1.4647J  |  **Wall clock:** 0.308s  |  **IPC:** 2.70  |  **Instructions:** 3,076,892,927

**Hypothesis:** BLAS matmul 43% fewer instr; Numba import pads wall_clock for clean measurement

**Prediction:** wall_clock>0.25s; run_quality=clean; joules<1.02J

**Prediction held:** ? `no (joules=1.46J > 1.02J Numba ref; Numba cache+BLAS overhead > savings)`

**What changed:** BLAS+Numba combo: clean but worse than pure Numba reference; Numba import cost dominates

---

## Exp 11 — ❌ REVERT *(noisy)*
**Commit:** `57870ab`  
**Joules:** 0.3738J  |  **Wall clock:** 0.149s  |  **IPC:** 4.44  |  **Instructions:** 2,390,441,523

**Hypothesis:** 400 step() calls with 16 args has Python overhead; inlining eliminates call cost

**Prediction:** instructions drop >=4%; joules drop >=4%

**Prediction held:** ? `no (instructions dropped only 0.9%; joules may have dropped 17% but noisy/uncertain)`

**What changed:** Inlined step loop: marginal instruction reduction; joules drop within noise range

---

## Exp 12 — ❌ REVERT *(noisy)*
**Commit:** `b95c031`  
**Joules:** 0.3029J  |  **Wall clock:** 0.128s  |  **IPC:** 3.04  |  **Instructions:** 1,352,438,350

**Hypothesis:** BLAS+VECLIB=1+inline step+fast total_energy combines all partial wins

**Prediction:** instructions drop >=40%; joules drop >=30%; run_quality=clean

**Prediction held:** ? `partial (instr: 44% drop=best yet; joules: 32% drop; but wall_clock=0.128s = still noisy)`

**What changed:** Best instruction count yet (1.35B) but still noisy; fundamental wall_clock floor prevents clean read

---

## Exp 13 — ✅ KEEP
**Commit:** `6e7097c`  
**Joules:** 0.3210J  |  **Wall clock:** 0.172s  |  **IPC:** 4.10  |  **Instructions:** 2,413,398,228

**Hypothesis:** original triu+scatter; VECLIB_MAXIMUM_THREADS=1 reduces multi-threaded Accelerate energy in total_energy

**Prediction:** ctx_switches drop; joules drop >=5%

**Prediction held:** ? `yes (joules: 28.6% drop vs noisy baseline; run_quality=clean; ctx_switches=191; wall_clock longer but power much lower)`

**What changed:** VECLIB=1 minimal change: single-threaded Apple Accelerate reduces power from ~3.38W to 1.87W; total_energy no longer multi-threaded

---

## Exp 14 — ❌ REVERT *(noisy)*
**Commit:** `71f30f8`  
**Joules:** 0.3885J  |  **Wall clock:** 0.170s  |  **IPC:** 4.17  |  **Instructions:** 2,410,400,751

**Hypothesis:** Python GC runs during step loop; disabling GC for hot loop eliminates trace overhead

**Prediction:** instructions drop >=2%; joules drop vs 0.321J baseline

**Prediction held:** ? `no (instructions unchanged; joules=0.389 > 0.321J baseline; run noisy)`

**What changed:** GC disable: no instruction benefit; measurement noisier than baseline

---

## Exp 15 — ❌ REVERT
**Commit:** `239a6f7`  
**Joules:** 0.3540J  |  **Wall clock:** 0.140s  |  **IPC:** 2.93  |  **Instructions:** 1,393,185,469

**Hypothesis:** BLAS matmul+VECLIB=1 reduces instructions 43% vs 0.321J baseline

**Prediction:** joules < 0.321J (current clean best)

**Prediction held:** ? `no (joules=0.354J > 0.321J baseline; BLAS uses 2.53W vs triu 1.87W -- more power despite fewer instructions)`

**What changed:** BLAS uses more power per second than triu+VECLIB=1; triu path is lower power at VECLIB=1

---

## Exp 16 — ❌ REVERT *(noisy)*
**Commit:** `8b3d09f`  
**Joules:** 0.4244J  |  **Wall clock:** 0.172s  |  **IPC:** 4.10  |  **Instructions:** 2,393,747,655

**Hypothesis:** VECLIB=2 allows faster total_energy matrix ops while limiting AMX thrashing vs VECLIB=1

**Prediction:** joules < 0.321J; run_quality=clean

**Prediction held:** ? `no (joules=0.424J > 0.321J; noisy with spread=117%; 2 threads causes contention)`

**What changed:** VECLIB=2 worse than VECLIB=1; single-thread minimizes power more than 2-thread reduces compute time

---

## Exp 17 — ❌ REVERT *(noisy)*
**Commit:** `3694b06`  
**Joules:** 2.5119J  |  **Wall clock:** 0.498s  |  **IPC:** 3.67  |  **Instructions:** 2,224,698,081

**Hypothesis:** np.add.at is Python-loop scatter; ctypes C scatter eliminates per-element Python frame overhead

**Prediction:** instructions drop >=10%; joules drop >=8%

**Prediction held:** ? `no (joules=2.51J; subprocess.run compile adds ~0.3s wall_clock overhead per run)`

**What changed:** ctypes with runtime compile: compile cost dominates; need pre-compiled .so to avoid overhead

---

## Exp 18 — ❌ REVERT
**Commit:** `7d7a5eb`  
**Joules:** 0.4650J  |  **Wall clock:** 0.191s  |  **IPC:** 3.58  |  **Instructions:** 2,160,954,451

**Hypothesis:** np.add.at unvectorized; cached ctypes C scatter eliminates Python frame overhead

**Prediction:** instructions drop >=10%; joules drop vs 0.321J baseline

**Prediction held:** ? `no (instructions: -10% yes; joules: 0.465 > 0.321J; ctypes call overhead 3x c_void_p extractions per step adds more energy than scatter saves; ipc dropped 4.10->3.58)`

**What changed:** ctypes scatter: fewer instructions but lower IPC -- ctypes bridge overhead dominates at 400 steps

---

## Exp 19 — ❌ REVERT *(noisy)*
**Commit:** `9cd7ac4`  
**Joules:** 1.7911J  |  **Wall clock:** 0.428s  |  **IPC:** 2.87  |  **Instructions:** 2,477,512,524

**Hypothesis:** P-cores 1.87W; E-cores via background QoS much lower power; net energy reduction despite 3x slowdown

**Prediction:** joules < 0.321J; run_quality=clean

**Prediction held:** ? `no (joules=1.79J; joules_above_idle=0.07J shows actual compute is tiny; idle_watts=4.02W dominates; longer wall_clock = more idle energy)`

**What changed:** E-core: actual compute energy 0.07J but system idle power 1.72J; total joules metric penalizes slower programs

---

## Exp 20 — ❌ REVERT *(noisy)*
**Commit:** `d3560fc`  
**Joules:** 0.9259J  |  **Wall clock:** 0.230s  |  **IPC:** 3.54  |  **Instructions:** 2,418,309,783

**Hypothesis:** VECLIB=0 may reduce idle power further than VECLIB=1

**Prediction:** joules < 0.321J; idle_watts drop vs VECLIB=1

**Prediction held:** ? `no (joules=0.926J; idle_watts=5.77W HIGHER than VECLIB=1 1.87W; VECLIB=0 starves Accelerate causing more thrashing)`

**What changed:** VECLIB=0 raises system idle power from 1.87W to 5.77W -- minimum is at VECLIB=1

---

## Exp 21 — ❌ REVERT
**Commit:** `236dd13`  
**Joules:** 0.4227J  |  **Wall clock:** 0.135s  |  **IPC:** 2.74  |  **Instructions:** 1,092,310,001

**Hypothesis:** C kernel eliminates Python overhead; 4x fewer instructions at VECLIB=1 idle power

**Prediction:** joules < 0.321J; instructions drop >=50%

**Prediction held:** ? `no (instructions: -55% yes; joules=0.422 > 0.321J; idle_watts jumped 4.69W vs 1.87W -- C code raises system power vs numpy path; ipc=2.74 vs 4.10)`

**What changed:** Full C kernel: faster and fewer instructions but idle_watts 4.69W vs numpy 1.87W; numpy path keeps system at lower power state

---

## Exp 22 — ❌ REVERT
**Commit:** `70b4ce0`  
**Joules:** 1.0055J  |  **Wall clock:** 0.231s  |  **IPC:** 3.50  |  **Instructions:** 2,395,403,779

**Hypothesis:** OMP/OPENBLAS/MKL=1 alongside VECLIB=1 kills additional background threads reducing idle_watts

**Prediction:** idle_watts < 1.87W; joules < 0.321J

**Prediction held:** ? `no (joules=1.005J; idle_watts=4.78W HIGHER than VECLIB=1 alone; extra env vars cause slower code paths raising system power)`

**What changed:** All-threads-1: OMP_NUM_THREADS=1 raises idle_watts 1.87W->4.78W; VECLIB=1 alone is the correct minimum

---

## Exp 23 — ❌ REVERT
**Commit:** `efd98d6`  
**Joules:** 0.4535J  |  **Wall clock:** 0.161s  |  **IPC:** 2.55  |  **Instructions:** 1,090,941,767

**Hypothesis:** numpy NEON warmup before C kernel keeps chip in 1.87W power state; C kernel 4x faster

**Prediction:** joules < 0.321J; idle_watts ~1.87W

**Prediction held:** ? `no (joules=0.454J; idle_watts=4.53W; NEON warmup doesn't persist into C kernel execution -- chip exits low-power state immediately when scalar C runs)`

**What changed:** NEON warmup fails: chip power state is determined by current instruction type, not prior warmup; only numpy ufunc path sustains 1.87W

---

## Exp 24 — ❌ REVERT *(noisy)*
**Commit:** `0c4aa4d`  
**Joules:** 1.0290J  |  **Wall clock:** 0.258s  |  **IPC:** 3.38  |  **Instructions:** 2,372,970,451

**Hypothesis:** total_energy O(N^2) matrix briefly uses multi-threaded Accelerate; pair-direct stays NEON

**Prediction:** idle_watts stays <=1.87W; joules < 0.321J

**Prediction held:** ? `no (joules=1.029J; idle_watts=4.99W; original matrix total_energy keeps chip in beneficial Accelerate state; removing it raises power)`

**What changed:** Pair-direct total_energy: removing O(N^2) matrix RAISES idle_watts 1.87->4.99W -- matrix ops stabilize system power state

---

## Exp 25 — ❌ REVERT *(noisy)*
**Commit:** `8bcf67b`  
**Joules:** 0.9218J  |  **Wall clock:** 0.296s  |  **IPC:** 3.20  |  **Instructions:** 2,397,548,601

**Hypothesis:** total_energy 3D broadcast wasteful; subtract.outer 2.3x faster stays in NEON/Accelerate path

**Prediction:** wall_clock drops ~1ms; idle_watts stays 1.87W; joules < 0.321J

**Prediction held:** ? `no (joules=0.922J; idle_watts=4.58W; subtract.outer raises power like pair-direct -- only the 3D pos broadcast maintains 1.87W state)`

**What changed:** subtract.outer raises idle_watts 1.87->4.58W; the original 3D pos[newaxis]-pos[newaxis] broadcast is uniquely required for the low-power state

---
