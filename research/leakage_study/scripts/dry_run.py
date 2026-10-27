"""Gate G4 dry run. Engineering checks only (see configs/dry_run.yaml). Writes results/dry_run/.
Run from research/leakage_study:  ..\\..\\.venv\\Scripts\\python scripts\\dry_run.py"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from leakage_study.data import complete_case_mask, load_pima  # noqa: E402
from leakage_study.experiments import load_config, run_exp1, run_exp2, run_exp3, run_exp4, save_df, write_json  # noqa: E402
from leakage_study.runner import run_grid  # noqa: E402
from leakage_study.simulate import estimate_corr  # noqa: E402
from leakage_study.splits import make_splits  # noqa: E402

OUT = HERE / "results" / "dry_run"
cfg = load_config(HERE / "configs" / "dry_run.yaml")
seed = cfg["master_seed"]
assert seed == 1, "dry run must use master seed 1, never the study seed"
X, y = load_pima()
S: dict = {"master_seed": seed, "gates": {}, "timing_s": {}}

# ---- Exp 1
t = time.perf_counter()
e1 = run_exp1(X, y, {**cfg["exp1"], "master_seed": seed})
S["timing_s"]["exp1_wall"] = time.perf_counter() - t
save_df(e1["metrics"], OUT / "exp1_metrics.csv")
save_df(e1["contrasts"], OUT / "exp1_contrasts.csv")
save_df(e1["timing"], OUT / "exp1_timing.csv")
save_df(run_exp3(e1), OUT / "exp3_diagnostics.csv")
c = e1["contrasts"]
S["exp1_auc_contrasts"] = c[c["contrast"].isin(["E1_apparent_inflation_Reg-3_vs_Reg-0", "E2_gap_Reg-3", "E3_harm_Reg-3", "E4_label_effect_Reg-2_vs_Reg-0", "E4_scope_effect_Reg-1_vs_Reg-0"])][
    ["model", "contrast", "mean", "sd", "se_corrected", "lo", "hi", "J"]].round(4).to_dict("records")
tm = e1["timing"].groupby("model")[["fit_s", "importance_s"]].mean()
S["mean_task_seconds_by_model"] = (tm["fit_s"] + tm["importance_s"]).round(3).to_dict()

# ---- Exp 2 and gate: Reg-0 permuted-label AUC within 0.5 +/- 0.02
t = time.perf_counter()
e2 = run_exp2(X, y, {**cfg["exp2"], "master_seed": seed})
S["timing_s"]["exp2_wall"] = time.perf_counter() - t
save_df(e2["detection"], OUT / "exp2_detection.csv")
ref = e2["permuted"][e2["permuted"]["regime"] == "Reg-0"].groupby("model")["auc"].mean()
S["gates"]["G_reg0_permuted_auc_within_0.5+-0.02"] = {k: round(float(v), 4) for k, v in ref.items()} | {"pass": bool(((ref - 0.5).abs() <= 0.02).all())}
S["canary_detection_dry"] = e2["detection"].round(3).to_dict("records")

# ---- Negative control B: complete-case Pima, all regimes must coincide exactly
cc = complete_case_mask(X)
Xc, yc = X[cc], y[cc]
splits = make_splits(yc, cfg["negative_control_b"]["n_splits"], seed)
preds, _, _ = run_grid(Xc, yc, splits, ["Reg-0", "Reg-1", "Reg-2", "Reg-3"], cfg["negative_control_b"]["models"])
wide = preds.pivot_table(index=["split", "model", "eval", "row"], columns="regime", values="p")
maxdiff = float((wide.sub(wide["Reg-0"], axis=0)).abs().to_numpy().max())
S["gates"]["G_negative_control_B_complete_case_identical"] = {"n_complete_cases": int(cc.sum()), "max_abs_prediction_diff": maxdiff, "pass": maxdiff == 0.0}

# ---- Exp 4 and negative control A (pi = 0 -> all regimes identical)
t = time.perf_counter()
e4 = run_exp4(estimate_corr(X), {**cfg["exp4"], "master_seed": seed})
S["timing_s"]["exp4_wall"] = time.perf_counter() - t
save_df(e4["contrasts"], OUT / "exp4_contrasts.csv")
save_df(e4["runs"], OUT / "exp4_runs.csv.gz")
z = e4["runs"][e4["runs"]["pi"] == 0.0]
w = z.pivot_table(index=["cell", "rep", "model"], columns="regime", values="auc_app")
d0 = float(w.sub(w["Reg-0"], axis=0).abs().to_numpy().max())
S["gates"]["G_negative_control_A_pi0_identical"] = {"max_abs_auc_diff": d0, "pass": d0 < 1e-9}
S["exp4_calibration"] = e4["calibration"]
S["exp4_contrasts_E1"] = e4["contrasts"][e4["contrasts"]["contrast"] == "E1_inflation_Reg-3_vs_Reg-0"][["n", "pi", "mechanism", "target_auc", "model", "mean", "sd", "lo", "hi"]].round(4).to_dict("records")

# ---- compute extrapolation (rough; not a promise)
n_jobs = cfg["exp1"]["n_jobs"]
per_model = (tm["fit_s"] + tm["importance_s"]).to_dict()
exp1_total = sum(per_model[m] * 4 * 100 for m in per_model)  # 4 regimes x 100 splits per model
S["extrapolated_serial_hours"] = {"exp1": round(exp1_total / 3600, 2)}
n_sim_pipelines = 5 * 2 * 3 * 2 * 4 * 3 * 50
sim_units = max(len(e4["runs"]), 1)
S["extrapolated_serial_hours"]["exp4_from_dry_run_ratio"] = round(S["timing_s"]["exp4_wall"] * n_jobs / sim_units * n_sim_pipelines / 3600, 2)
S["extrapolation_note"] = f"serial-equivalent; divide by effective parallelism (n_jobs={n_jobs}). Exp 4 at n=5000 will be slower than this n=768 dry run."
S["all_gates_pass"] = all(v["pass"] for v in S["gates"].values())
write_json(S, OUT / "dry_run_summary.json")
print(pd.Series({k: v for k, v in S["timing_s"].items()}))
print("gates:", {k: v["pass"] for k, v in S["gates"].items()}, "| all pass:", S["all_gates_pass"])
