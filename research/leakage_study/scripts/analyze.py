"""Pre-registered contrasts, figures and reports. Refuses to run unless the G6 audit passed and the audited files are unchanged.
Run after audit_g6.py:  ..\\..\\.venv\\Scripts\\python scripts\\analyze.py
Every number placed in a report is registered in results/analysis/report_numbers.json and re-derived by verify_report.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from leakage_study.analysis import SESOI, exp1_decisions, exp2_decision, exp4_h5, sim_contrasts_correct  # noqa: E402
from leakage_study.experiments import contrast_table  # noqa: E402
from leakage_study.stats import nb_corrected_ci  # noqa: E402

NUM: dict = {}


def reg(key: str, value, fmt: str, source: str) -> str:
    """Format a number for a report and register it for independent verification."""
    text = format(value, fmt) if isinstance(value, (int, float, np.integer, np.floating)) else str(value)
    NUM[key] = {"value": float(value) if isinstance(value, (int, float, np.integer, np.floating)) else str(value), "text": text, "source": source}
    return text


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(out)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()


def main(res: Path, out: Path, reports: Path, n_total: int, test_mode: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    banner = "> **TEST MODE: smoke test on synthetic toy results. Not study output.**\n\n" if test_mode else ""
    audit_path = res / "audit" / "AUDIT_G6.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    if not test_mode:
        if audit is None or not audit["all_pass"]:
            sys.exit("REFUSING TO RUN: the G6 audit has not passed (results/audit/AUDIT_G6.json missing or failing).")
        for rel, h in audit["result_file_sha256"].items():
            if sha(HERE / rel) != h:
                sys.exit(f"REFUSING TO RUN: audited file changed since the audit: {rel}")

    M = pd.read_csv(res / "exp1/metrics.csv")
    P_rows = pd.read_csv(res / "exp1/predictions.csv.gz", usecols=["split", "regime", "model", "eval", "row"])
    n_test = int(P_rows.groupby(["split", "regime", "model", "eval"]).size().iloc[0])
    n_train = n_total - n_test
    J = int(M["split"].nunique())
    cfg1 = json.loads((res / "exp1/run_config.json").read_text(encoding="utf-8"))["config"]
    cfg2 = json.loads((res / "exp2/run_config.json").read_text(encoding="utf-8"))["config"]
    cfg4 = json.loads((res / "exp4/run_config.json").read_text(encoding="utf-8"))["config"]
    rt = audit["runtimes"] if audit else {k: {"seconds_wall": float("nan")} for k in ("exp1", "exp2", "exp4")}

    # ------------------------------------------------------------ Exp 1 contrasts and decisions
    D1 = exp1_decisions(M, n_train, n_test)
    allc = pd.concat([contrast_table(M, n_train, n_test, metric=m) for m in ["auc", "pr_auc", "brier", "cal_slope", "cal_intercept", "sens_0.5", "spec_0.5", "sens_prev", "spec_prev"]], ignore_index=True)
    allc.to_csv(out / "exp1_contrasts_all_metrics.csv", index=False)
    levels = []
    for (model, regime, ev), g in M.groupby(["model", "regime", "eval"]):
        ci = nb_corrected_ci(g["auc"].to_numpy(), n_train, n_test)
        levels.append({"model": model, "regime": regime, "eval": ev, "mean_auc": ci["mean"], "sd_across_splits": ci["sd"], "ci_lo": ci["lo"], "ci_hi": ci["hi"]})
    levels = pd.DataFrame(levels)
    levels.to_csv(out / "exp1_levels_auc.csv", index=False)
    auc_c = allc[allc["metric"] == "auc"]

    diag_path = res / "exp1/exp3_diagnostics.csv"
    diag = pd.read_csv(diag_path) if diag_path.exists() and diag_path.stat().st_size > 5 else pd.DataFrame()
    diag_rows = []
    if not diag.empty:
        for model in sorted(diag["model"].unique()):
            for col in ("LAS", "cal_slope", "brier"):
                for regime in ("Reg-1", "Reg-2", "Reg-3"):
                    a = diag[(diag["model"] == model) & (diag["regime"] == regime)].set_index("split")[col]
                    b = diag[(diag["model"] == model) & (diag["regime"] == "Reg-0")].set_index("split")[col]
                    d = (a - b).dropna()
                    if len(d) >= 2:
                        ci = nb_corrected_ci(d.to_numpy(), n_train, n_test)
                        diag_rows.append({"model": model, "measure": col, "contrast": f"{regime} - Reg-0", **{k: ci[k] for k in ("mean", "lo", "hi")}})
    diag_c = pd.DataFrame(diag_rows)
    diag_c.to_csv(out / "exp3_diagnostic_contrasts.csv", index=False)

    # ------------------------------------------------------------ Exp 2
    DET = pd.read_csv(res / "exp2/detection.csv")
    PA = pd.read_csv(res / "exp2/permuted_auc.csv.gz")
    D2 = exp2_decision(DET)
    perm_levels = PA.groupby(["model", "regime"])["auc"].agg(["mean", "std"]).reset_index().rename(columns={"mean": "mean_perm_auc", "std": "sd_perm_auc"})
    perm_levels.to_csv(out / "exp2_permuted_auc_levels.csv", index=False)

    # ------------------------------------------------------------ Exp 4
    R4 = pd.read_csv(res / "exp4/runs.csv.gz")
    C4 = sim_contrasts_correct(R4)  # the saved contrasts.csv has a mislabelled `n` column (see analysis.sim_contrasts_correct)
    C4.to_csv(out / "exp4_contrasts_corrected.csv", index=False)
    H5 = exp4_h5(C4)
    cal4 = json.loads((res / "exp4/calibration.json").read_text(encoding="utf-8"))

    decisions = {"H1": D1["H1"], "H2": D1["H2"], "H3": D1["H3"], "H4": D1["H4"], "holm_supplementary": D1["holm"], "H5": {k: v for k, v in H5.items() if k != "groups"}, "H6": D2}
    (out / "decisions.json").write_text(json.dumps(decisions, indent=1, default=str), encoding="utf-8")

    # ------------------------------------------------------------ figures (from saved data only)
    fig_dir = out / "figures"
    (fig_dir / "data").mkdir(parents=True, exist_ok=True)
    models = list(cfg1["models"])
    fig, axes = plt.subplots(1, len(models), figsize=(3.2 * len(models), 3.6), sharey=True)
    for ax, m in zip(np.atleast_1d(axes), models, strict=True):
        for ev, mk, fc in (("app", "o", "tab:red"), ("dep", "s", "tab:blue")):
            d = levels[(levels["model"] == m) & (levels["eval"] == ev)].set_index("regime").reindex(cfg1["regimes"])
            x = np.arange(len(d)) + (0.08 if ev == "dep" else -0.08)
            ax.errorbar(x, d["mean_auc"], yerr=[d["mean_auc"] - d["ci_lo"], d["ci_hi"] - d["mean_auc"]], fmt=mk, color=fc, capsize=3, label="apparent (regime's own imputation)" if ev == "app" else "deployment (label-free)")
        ax.set_xticks(range(len(cfg1["regimes"])), cfg1["regimes"], rotation=30)
        ax.set_title(m)
        ax.grid(alpha=0.3)
    np.atleast_1d(axes)[0].set_ylabel("held-out ROC-AUC (mean, corrected 95% CI)")
    np.atleast_1d(axes)[-1].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig2_exp1_apparent_vs_deployment.png", dpi=160)
    plt.close(fig)
    levels.to_csv(fig_dir / "data/fig2_data.csv", index=False)

    e1 = C4[C4["contrast"] == "E1_inflation_Reg-3_vs_Reg-0"]
    ns, aucs = sorted(e1["n"].unique()), sorted(e1["target_auc"].unique())
    fig, axes = plt.subplots(len(ns), len(aucs), figsize=(3.6 * len(aucs), 3.0 * len(ns)), sharex=True, squeeze=False)
    for i, n in enumerate(ns):
        for j, a in enumerate(aucs):
            ax = axes[i][j]
            for model, col in zip(sorted(e1["model"].unique()), ("tab:blue", "tab:green", "tab:red"), strict=False):
                for mech, ls in (("MCAR", "-"), ("MNAR", "--")):
                    g = e1[(e1["n"] == n) & (e1["target_auc"] == a) & (e1["model"] == model) & (e1["mechanism"] == mech)].sort_values("pi")
                    ax.plot(g["pi"], g["mean"], ls, color=col, marker="o", ms=3, label=f"{model} {mech}")
                    ax.fill_between(g["pi"], g["lo"], g["hi"], color=col, alpha=0.12)
            ax.set_title(f"n = {n}, oracle AUC {a}", fontsize=9)
            ax.grid(alpha=0.3)
            if j == 0:
                ax.set_ylabel("apparent inflation\n(Reg-3 - Reg-0 ROC-AUC)")
            if i == len(ns) - 1:
                ax.set_xlabel("missing fraction pi")
    axes[0][-1].legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig3_exp4_dose_response.png", dpi=160)
    plt.close(fig)
    e1.to_csv(fig_dir / "data/fig3_data.csv", index=False)

    fig, axes = plt.subplots(1, len(cfg2["models"]), figsize=(3.0 * len(cfg2["models"]), 3.4), sharey=True)
    for ax, m in zip(np.atleast_1d(axes), cfg2["models"], strict=True):
        data = [PA[(PA["model"] == m) & (PA["regime"] == r)]["auc"].to_numpy() for r in cfg2["regimes"]]
        ax.boxplot(data, tick_labels=cfg2["regimes"])
        ax.axhline(0.5, color="gray", ls=":")
        ax.set_title(m)
        ax.tick_params(axis="x", rotation=30)
    np.atleast_1d(axes)[0].set_ylabel("held-out AUC with PERMUTED labels")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_exp2_canary.png", dpi=160)
    plt.close(fig)
    perm_levels.to_csv(fig_dir / "data/fig4_data.csv", index=False)

    if not diag.empty:
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
        for ax, col, ttl in ((axes[0], "LAS", "leak-attribution share"), (axes[1], "cal_slope", "calibration slope (apparent)")):
            for k, m in enumerate(sorted(diag["model"].unique())):
                for r, regime in enumerate(cfg1["regimes"]):
                    v = diag[(diag["model"] == m) & (diag["regime"] == regime)][col].dropna().to_numpy()
                    if len(v):
                        ax.boxplot(v, positions=[r + (k - 1) * 0.25], widths=0.2, showfliers=False)
            ax.set_xticks(range(len(cfg1["regimes"])), cfg1["regimes"])
            ax.set_title(ttl + " (boxes per model within regime)", fontsize=8)
        fig.tight_layout()
        fig.savefig(fig_dir / "fig5_exp3_diagnostics.png", dpi=160)
        plt.close(fig)
        diag.to_csv(fig_dir / "data/fig5_data.csv", index=False)

    # ------------------------------------------------------------ reports
    def ci_str(c: dict, key: str, fmt: str = ".4f") -> str:
        return f"{reg(key + '_mean', c['mean'], fmt, 'analysis')} (95% CI {reg(key + '_lo', c['lo'], fmt, 'analysis')} to {reg(key + '_hi', c['hi'], fmt, 'analysis')})"

    h1, h2, h3, h4 = D1["H1"], D1["H2"], D1["H3"], D1["H4"]
    gate = {c["id"]: c for c in audit["checks"]} if audit else {}

    def gstat(cid: str) -> str:
        return ("PASS" if gate[cid]["passed"] else "FAIL") if cid in gate else "not run (test mode)"

    run_cmd = ("```\ncd research/leakage_study\n..\\..\\.venv\\Scripts\\python -m pytest tests -q\n"
               "..\\..\\.venv\\Scripts\\python scripts\\run.py --exp 1 --config configs\\exp1_pima.yaml --out results\\exp1\n"
               "..\\..\\.venv\\Scripts\\python scripts\\run.py --exp 2 --config configs\\exp2_canary.yaml --out results\\exp2\n"
               "..\\..\\.venv\\Scripts\\python scripts\\run.py --exp 4 --config configs\\exp4_simulation.yaml --out results\\exp4\n"
               "..\\..\\.venv\\Scripts\\python scripts\\audit_g6.py\n..\\..\\.venv\\Scripts\\python scripts\\analyze.py\n..\\..\\.venv\\Scripts\\python scripts\\verify_report.py\n```")

    # ----- Exp 1 report
    rf_tbl = auc_c[auc_c["contrast"].isin(["E1_apparent_inflation_Reg-3_vs_Reg-0", "E4_label_effect_Reg-2_vs_Reg-0", "E4_scope_effect_Reg-1_vs_Reg-0", "E4_interaction", "E2_gap_Reg-0", "E2_gap_Reg-1", "E2_gap_Reg-2", "E2_gap_Reg-3", "E3_harm_Reg-1", "E3_harm_Reg-2", "E3_harm_Reg-3"])]
    rows = [{"model": r.model, "contrast": r.contrast, "mean": f"{r.mean:.4f}", "95% CI (NB-corrected)": f"{r.lo:.4f} to {r.hi:.4f}", "SD across splits": f"{r.sd:.4f}"} for r in rf_tbl.itertuples()]
    exp1_md = f"""{banner}# Exp 1 report — label-aware imputation on real Pima data

