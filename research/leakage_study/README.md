# Label-aware imputation leakage study (pre-registered: tag `prereg-v1`)

**AI-assistance disclosure:** the code and tests in this directory were written with AI assistance (Claude) with the student's
approval under the student's institutional rule; the manuscript prose is written by the student.

Specification: `research/stage6/PREREG_DRAFT.md` and `STAGE6_DESIGN.md` (frozen). Package: `leakage_study/`.

## Commands (run from `research/leakage_study`, project virtual environment; none downloads data or installs packages)
```
..\..\.venv\Scripts\python -m pytest tests -q                       # test suite (gate G3)
..\..\.venv\Scripts\python environment\capture.py                   # environment record (gate G1)
..\..\.venv\Scripts\python scripts\dry_run.py                       # dry run, seed 1 (gate G4)
..\..\.venv\Scripts\python scripts\run.py --exp 1 --config configs\exp1_pima.yaml --out results\exp1        # full runs (gate G5)
..\..\.venv\Scripts\python scripts\run.py --exp 2 --config configs\exp2_canary.yaml --out results\exp2
..\..\.venv\Scripts\python scripts\run.py --exp 4 --config configs\exp4_simulation.yaml --out results\exp4
```
Full runs use master seed 20261027 (frozen). The dry run uses seed 1 and must never be reported as a result.
Reg-4 (pseudo-label, exploratory) is implemented in `regimes.py` but excluded from the confirmatory configs.
