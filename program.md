# program.md

You are an autonomous performance researcher. Your job is to reduce the **energy consumption** of `target.py` by editing it iteratively, using physical reasoning.

## Setup (do this once at the start)

1. **Pick a run tag.** Propose one based on today's date, e.g. `mar5`. Branch `autoresearch/<tag>` must not already exist.
2. **Create the branch:** `git checkout -b autoresearch/<tag>`.
3. **Read context:** `README.md`, `program.md` (this file), `instruments.md`, `measure.py`, `target.py`. The repo is small. Read them once.
4. **Confirm with the human and go.**

If the branch already exists, you are **resuming** a prior run. Read the last 5 rows of `results.tsv` to see where you left off. The current `HEAD` of the branch is your baseline.

## The loop

Once started, run forever until the human stops you. **Do not ask "should I continue?" — keep going.**

For each experiment:

### 1. OBSERVE
Read `results.tsv` (last ~15 rows + the all-time best row). Read the current `target.py`. Look at the diagnostic dashboard from the last `measure.py` run.

### 1b. SEARCH
Before forming a hypothesis, ask: "Is there a known solution to this bottleneck?" Search online for the specific operation that dominates — e.g. `"numpy scatter sum faster"`, `"n-body simulation python optimisation"`, `"numba pairwise forces benchmark"`. Check Stack Overflow, GitHub issues, arXiv, and official library docs.

- If a library or algorithm appears repeatedly in credible sources as a solution to your exact bottleneck, treat it as a hypothesis candidate with the same weight as a code-level change. Install it and test it (see **Library installs** under Discipline).
- If microbenchmarks already ruled out pure-numpy improvements for this bottleneck, go straight to library search — don't grind more numpy variants.
- If `wall_clock` is below ~0.3s (measurement floor), stop optimising for speed and search for JIT options (Numba, Taichi, Cython) that reduce energy-per-instruction instead.

This step is **mandatory when**: (a) the same bottleneck has survived 3+ failed experiments, or (b) `wall_clock < 0.3s` and runs are consistently noisy.

### 2. HYPOTHESIZE
Write down, in your reasoning:

- **Causal claim:** a specific statement about *what physical mechanism* on the chip is responsible for current energy use. Example: *"Energy is dominated by the O(N²) pairwise force loop. Each iteration's working set exceeds L1; expect L1 miss rate to be high."*
- **Prediction:** a quantitative expectation that follows from the claim. Example: *"If I change the inner loop to operate on contiguous numpy arrays, L1 miss rate should drop by ≥50% and joules by ≥15%."*
- **Falsification:** what observation would refute the claim. Example: *"If joules don't drop or instructions retired stays roughly equal, the hypothesis was wrong — the bottleneck wasn't memory access pattern."*

A hypothesis without a quantitative prediction is not a hypothesis. Don't skip this step.

### 3. PICK AN INSTRUMENT (if needed)
`measure.py` collects a default dashboard on every run. If your hypothesis requires a signal not in the default set, look at `instruments.md` and decide whether to ask the human for an additional measurement. Default behavior: use the default dashboard.

### 4. CHANGE
Edit `target.py`. **The change must be justified by the hypothesis** — not "let me try this and see," but "the hypothesis predicts this change will help because X."

Commit: `git add target.py && git commit -m "hypothesis: <causal claim, one line>"`

### 5. MEASURE
```
python3 measure.py target.py > run.log 2>&1
```

Read the JSON result from the last line of `run.log`. If the run crashed (no JSON, or `error` field), read the last 50 lines of `run.log` for the stack trace. If it's a trivial fix, fix it and re-measure. If the idea is fundamentally broken, log it as `crash` and revert.

### 6. EVALUATE
- **Did joules drop** compared to the current best? → primary keep/revert signal.
- **Did the prediction hold?** Check the specific quantitative claim from step 2. This is the second-order signal.

### 7. LOG
Append one row to `results.tsv`:

```
commit	joules	wall_clock	instructions	cycles	ipc	max_rss_mb	page_faults	ctx_switches	run_quality	status	hypothesis	prediction	prediction_held	description
```

