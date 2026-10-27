# Dry run report (gate G4) — engineering output, NOT a study result

Seed 1 (never reused for a reported result), code state `leakage-code-v0.1`; machine: 12 logical CPUs, `n_jobs = 4`.
Per `PREREG_DRAFT.md` §8 this dry run may be used only for runtime, test-suite health and planning the CI width. **It may not be used to change hypotheses, regimes, models, SESOI, thresholds or decision rules, and none of the numbers below may be reported as findings.**

## Gates
| Gate | Result |
|---|---|
| Reg-0 permuted-label AUC within 0.5 ± 0.02 (LR / RF-default) | **pass** (0.499 / 0.509) |
| Negative control B: complete-case Pima (n = 392), all regimes identical | **pass** (max prediction difference 0.0) |
| Negative control A: simulation with π = 0, all regimes identical | **pass** (max AUC difference 0.0) |
| Test suite (51 tests) | **pass** (71 s) |
| Mutation check: 4 injected leaks into the valid regime | **all caught** |

## Runtime (dry run → full run, rough)
| Experiment | Dry run | Full run estimate (4 workers) |
|---|---|---|
| Exp 1 (5 → 100 splits) | 28 s | roughly 10 min (serial ≈ 0.5 h) |
| Exp 2 (2 splits × 20 perms, 2 models → 10 × 100, 5 models) | 25 s | well under 1 h |
| Exp 4 (4 cells × 5 reps, n = 768 → full grid, n up to 5000) | 33 s | about 1.5-3 h (n = 5000 random forests are slower) |

Mean seconds per fitted task (fit + importance where applicable): LR 0.22, RF-default 3.2, RF-regularised 0.48, HGB 0.51, SVM 0.05.

## Planning facts for the CI width (no decisions changed)
Per-split SD of the paired ROC-AUC difference was about 0.010 (RF-default) and 0.007 (LR) on 5 splits, below the 0.02 guessed in the design. With J = 100 the corrected standard error would be roughly `sqrt(0.01 + 0.25) × SD`, i.e. about 0.005 (RF) and 0.004 (LR), so half-widths of about 0.01 and 0.007. The corrected interval is dominated by the n_test/n_train term, as the design warned; for LR the interval may still straddle the pre-registered SESOI of 0.02.

## Issues found and handled
- A scikit-learn deprecation warning (`penalty=None`) in the calibration metric was replaced by the equivalent `C=np.inf`; numbers are identical to 10 digits (code `leakage-code-v0.1.1`).
- One full test run took 17.8 minutes (versus ≈ 1 minute); the machine was otherwise idle and the dry run and later reruns were normal, so I attribute it to a system pause. Not reproduced.

## Not yet done
Full runs (gate G5) have **not** been started.
