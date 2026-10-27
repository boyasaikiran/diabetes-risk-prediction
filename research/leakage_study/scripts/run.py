"""CLI for the full experiments.  Example:  python scripts/run.py --exp 1 --config configs/exp1_pima.yaml --out results/exp1
Run from research/leakage_study with the project's virtual environment."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from leakage_study.data import load_pima  # noqa: E402
from leakage_study.experiments import load_config, run_exp1, run_exp2, run_exp3, run_exp4, save_df, write_json  # noqa: E402
from leakage_study.simulate import estimate_corr  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", type=int, required=True, choices=[1, 2, 4])
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfg, out = load_config(a.config), Path(a.out)
    X, y = load_pima()
    if a.exp == 1:
        r = run_exp1(X, y, cfg)
        save_df(r["preds"], out / "predictions.csv.gz")
        for k in ("metrics", "importance", "timing", "contrasts"):
            save_df(r[k], out / f"{k}.csv")
        save_df(run_exp3(r), out / "exp3_diagnostics.csv")
    elif a.exp == 2:
        r = run_exp2(X, y, cfg)
        save_df(r["permuted"], out / "permuted_auc.csv.gz")
        save_df(r["flags"], out / "flags.csv")
        save_df(r["detection"], out / "detection.csv")
    else:
        r = run_exp4(estimate_corr(X), cfg)
        save_df(r["runs"], out / "runs.csv.gz")
        save_df(r["contrasts"], out / "contrasts.csv")
        write_json(r["calibration"], out / "calibration.json")
    write_json({"config": cfg, "config_file": a.config}, out / "run_config.json")
    print("done ->", out)


if __name__ == "__main__":
    main()