- `commit` — 7-char git short hash
- `joules`, `wall_clock`, etc. — from the measure.py JSON
- `run_quality` — `clean` or `noisy` (from measure.py)
- `status` — `keep`, `revert`, or `crash`
- `hypothesis` — your causal claim, one line
- `prediction` — your quantitative claim, one line
- `prediction_held` — `yes` / `no` / `unclear`
- `description` — what you actually changed, one line

Use **tab separators**, not commas. Do not commit `results.tsv` to git — it stays untracked.

### 8. KEEP OR REVERT
- If `joules` dropped AND `run_quality == clean` → **keep**. The commit stays.
- If `joules` did not drop OR `run_quality == noisy` → **revert**: `git reset --hard HEAD~1`.
- If crashed → revert.

Then return to step 1.

## Discipline

**Turn budget.** Each experiment should take ≤5 turns of reasoning. If you're deliberating longer, pick the most plausible change and run it. Bad data is better than no data; analysis paralysis is worse than either.

**Context discipline.** Do not re-read `program.md`, `instruments.md`, or `README.md` once you've read them at startup. They don't change. Do not read the full `results.tsv` — read only the tail (`tail -20 results.tsv`).

**Simplicity preference.** A small win that adds 30 lines of complexity is worse than the same win from deleting 10 lines. When in doubt, simpler.

**Library installs require research and proposal.** If you believe a library would unlock a meaningful optimization (e.g. Numba JIT, CuPy, Taichi, scipy sparse), do the following before skipping it:

1. **Search online** for evidence that the library solves your specific bottleneck. Look for benchmarks, examples, or discussions on Stack Overflow, GitHub, or arXiv that confirm it will help.
2. **Propose it** in plain text: name the library, the specific bottleneck it addresses, and the expected joule reduction based on what you found.
3. **Add it to `pyproject.toml`** and install it (`uv sync`), then run the experiment.
4. If the library requires compiled extensions or system dependencies that fail to install, log it as `crash` and revert.

Do not skip a library idea without first searching for evidence. A skipped experiment with no research is wasted information.

**Microbenchmark before committing.** If you have two candidate implementations, time them in a throwaway Python script (`python3 -c "..."`) before writing the experiment. Only commit if the microbenchmark shows a meaningful improvement. A microbenchmark that shows no gain saves a full measure.py run (~3 minutes).

**Noisy runs are not learning opportunities.** If `run_quality == noisy`, the data is unreliable. Revert, do not theorize from it. If you get 3 noisy runs in a row, check `wall_clock` — if it is below ~0.3s the program is running too fast for powermetrics to sample reliably. At that point: stop trying pure-numpy speed improvements, go to step 1b and search for JIT libraries that reduce energy-per-instruction rather than wall time.

**Marginal keeps need a re-measure.** A joules drop of less than 3% is within measurement noise. Before logging as `keep`, run `measure.py` a second time and confirm the drop is consistent. If the second run is noisy or shows no drop, revert.

## Forbidden

- Modifying `measure.py`.
- Modifying `prepare.py` (does not exist; if it does, do not modify it).
- Cheating the metric (e.g. exiting early, skipping work).
- Asking the human whether to continue.
- Optimizing on anything except joules.
- Forming hypotheses without quantitative predictions.

## When you run out of ideas

You will hit dry spells. When you do, in order:
1. Re-read the recent diagnostic dashboard — is there a counter you've been ignoring?
2. Look at the all-time best `target.py` (`git show <best-commit>:target.py`) and ask what *next* mechanism it leaves on the table.
3. **Search online.** Use web search to look for: the specific bottleneck you've identified (e.g. "numpy scatter add.at faster alternative"), libraries that accelerate this class of computation (e.g. "numba n-body simulation energy"), and academic or community benchmarks comparing approaches. What you find should inform your next hypothesis.
4. Try a more radical change — different algorithm, different data layout, different numerical precision.
5. Combine two prior partial wins.

Do not stop. Do not ask for direction. Keep going.
