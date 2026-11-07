# REPRODUCIBILITY (draft, written while Exp 4 was still running)

Status key: **[recorded]** = read from a file in the repository; **[reported]** = stated earlier in the project but not re-checked here; **[PENDING]** = cannot be verified until Exp 4, G6 and the verification pass finish. Nothing below is a scientific result.

## 1. Frozen identifiers
| Item | Value | Status |
|---|---|---|
| Pre-registration tag | `prereg-v1`, commit `6cf3d8c3bafbbaceca48396e9f53560fdb34a50e` | [recorded] `environment.json`, `git log` |
| Frozen files + SHA-256 | `PREREG_DRAFT.md`, `STAGE6_DESIGN.md`, `experiment_matrix.csv`; full SHA-256 values in `research/stage6/PREREG_FREEZE.txt` (not abbreviated here to avoid transcription errors) | [recorded]; re-hash check [PENDING] |
| Experiment code | tag `leakage-code-v0.1.1`, commit `3cff89f739e2d15d7f488a7c5252022adad1fd1f` | [recorded] |
| Earlier code tag | `leakage-code-v0.1` (`022c2a4`), used for the dry run before the `penalty=None` → `C=np.inf` fix | [recorded] |
| Analysis / audit code | tag `analysis-code-v1`, commit `e508d75` (HEAD at run time). Adds `leakage_study/analysis.py` and `scripts/{analyze,audit_g6,verify_report}.py` on top of v0.1.1. Committed before any full-run result was inspected. | [recorded] |
| Environment record | commit `dc4b04b` (`environment/environment.json`, `requirements.lock.txt`) | [recorded] |
| Dataset | Pima, OpenML id 37, 768 rows; SHA-256 `779e408fd8c0792f4f6accb05cce14dcd6cdc7aaeaa643b34667134dfc655b49` (checked by `load_pima`) | [recorded] |
| Master seed | `20261027` (full runs). Dry run used seed `1`; never reused for reported results. | [recorded] PREREG §8 |

Seed derivation: all split, permutation, simulation and model seeds come from `numpy.random.SeedSequence` spawned from the master seed (PREREG §8). Per-task seeds are independent of the number of workers.

## 2. Environment
Captured by `environment/capture.py` at 2026-10-27T11:29:54Z [recorded]:
- Python 3.12.3; Windows-11-10.0.26200-SP0
- numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, scikit-learn 1.9.1, joblib 1.6.0, PyYAML 6.0.3, pytest 9.1.1
- CPU: AMD64 Family 25 Model 80 (AMD), 12 logical cores. Total RAM, disk and exact CPU model name: **not recorded** [PENDING; do not state until measured].
- Full pinned list: `environment/requirements.lock.txt`.
- Parallelism: joblib/loky, `n_jobs: 4` in the frozen Exp 4 config. Results are designed not to depend on `n_jobs`; this has **not** been independently tested [PENDING].

## 3. Configurations (frozen, in `research/leakage_study/configs/`)
- `exp1_pima.yaml` (real data, J = 100 paired splits, 4 regimes, 5 models)
- `exp2_canary.yaml` (10 splits × 100 permutations)
- `exp4_simulation.yaml` (π ∈ {0, .10, .25, .50, .75}, MCAR/MNAR, target AUC {.70,.80,.90}, n ∈ {768, 5000}, regimes Reg-0..3, models LR / RF-default / HGB, 50 reps, truth sample 20,000, prevalence .35)
- `dry_run.yaml` (engineering only; never used for findings)
Config-vs-saved-config match: [PENDING] (G6 check).

## 4. Commands (run from `research/leakage_study`, project venv `..\..\.venv`)
```bash
python scripts/run.py --exp 1 --config configs/exp1_pima.yaml       --out results/exp1
python scripts/run.py --exp 2 --config configs/exp2_canary.yaml     --out results/exp2
python scripts/run.py --exp 4 --config configs/exp4_simulation.yaml --out results/exp4
python scripts/audit_g6.py            # pre-registered consistency audit; writes results/audit/AUDIT_G6.{json,md}
python scripts/analyze.py             # refuses to run unless the audit passed and result hashes are unchanged
python scripts/verify_report.py       # independent re-derivation of registered report numbers
python -m pytest tests                # study tests
```
Exp 1 and Exp 2 were launched by a background shell wrapper that appended `exit N` to `run.log`; the wrapper text itself is not archived in the repository, so the commands above are the equivalent direct invocations [reported]. Exp 4 attempt 2 was launched with `Start-Process` (stdout/stderr to `results/exp4/stdout.log` and `stderr.log`, start time to `run.log`).

## 5. Known execution issues
1. **Exp 4 attempt 1 failed.** Started about 17:09 (local) on 2026-10-27; the background task was reported failed at 18:21 with exit code 4. `run.log` was empty: no traceback, no partial outputs. Cause **unknown**. Record: `results/exp4_failed_attempt1/{run.log,FAILURE_NOTE.md}`. Nothing from it was used.
2. **Exp 4 attempt 2** started 20:57:43 with the identical frozen config, seed and code (`analysis-code-v1`, tree clean). Because it was launched detached, its exit code may not be recoverable. If so, completion will be judged from the output inventory, empty `stderr.log`, `stdout.log` showing `done -> results\exp4`, and the G6 audit, not from the files merely existing. Final status: [PENDING].
3. **Code v0.1 → v0.1.1** (deprecated sklearn `penalty=None` replaced by `C=np.inf`, numerically identical). Disclosed deviation.
4. **Known labelling defect in frozen `sim_contrasts`:** the `n` column of `results/exp4/contrasts.csv` holds the replicate count, not dataset size. The frozen code is unchanged; `analysis.sim_contrasts_correct` recomputes from raw runs; audit check D5 and a pinning test cover it.
5. **Concurrency:** Exp 1, 2 and 4 were run at the same time on one machine; runtimes are therefore not stand-alone timings.
6. Dry-run results are engineering-only and are not used anywhere.

## 6. Test and lint claims
51 study tests, 45 application tests and ruff were reported as passing earlier. G6 re-runs the study tests; application tests and ruff are not part of the study's evidence [PENDING re-run at final commit].

## 7. Outputs expected (inventory to be confirmed after the runs)
`results/exp1/{predictions.csv.gz,metrics.csv,importance.csv,timing.csv,contrasts.csv,exp3_diagnostics.csv,run_config.json}`; `results/exp2/{permuted_auc.csv.gz,flags.csv,detection.csv,run_config.json}`; `results/exp4/{runs.csv.gz,contrasts.csv,calibration.json,run_config.json}`; `results/audit/`, `results/analysis/`, `reports/`. Results directories are untracked in git; large files should be archived with SHA-256 hashes [PENDING].

## 8. Actual runtimes
Exp 1: [PENDING, from log/file timestamps]. Exp 2: [PENDING]. Exp 4 attempt 2: started 20:57:43, end [PENDING]. Not to be filled from estimates.