**Research question.** How much does outcome-conditional imputation of Pima's impossible zeros inflate held-out discrimination relative to leakage-safe imputation, how does it depend on model family, and what does it do to deployment performance?

**Setup (frozen config, seed {cfg1['master_seed']}).** {J} paired stratified 80/20 splits ({n_train}/{n_test}) of all {n_total} rows; regimes {', '.join(cfg1['regimes'])}; models {', '.join(cfg1['models'])}; each fitted model is evaluated on the held-out rows imputed by the regime's own rule (App) and with label-free training medians (Dep). Fixed untuned model settings. Inference: Nadeau–Bengio corrected CIs over splits (splits are not treated as independent).

**Completed runs.** {reg('exp1_groups', len(M) , 'd', 'metrics.csv')} (split, regime, model, eval) groups; {reg('exp1_fits', len(M) // 2, 'd', 'metrics.csv')} fitted models. **Measured wall time:** {reg('rt_exp1', rt['exp1']['seconds_wall'], '.0f', 'audit')} s (concurrent with Exp 2 and 4).

## Pre-registered decisions (execution success is not confirmation; these are the hypothesis outcomes)
| Hypothesis | Contrast | Estimate | Status |
|---|---|---|---|
| H1 (primary, confirmatory) | E1, RF-default, ROC-AUC (SESOI {SESOI}) | {ci_str(h1, 'h1')} | **{h1['status']}** |
| H2 | E1(RF-default) − E1(LR) | {ci_str(h2, 'h2')} | **{h2['status']}** |
| H3 | label effect − scope effect (RF-default); interaction within ±{SESOI}? | {ci_str(h3['label_minus_scope'], 'h3')}; interaction {ci_str(h3['interaction'], 'h3i')} | **{h3['status']}** |
| H4 | E2 gap RF-default: Reg-2 {ci_str(h4['gap_ci']['Reg-2'], 'h4r2')}; Reg-3 {ci_str(h4['gap_ci']['Reg-3'], 'h4r3')}; Reg-0 {ci_str(h4['gap_ci']['Reg-0'], 'h4r0')}; Reg-1 {ci_str(h4['gap_ci']['Reg-1'], 'h4r1')} | see left | **{h4['status']}** |

Supplementary Holm-adjusted one-sided p-values (family H2, H3, H4 Reg-2, H4 Reg-3): {', '.join(f'{n} {reg("holm_" + n, a, ".4g", "analysis")}' for n, a in zip(D1['holm']['family'], D1['holm']['adjusted_p'], strict=True))}. (Construction of these p-values was not specified in the frozen plan and is listed under operationalisations in FULL_RUN_REPORT.md.)

## Contrasts on ROC-AUC (all models; NB-corrected 95% CI)
{md_table(pd.DataFrame(rows))}

Other metrics (PR-AUC, Brier, calibration intercept/slope, sensitivity/specificity at τ = 0.5 and at training prevalence) are in `results/analysis/exp1_contrasts_all_metrics.csv`. Mean ROC-AUC by regime, evaluation and model is in `results/analysis/exp1_levels_auc.csv` and Figure 2.

## Gate-by-gate status (from the G6 audit)
Counts/duplicates/labels/splits (B1–B6): {', '.join(f'{c}:{gstat(c)}' for c in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6'])}; metrics recomputed from predictions (B7, B8): {gstat('B7')}, {gstat('B8')}; importance/timing tables (B9, B10): {gstat('B9')}, {gstat('B10')}; reproduction of cells from scratch (E1): {gstat('E1')}; negative control B on real complete cases (G3): {gstat('G3')}.

## Deviations and failures
See FULL_RUN_REPORT.md section 10. No run failure is recorded for Exp 1 unless the audit says otherwise (A4_exp1: {gstat('A4_exp1')}).

## Outputs and reproduction
`results/exp1/` (predictions.csv.gz, metrics.csv, contrasts.csv, importance.csv, timing.csv, exp3_diagnostics.csv, run.log, run_config.json); `results/analysis/`; figures in `results/analysis/figures/`. Reproduce with:
{run_cmd}
"""
    (reports / "EXP1_REPORT.md").write_text(exp1_md, encoding="utf-8")

    # ----- Exp 2 report
    detd = DET.copy()
    for c in ("rate", "wilson_lo", "wilson_hi", "mean_perm_auc"):
        detd[c] = detd[c].map(lambda v: f"{v:.3f}")
    ref0 = perm_levels[perm_levels["regime"] == "Reg-0"].set_index("model")["mean_perm_auc"]
    exp2_md = f"""{banner}# Exp 2 report — label-permutation canary

**Research question.** Can a label-permutation canary detect label-dependent preprocessing without knowing the true effect?

**Setup (frozen config, seed {cfg2['master_seed']}).** The first {cfg2['n_splits_used']} of the Exp 1 splits; {cfg2['n_perm']} global label permutations per regime × model (identical permutations across regimes and models for each split); regimes {', '.join(cfg2['regimes'])}; models {', '.join(cfg2['models'])}. A cell is **flagged** if its mean permuted-label AUC exceeds μ0 + 2σ0 of the Reg-0 reference of the same model.

**Completed runs.** {reg('exp2_rows', len(PA), 'd', 'permuted_auc.csv.gz')} permuted-label fits. **Measured wall time:** {reg('rt_exp2', rt['exp2']['seconds_wall'], '.0f', 'audit')} s (concurrent with Exp 1 and 4).

## Detection rates (fraction of splits flagged; Wilson 95% interval)
{md_table(detd[['model', 'regime', 'flagged', 'n_splits', 'rate', 'wilson_lo', 'wilson_hi', 'mean_perm_auc']])}

## H6 (decision rule on flexible models RF-default, RF-regularised, HGB): **{D2['status']}**
{md_table(pd.DataFrame([{'model': r['model'], 'TPR Reg-2': f"{r['tpr']['Reg-2']:.2f}", 'TPR Reg-3': f"{r['tpr']['Reg-3']:.2f}", 'FPR Reg-0': f"{r['fpr']['Reg-0']:.2f}", 'FPR Reg-1': f"{r['fpr']['Reg-1']:.2f}", 'meets thresholds': r['meets_thresholds']} for r in D2['flexible_models']]))}

Reg-0 is the reference that defines the threshold, so its flag rate is near zero by construction; only the Reg-1 rate is an informative false-positive estimate. Per-split flags are dependent samples (same data), so Wilson intervals are indicative only. Power for non-flexible models (LR, SVM-RBF) is reported but not part of H6.

## Gate-by-gate status
Records/duplicates/missing (C1): {gstat('C1')}; splits used (C2): {gstat('C2')}; flags recomputed (C3): {gstat('C3')}; cell reproduced from scratch (E2): {gstat('E2')}; **stop rule 1** (Reg-0 permuted AUC within 0.5 ± 0.02, G1): {gstat('G1')} — Reg-0 means: {', '.join(f'{k} {reg("ref0_" + k, v, ".4f", "permuted_auc.csv.gz")}' for k, v in ref0.items())}.

## Outputs and reproduction
`results/exp2/` (permuted_auc.csv.gz, flags.csv, detection.csv), `results/analysis/exp2_permuted_auc_levels.csv`, Figure 4. Reproduce:
{run_cmd}
"""
    (reports / "EXP2_REPORT.md").write_text(exp2_md, encoding="utf-8")

    # ----- Exp 4 report
    key = C4[(C4["contrast"] == "E1_inflation_Reg-3_vs_Reg-0") & (C4["mechanism"] == "MCAR") & (C4["n"] == min(cfg4["n"])) & (C4["target_auc"] == sorted(cfg4["target_auc"])[len(cfg4["target_auc"]) // 2])]
    ktab = key.pivot_table(index="pi", columns="model", values="mean").round(4).reset_index()
    exp4_md = f"""{banner}# Exp 4 report — controlled simulation (synthetic data; no clinical claims)

**Research question.** Does apparent inflation from label-aware imputation scale with the missing fraction and model flexibility when the truth is known?

**Setup (frozen config, seed {cfg4['master_seed']}).** π ∈ {cfg4['pi']}; mechanism {cfg4['mechanism']}; oracle AUC {cfg4['target_auc']}; n {cfg4['n']}; regimes {', '.join(cfg4['regimes'])}; models {', '.join(cfg4['models'])}; {cfg4['reps']} independent replicates per cell; truth sample {cfg4['truth_n']}. Calibrated generator parameters (κ, b0): {json.dumps({k: {a: round(b, 4) for a, b in v.items()} for k, v in cal4.items()})}.

**Completed runs.** {reg('exp4_rows', len(R4), 'd', 'runs.csv.gz')} pipeline runs. **Measured wall time:** {reg('rt_exp4', rt['exp4']['seconds_wall'], '.0f', 'audit')} s (concurrent with Exp 1 and 2).

## H5 (simulation): **{H5['status']}**
{H5['n_groups']} groups (n × mechanism × oracle AUC × model). Violations of "mean inflation at π = 0 within ±0.005": {reg('h5_pi0_viol', len(H5['pi0_violations']), 'd', 'contrasts.csv')}. Groups where mean inflation is not non-decreasing in π for RF-default or HGB: {reg('h5_mono_viol', len(H5['monotone_violations_flexible']), 'd', 'contrasts.csv')}. Independent replicates, so intervals are ordinary (not Nadeau–Bengio).

## Mean apparent inflation (Reg-3 − Reg-0 ROC-AUC) by missing fraction, MCAR, n = {min(cfg4['n'])}, oracle AUC {sorted(cfg4['target_auc'])[len(cfg4['target_auc']) // 2]}
{md_table(ktab)}

Full grid with CIs (corrected `n` labels): `results/analysis/exp4_contrasts_corrected.csv`; deployment gap and harm contrasts are in the same file; Figure 3. (The `n` column of the saved `results/exp4/contrasts.csv` holds the replicate count, a labelling defect in the frozen summary code; raw runs and per-cell numbers are unaffected. See FULL_RUN_REPORT.md section 10.)

## Gate-by-gate status
Counts/duplicates (D1): {gstat('D1')}; cell parameters and replicates (D2): {gstat('D2')}; generator checks (D3): {gstat('D3')}; contrasts recomputed (D4): {gstat('D4')}; replicate reproduced from scratch (E3): {gstat('E3')}; **stop rule 2 / negative control A** (π = 0 identical, G2): {gstat('G2')}.

## Outputs and reproduction
`results/exp4/` (runs.csv.gz, contrasts.csv, calibration.json), `results/analysis/figures/fig3_exp4_dose_response.png`. Reproduce:
{run_cmd}
"""
    (reports / "EXP4_REPORT.md").write_text(exp4_md, encoding="utf-8")

    # ----- Full run report
    cfg_hash = {f: sha(HERE / "configs" / f)[:16] for f in ("exp1_pima.yaml", "exp2_canary.yaml", "exp4_simulation.yaml")}
    env_path = HERE / "environment/environment.json"
    env = json.loads(env_path.read_text(encoding="utf-8")) if env_path.exists() else {}
    audit_rows = pd.DataFrame([{"check": c["id"], "result": "PASS" if c["passed"] else "FAIL", "description": c["description"]} for c in audit["checks"]]) if audit else pd.DataFrame()
    full = f"""{banner}# FULL_RUN_REPORT — label-aware imputation leakage (pre-registered study, prereg-v1)

*Research-stage report. No manuscript has been drafted. Executing the experiments and passing the engineering gates is not the same as confirming the hypotheses; the hypothesis outcomes are stated separately in section 4.*

## 1. Experiment completion status
| Experiment | Planned | Completed | Measured wall time | Exit |
|---|---|---|---|---|
| Exp 1 (real Pima) | {J} splits × {len(cfg1['regimes'])} regimes × {len(cfg1['models'])} models | {len(M) // 2} fitted models ({len(M)} evaluations) | {rt['exp1']['seconds_wall']:.0f} s | {gstat('A4_exp1')} |
| Exp 2 (canary) | {cfg2['n_splits_used']} splits × {cfg2['n_perm']} permutations × {len(cfg2['regimes'])} × {len(cfg2['models'])} | {len(PA)} fits | {rt['exp2']['seconds_wall']:.0f} s | {gstat('A4_exp2')} |
| Exp 4 (simulation) | full grid, {cfg4['reps']} replicates | {len(R4)} runs | {rt['exp4']['seconds_wall']:.0f} s | {gstat('A4_exp4')} |
| Exp 3 (diagnostics) | derived from Exp 1 | computed | negligible | — |
| Exp 5 (published pipelines) | conditional on full-text reading | **not run** | — | — |
| Reg-4 (pseudo-label, exploratory) | excluded from confirmatory configs | **not run** | — | — |

Wall times are from log-file timestamps; the three runs were executed concurrently on one 12-thread machine, so each includes CPU contention.

## 2. Audit results (G6)
{md_table(audit_rows) if not audit_rows.empty else '(test mode)'}

## 3. Main findings (restricted to what the pre-registered rules decide)
- **H1 (primary):** {h1['status']}. Apparent ROC-AUC inflation of RF-default under Reg-3 vs Reg-0 was {ci_str(h1, 'h1')} against a smallest effect of interest of {SESOI}.
- **H2:** {h2['status']} (E1 RF-default − LR: {ci_str(h2, 'h2')}).
- **H3:** {h3['status']}; **H4:** {h4['status']}; **H5 (simulation):** {H5['status']}; **H6 (canary):** {D2['status']}.
- H7 (importance share and calibration) is exploratory; see `results/analysis/exp3_diagnostic_contrasts.csv`.
- Logistic regression and other models: all per-model contrasts are in `exp1_contrasts_all_metrics.csv`; whether an effect for a given model clears the SESOI must be read from its corrected CI, not inferred from the point estimate.

## 4. Pre-registered contrast results
{md_table(pd.DataFrame(rows))}

Method: per-split paired differences of held-out ROC-AUC (same splits for every regime and model); mean with Nadeau–Bengio corrected 95% CI, `Var = (1/J + n_test/n_train)·s²`, `J = {J}`, `n_train = {n_train}`, `n_test = {n_test}`, t with J−1 degrees of freedom. Decision rules are those of `PREREG_DRAFT.md` §4 as operationalised in `leakage_study/analysis.py`.

## 5. Stop-rule outcomes
1. Reg-0 permuted-label AUC within 0.5 ± 0.02 (all models): **{gstat('G1')}**
2. Negative control A (π = 0, all regimes identical): **{gstat('G2')}**
3. Negative control B (real complete cases, all regimes identical): **{gstat('G3')}**
4. Unit tests for label/scope isolation etc.: **{gstat('G4')}**
5. All metrics recomputable from saved predictions: **{gstat('G5')}**

## 6. Limitations and unresolved questions
- One real dataset (768 rows); fixed, untuned models; the regimes emulate the *described* practice and are not the authors' code. No claim is made that any published study is wrong.
- Corrected CIs on real data are wide relative to small effects (dominated by n_test/n_train); an effect below the SESOI for a model such as logistic regression may remain inconclusive.
- The Pima outcome's timing relative to the predictors is unresolved (Smith 1988 not yet read); the target is treated as recorded diabetes status.
- Full texts of the three studies that describe group-median imputation have not yet been read; Exp 5 is not run and no new regime has been introduced.
- Simulation uses a synthetic generator (Gaussian features, logistic outcome); results show mechanism and dose–response, not clinical performance.
- The pilot informed the SESOI and regime definitions (disclosed in the pre-registration).

## 7. Commands to reproduce
{run_cmd}

## 8. Paths to the underlying artifacts
Predictions: `results/exp1/predictions.csv.gz`; metrics: `results/exp1/metrics.csv`, `results/exp2/`, `results/exp4/`; logs: `results/*/run.log`; audit: `results/audit/AUDIT_G6.json|md`; analysis tables: `results/analysis/`; figures: `results/analysis/figures/` (data files in `figures/data/`); per-experiment reports: `reports/`.

## 9. Git commit and configuration identifiers
- Pre-registration tag `prereg-v1` (commit {git('rev-list', '-n', '1', 'prereg-v1')[:10]}); code tag `leakage-code-v0.1.1` (commit {git('rev-list', '-n', '1', 'leakage-code-v0.1.1')[:10]}); analysis/audit code tag `analysis-code-v1` (commit {git('rev-list', '-n', '1', 'analysis-code-v1')[:10] if git('tag', '-l', 'analysis-code-v1') else 'not tagged'}); HEAD at analysis: {git('rev-parse', 'HEAD')[:10]}.
- Master seed {cfg1['master_seed']}; config file hashes (sha256, first 16): {json.dumps(cfg_hash)}.
- Environment: Python {env.get('python', '?')}, scikit-learn {env.get('packages', {}).get('scikit-learn', '?')}, numpy {env.get('packages', {}).get('numpy', '?')}, pandas {env.get('packages', {}).get('pandas', '?')}; record: `environment/environment.json`; lock file `environment/requirements.lock.txt`; data SHA-256 {env.get('data_sha256', '?')[:16]}….

## 10. Deviations from the frozen protocol
- **Code:** `leakage-code-v0.1` → `v0.1.1` replaced a deprecated scikit-learn argument (`penalty=None` → `C=np.inf`); numerically identical; done before any full run.
- **Concurrency:** Exp 1, 2 and 4 were run at the same time (affects wall-clock only; outputs are independent of worker count and were verified reproducible).
- **Analysis and audit code** (`analysis.py`, `audit_g6.py`, `analyze.py`, `verify_report.py`) were written after the freeze but **before any full-run result was inspected**, then committed and tagged `analysis-code-v1`.
- **Operationalisations of the frozen plan** (fixed before unblinding; the plan's wording left room): H1 three-way rule on the corrected CI; H2, H3, H4 as written in `leakage_study/analysis.py`; H5 requires mean inflation within ±0.005 at π = 0 and non-decreasing means in π for RF-default and HGB; H6 "flexible" = RF-default, RF-regularised, HGB; Holm-adjusted p-values (supplementary) come from one-sided Nadeau–Bengio t-tests against the stated bounds; the plan did not specify how to form p-values.
- **Frozen-code labelling defect (derived output only):** `experiments.sim_contrasts` overwrites the simulation dataset size `n` with the replicate count in `results/exp4/contrasts.csv`. Found by the independent report verifier on toy data before any full-run inspection. The frozen code was **not** modified; all reported Exp 4 analysis uses `analysis.sim_contrasts_correct` recomputed from the raw `runs.csv.gz`. Raw runs and per-cell statistics are unaffected (audit check D5 verifies this).
- **Not run:** Exp 5 and Reg-4 (as stated in the plan).
- **Audit-detected discrepancies:** {'none' if audit and audit['all_pass'] else 'see section 2'}.
"""
    (reports / "FULL_RUN_REPORT.md" if test_mode else HERE / "FULL_RUN_REPORT.md").write_text(full, encoding="utf-8")
    (out / "report_numbers.json").write_text(json.dumps(NUM, indent=1), encoding="utf-8")
    print("analysis complete ->", out, "| reports ->", reports, "| numbers registered:", len(NUM))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(HERE / "results"))
    ap.add_argument("--out", default=str(HERE / "results" / "analysis"))
    ap.add_argument("--reports", default=str(HERE / "reports"))
    ap.add_argument("--n-total", type=int, default=768)
    ap.add_argument("--test-mode", action="store_true")
    a = ap.parse_args()
    main(Path(a.results), Path(a.out), Path(a.reports), a.n_total, a.test_mode)
