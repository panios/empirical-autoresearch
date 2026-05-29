# Hypothesis log

Total experiments: 16  
Kept: 8  
Reverted: 8  
Prediction held: 5 / 11 (excluding unclear)

---

## Exp 1 — ✅ KEEP
**Commit:** `0479429`  
**Joules:** 26.5410J  |  **Wall clock:** 3.962s  |  **IPC:** 6.22  |  **Instructions:** 98,539,087,171

**Hypothesis:** baseline: Python dict-based N-body O(N^2) loop

**Prediction:** baseline measurement

**Prediction held:** ? `nan`

**What changed:** original target.py

---

## Exp 2 — ✅ KEEP
**Commit:** `1fa19fa`  
**Joules:** 2.2928J  |  **Wall clock:** 0.405s  |  **IPC:** 5.20  |  **Instructions:** 8,556,368,009

**Hypothesis:** Python dict O(N^2) loop wastes 98B instructions; numpy vectorizes in C

**Prediction:** instructions drop >=80% joules drop >=60%

**Prediction held:** ✓ `yes`

**What changed:** replaced dicts+math.sqrt with numpy; vectorized pairwise force computation

---

## Exp 3 — ✅ KEEP
**Commit:** `1b1f03a`  
**Joules:** 1.8588J  |  **Wall clock:** 0.360s  |  **IPC:** 4.99  |  **Instructions:** 7,259,652,467

**Hypothesis:** repeated large temp allocs in step() drive overhead; pre-alloc buffers for 400 steps

**Prediction:** joules drop >=10%

**Prediction held:** ✓ `yes`

**What changed:** pre-allocated diff/r2/r/f_mag/f_vec/accel arrays reused via out= params

---

## Exp 4 — ✅ KEEP
**Commit:** `e5d73d5`  
**Joules:** 1.2443J  |  **Wall clock:** 0.242s  |  **IPC:** 3.79  |  **Instructions:** 3,810,349,653

**Hypothesis:** full N^2 pairs redundant; Newton 3rd law halves pairs via triu_indices

**Prediction:** instructions drop ~35-40% joules drop ~30%

**Prediction held:** ✓ `yes`

**What changed:** triu_indices + np.add.at scatter for F(i,j)=-F(j,i)

---

## Exp 5 — ✅ KEEP
**Commit:** `0f567d9`  
**Joules:** 1.2190J  |  **Wall clock:** 0.230s  |  **IPC:** 2.84  |  **Instructions:** 2,768,998,053

**Hypothesis:** np.add.at unbuffered; np.bincount vectorized scatter should cut scatter cost

**Prediction:** joules drop >=15%

**Prediction held:** ✗ `no`

**What changed:** replaced 6x np.add.at with 6x np.bincount; IPC dropped to 2.84

---

## Exp 6 — ❌ REVERT *(noisy)*
**Commit:** `48c554e`  
**Joules:** 1.0748J  |  **Wall clock:** 0.222s  |  **IPC:** 2.86  |  **Instructions:** 2,719,286,015

**Hypothesis:** float64 uses 2x bandwidth vs float32; halving traffic reduces joules 15%+

**Prediction:** joules drop >=15%

**Prediction held:** ~ `unclear`

**What changed:** switched to float32; reverted due to noisy run

---

## Exp 7 — ❌ REVERT
**Commit:** `56b4321`  
**Joules:** 1.3883J  |  **Wall clock:** 0.385s  |  **IPC:** 4.00  |  **Instructions:** 4,420,974,839

**Hypothesis:** scatter(bincount) 2x slower than dist; N^2 matrix+einsum eliminates scatter

**Prediction:** joules <=1.0J

**Prediction held:** ✗ `no`

**What changed:** full N^2 matrix + einsum; 2x compute outweighed scatter savings

---

## Exp 8 — ✅ KEEP
**Commit:** `f7dd233`  
**Joules:** 1.0415J  |  **Wall clock:** 0.227s  |  **IPC:** 2.77  |  **Instructions:** 2,517,889,870

**Hypothesis:** AoS pos[ii,c] creates temp copies; SoA px/py/pz makes reads contiguous

**Prediction:** joules drop >=10%

**Prediction held:** ✓ `yes`

**What changed:** split pos (n,3) into px/py/pz arrays; same for vel

---

## Exp 9 — ✅ KEEP
**Commit:** `4aaae0e`  
**Joules:** 1.0167J  |  **Wall clock:** 0.220s  |  **IPC:** 2.77  |  **Instructions:** 2,540,408,009

**Hypothesis:** fx/fy/fz alloc each step; pre-alloc pair buffers cuts allocation pressure

**Prediction:** joules drop >=8%

**Prediction held:** ✗ `no`

**What changed:** pre-alloc 9-buffer dict; marginal 2.4% improvement

---

## Exp 10 — ✅ KEEP
**Commit:** `cbe3d69`  
**Joules:** 0.2715J  |  **Wall clock:** 0.155s  |  **IPC:** 4.36  |  **Instructions:** 2,390,656,627

**Hypothesis:** bincount(ii) slow on sorted segments; reduceat sums contiguous blocks 15x faster

**Prediction:** joules drop ~58%

**Prediction held:** ✓ `yes`

**What changed:** replaced 3 bincount(ii) with reduceat+starts_ii; 73% actual drop

---

## Exp 11 — ❌ REVERT
**Commit:** `8dd68d9`  
**Joules:** 0.2877J  |  **Wall clock:** 0.156s  |  **IPC:** 4.35  |  **Instructions:** 2,387,000,000

**Hypothesis:** 400 fn calls to step() have Python overhead; inlining eliminates call cost

**Prediction:** joules drop >=5%

**Prediction held:** ✗ `no`

**What changed:** inlined step() body; marginally worse (0.29 vs 0.27J)

---

## Exp 12 — ❌ REVERT *(noisy)*
**Commit:** `5b6266c`  
**Joules:** 0.3647J  |  **Wall clock:** 0.158s  |  **IPC:** 4.32  |  **Instructions:** 2,401,000,000

**Hypothesis:** add.at(jj) non-contiguous; sort+reduceat for jj eliminates scatter

**Prediction:** joules drop >=8%

**Prediction held:** ~ `unclear`

**What changed:** double reduceat; noisy run

---

## Exp 13 — ❌ REVERT *(noisy)*
**Commit:** `6cd4461`  
**Joules:** 0.3504J  |  **Wall clock:** 0.162s  |  **IPC:** 4.32  |  **Instructions:** 2,410,000,000

**Hypothesis:** 9 temp allocs per step; pre-alloc all with out= should help

**Prediction:** joules drop >=5%

**Prediction held:** ~ `unclear`

**What changed:** pre-alloc all temps; noisy run

---

## Exp 14 — ❌ REVERT *(noisy)*
**Commit:** `7b5eae7`  
**Joules:** 0.3542J  |  **Wall clock:** 0.151s  |  **IPC:** 4.35  |  **Instructions:** 2,385,000,000

**Hypothesis:** total_energy uses O(N^2) matrix; pairs-based 5x faster

**Prediction:** joules drop ~0.7%

**Prediction held:** ~ `unclear`

**What changed:** pairs-based total_energy; noisy

---

## Exp 15 — ❌ REVERT
**Commit:** `af3a99e`  
**Joules:** 6.1829J  |  **Wall clock:** 0.453s  |  **IPC:** 4.38  |  **Instructions:** 2,410,000,000

**Hypothesis:** float32 pairs fit in L1; combined with reduceat halves bandwidth

**Prediction:** joules drop 40%

**Prediction held:** ✗ `no`

**What changed:** float32+reduceat; type promotion caused 6.2J regression

---

## Exp 16 — ❌ REVERT
**Commit:** `a7698f8`  
**Joules:** 0.3748J  |  **Wall clock:** 0.164s  |  **IPC:** 4.08  |  **Instructions:** 2,236,645,564

**Hypothesis:** consistent float32 avoids dtype promotion overhead

**Prediction:** joules drop 40%

**Prediction held:** ✗ `no`

**What changed:** all float32; WORSE (0.37J) — Apple M-series float32 no faster than float64

---
