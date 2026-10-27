"""Pre-registered G6 consistency audit. Run AFTER all full runs have finished. Writes results/audit/AUDIT_G6.json and .md.
Nothing is marked as passed without recorded evidence. Run from research/leakage_study:
  ..\\..\\.venv\\Scripts\\python scripts\\audit_g6.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from leakage_study.analysis import sim_contrasts_correct  # noqa: E402
from leakage_study.canary import canary_flags, permuted_label_aucs  # noqa: E402
from leakage_study.data import complete_case_mask, load_pima  # noqa: E402
from leakage_study.experiments import contrast_table, sim_contrasts, sim_replicate  # noqa: E402
from leakage_study.metrics import KEYS, summarise  # noqa: E402
from leakage_study.runner import run_grid  # noqa: E402
from leakage_study.simulate import calibrate, estimate_corr  # noqa: E402
from leakage_study.splits import make_splits  # noqa: E402

RES = HERE / "results"
OUT = RES / "audit"
SEED = 20261027
TAG = "leakage-code-v0.1.1"
checks: list[dict] = []


def rec(cid: str, desc: str, ok: bool, evidence) -> bool:
    checks.append({"id": cid, "description": desc, "passed": bool(ok), "evidence": evidence})
    print(("PASS " if ok else "FAIL ") + cid + ": " + desc)
    return ok


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=120).stdout.strip()


def frame_equal(a: pd.DataFrame, b: pd.DataFrame, atol: float = 1e-12) -> tuple[bool, str]:
    try:
        pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True), check_exact=False, atol=atol, rtol=0)
        return True, "frames equal within atol"
    except AssertionError as e:
        return False, str(e)[:300]


# ------------------------------------------------------------------ A. provenance and frozen configuration
tracked = ["research/leakage_study/leakage_study", "research/leakage_study/configs", "research/leakage_study/scripts/run.py"]
ALLOWED_NEW = {"research/leakage_study/leakage_study/analysis.py"}   # analysis-only module added after the runs started; imported by no run
diff_files = [f for f in git("diff", "--name-only", TAG, "HEAD", "--", *tracked).splitlines() if f]
dirty = git("status", "--porcelain", "--", *tracked)
unexpected = sorted(set(diff_files) - ALLOWED_NEW)
rec("A1", f"Experiment code and configs identical to tag {TAG} (only the analysis-only module analysis.py may differ; no uncommitted changes)", not unexpected and dirty == "",
    {"head": git("rev-parse", "HEAD"), "tag_commit": git("rev-list", "-n", "1", TAG), "differing_files": diff_files, "unexpected_differences": unexpected, "dirty": dirty})

freeze = (ROOT / "research/stage6/PREREG_FREEZE.txt").read_text(encoding="utf-8").splitlines()
recorded = {ln.split()[1]: ln.split()[0] for ln in freeze if len(ln.split()) == 2 and len(ln.split()[0]) == 64}
now = {f: sha(ROOT / "research/stage6" / f) for f in recorded}
at_tag = {f: hashlib.sha256(subprocess.run(["git", "show", f"prereg-v1:research/stage6/{f}"], cwd=ROOT, capture_output=True, timeout=60).stdout).hexdigest() for f in recorded}
rec("A2", "Frozen pre-registration files unchanged (hash now == hash in freeze record == hash at tag prereg-v1)", now == recorded == at_tag, {"recorded": recorded, "now": now, "at_tag": at_tag})

cfg_ev, cfg_ok = {}, True
for exp, fn in (("exp1", "exp1_pima.yaml"), ("exp2", "exp2_canary.yaml"), ("exp4", "exp4_simulation.yaml")):
    working = yaml.safe_load((HERE / "configs" / fn).read_text(encoding="utf-8"))
    at = yaml.safe_load(subprocess.run(["git", "show", f"{TAG}:research/leakage_study/configs/{fn}"], cwd=ROOT, capture_output=True, text=True).stdout)
    used = json.loads((RES / exp / "run_config.json").read_text(encoding="utf-8"))["config"]
    same = working == at == used and used["master_seed"] == SEED
    cfg_ok &= same
    cfg_ev[exp] = {"config_used_equals_tag_and_working": same, "master_seed": used["master_seed"]}
rec("A3", f"Config used by each full run equals the frozen config at {TAG}; master seed == {SEED}", cfg_ok, cfg_ev)

for exp in ("exp1", "exp2", "exp4"):
    log = (RES / exp / "run.log").read_text(encoding="utf-8", errors="replace").strip().splitlines()
    rec(f"A4_{exp}", f"{exp} run log ends with exit 0 (no recorded failure)", log[-1].strip() == "exit 0", {"last_line": log[-1] if log else None})

# ------------------------------------------------------------------ B. Exp 1 (real Pima)
X, y = load_pima()
c1 = yaml.safe_load((HERE / "configs/exp1_pima.yaml").read_text(encoding="utf-8"))
splits = make_splits(y, c1["n_splits"], SEED, c1["test_size"])
P = pd.read_csv(RES / "exp1/predictions.csv.gz")
M1 = pd.read_csv(RES / "exp1/metrics.csv")
n_groups = c1["n_splits"] * len(c1["regimes"]) * len(c1["models"]) * 2
g = P.groupby(KEYS).size()
rec("B1", f"Exp 1: {n_groups} (split, regime, model, eval) groups, each with {len(splits[0].test_idx)} held-out rows", len(g) == n_groups and bool((g == len(splits[0].test_idx)).all()),
    {"groups": int(len(g)), "expected": n_groups, "rows": int(len(P)), "min_rows_per_group": int(g.min()), "max_rows_per_group": int(g.max())})
rec("B2", "Exp 1: no duplicated (split, regime, model, eval, row) records", int(P.duplicated(["split", "regime", "model", "eval", "row"]).sum()) == 0, {"duplicates": int(P.duplicated(["split", "regime", "model", "eval", "row"]).sum())})
rec("B3", "Exp 1: no missing predictions; all probabilities in [0, 1]", bool(P["p"].notna().all() and P["p"].between(0, 1).all()), {"nan": int(P["p"].isna().sum()), "min": float(P["p"].min()), "max": float(P["p"].max())})
rec("B4", "Exp 1: saved outcome labels equal the source data for every saved row", bool((P["y"].to_numpy() == y[P["row"].to_numpy()]).all()), {"checked_rows": int(len(P))})
bad_split, bad_prev = [], []
for s in splits:
    sub = P[P["split"] == s.index]
    for _, gg in sub.groupby(["regime", "model", "eval"]):
        if not np.array_equal(np.sort(gg["row"].to_numpy()), s.test_idx):
            bad_split.append(s.index)
            break
    if not np.allclose(sub["train_prev"].to_numpy(), float(y[s.train_idx].mean()), atol=1e-12):
        bad_prev.append(s.index)
rec("B5", "Exp 1: saved held-out rows of every split equal the splits regenerated from SeedSequence(20261027).spawn(100); train prevalence matches", not bad_split and not bad_prev,
    {"splits_checked": len(splits), "mismatching_row_sets": bad_split, "mismatching_train_prev": bad_prev,
     "disjoint_and_complete": all(len(set(s.train_idx) & set(s.test_idx)) == 0 and len(s.train_idx) + len(s.test_idx) == len(y) for s in splits)})
rec("B6", "Exp 1: regimes and models present are exactly those in the frozen config", set(P["regime"]) == set(c1["regimes"]) and set(P["model"]) == set(c1["models"]), {"regimes": sorted(set(P["regime"])), "models": sorted(set(P["model"]))})
ok, msg = frame_equal(summarise(P), M1)
rec("B7", "Exp 1: metrics.csv recomputed from the saved per-row predictions (summarise) equals the saved metrics (atol 1e-12)", ok, {"result": msg, "rows": int(len(M1))})
ct = pd.read_csv(RES / "exp1/contrasts.csv")
ok, msg = frame_equal(contrast_table(M1, len(splits[0].train_idx), len(splits[0].test_idx)), ct)
rec("B8", "Exp 1: contrasts.csv recomputed from metrics equals the saved contrasts", ok, {"result": msg, "rows": int(len(ct))})
imp = pd.read_csv(RES / "exp1/importance.csv")
exp_imp = c1["n_splits"] * len(c1["regimes"]) * len(c1["importance_models"]) * 8
rec("B9", f"Exp 1: importance table has {exp_imp} rows (splits x regimes x importance models x 8 features) with no missing values", len(imp) == exp_imp and bool(imp["importance"].notna().all()), {"rows": int(len(imp))})
tm = pd.read_csv(RES / "exp1/timing.csv")
rec("B10", f"Exp 1: timing table has {c1['n_splits'] * len(c1['regimes']) * len(c1['models'])} fitted tasks", len(tm) == c1["n_splits"] * len(c1["regimes"]) * len(c1["models"]), {"rows": int(len(tm)), "total_task_seconds": float(tm[["fit_s", "importance_s"]].sum().sum())})

# reproduce cells from scratch (fresh process state, fresh splits)
t0 = time.perf_counter()
sel = [0, 37, 99]
sub_splits = [splits[i] for i in sel]
Pn, _, _ = run_grid(X, y, sub_splits, ["Reg-0", "Reg-3"], ["LR", "RF-default", "HGB"], n_jobs=1)
saved = P[P["split"].isin(sel) & P["regime"].isin(["Reg-0", "Reg-3"]) & P["model"].isin(["LR", "RF-default", "HGB"])].sort_values(["split", "regime", "model", "eval", "row"], kind="mergesort").reset_index(drop=True)
Pn = Pn.sort_values(["split", "regime", "model", "eval", "row"], kind="mergesort").reset_index(drop=True)
same = len(saved) == len(Pn) and np.array_equal(saved["p"].to_numpy(), Pn["p"].to_numpy())
rec("E1", "Reproduced Exp 1 cells from scratch (splits 0, 37, 99; Reg-0 and Reg-3; LR, RF-default, HGB): predictions bit-identical to the saved ones", same,
    {"rows_compared": int(len(saved)), "max_abs_diff": float(np.abs(saved["p"].to_numpy() - Pn["p"].to_numpy()).max()) if len(saved) == len(Pn) else None, "seconds": round(time.perf_counter() - t0, 1)})

# ------------------------------------------------------------------ C. Exp 2 (canary)
c2 = yaml.safe_load((HERE / "configs/exp2_canary.yaml").read_text(encoding="utf-8"))
PA = pd.read_csv(RES / "exp2/permuted_auc.csv.gz")
exp_rows = c2["n_splits_used"] * len(c2["regimes"]) * len(c2["models"]) * c2["n_perm"]
keys2 = ["split", "regime", "model", "perm"]
rec("C1", f"Exp 2: {exp_rows} (split, regime, model, permutation) records, no duplicates, no missing AUC",
    len(PA) == exp_rows and int(PA.duplicated(keys2).sum()) == 0 and bool(PA["auc"].notna().all()), {"rows": int(len(PA)), "duplicates": int(PA.duplicated(keys2).sum()), "nan": int(PA["auc"].isna().sum())})
rec("C2", "Exp 2: splits used are exactly the first n_splits_used splits of the Exp 1 split list", sorted(PA["split"].unique().tolist()) == list(range(c2["n_splits_used"])), {"splits": sorted(PA["split"].unique().tolist())})
fl = pd.read_csv(RES / "exp2/flags.csv")
det = pd.read_csv(RES / "exp2/detection.csv")
ok1, m1 = frame_equal(canary_flags(PA).sort_values(["model", "regime", "split"]), fl.sort_values(["model", "regime", "split"]))
rec("C3", "Exp 2: canary flags recomputed from the saved permuted AUCs equal the saved flags", ok1, {"result": m1})
t0 = time.perf_counter()
rows = permuted_label_aucs(X, y, splits[4], "Reg-3", "RF-default", 10, SEED)
saved_c = PA[(PA["split"] == 4) & (PA["regime"] == "Reg-3") & (PA["model"] == "RF-default") & (PA["perm"] < 10)].sort_values("perm")
rec("E2", "Reproduced Exp 2 cell from scratch (split 4, Reg-3, RF-default, permutations 0-9): AUCs bit-identical", np.array_equal(saved_c["auc"].to_numpy(), np.array([r["auc"] for r in rows])),
    {"max_abs_diff": float(np.abs(saved_c["auc"].to_numpy() - np.array([r["auc"] for r in rows])).max()), "seconds": round(time.perf_counter() - t0, 1)})

# ------------------------------------------------------------------ D. Exp 4 (simulation)
import itertools  # noqa: E402

c4 = yaml.safe_load((HERE / "configs/exp4_simulation.yaml").read_text(encoding="utf-8"))
R4 = pd.read_csv(RES / "exp4/runs.csv.gz")
cells = list(itertools.product(c4["pi"], c4["mechanism"], c4["target_auc"], c4["n"]))
exp4_rows = len(cells) * c4["reps"] * len(c4["regimes"]) * len(c4["models"])
keys4 = ["cell", "rep", "regime", "model"]
rec("D1", f"Exp 4: {exp4_rows} runs = {len(cells)} cells x {c4['reps']} replicates x {len(c4['regimes'])} regimes x {len(c4['models'])} models; no duplicates; no missing values",
    len(R4) == exp4_rows and int(R4.duplicated(keys4).sum()) == 0 and bool(R4[["auc_app", "auc_dep", "auc_truth"]].notna().all().all()),
    {"rows": int(len(R4)), "duplicates": int(R4.duplicated(keys4).sum())})
per_cell = R4.groupby("cell")["rep"].nunique()
grid_ok = all(len(R4[R4["cell"] == i]) > 0 and R4[R4["cell"] == i]["pi"].iloc[0] == c[0] and R4[R4["cell"] == i]["mechanism"].iloc[0] == c[1] and R4[R4["cell"] == i]["target_auc"].iloc[0] == c[2] and R4[R4["cell"] == i]["n"].iloc[0] == c[3] for i, c in enumerate(cells))
rec("D2", "Exp 4: each cell has the configured parameters and exactly the configured number of replicates", grid_ok and bool((per_cell == c4["reps"]).all()), {"cells": int(R4["cell"].nunique()), "replicates_per_cell_min_max": [int(per_cell.min()), int(per_cell.max())]})
o = R4.groupby("cell")[["oracle_auc_truth", "target_auc"]].mean()
mf = R4[R4["regime"] == "Reg-0"].groupby("cell").agg(miss=("miss_frac_high", "mean"), pi=("pi", "first"))
rec("D3", "Exp 4: oracle AUC of the truth sample within 0.015 of the target in every cell; mean missing fraction of the high-missing feature within 0.04 of pi (MCAR/MNAR); exactly 0 when pi = 0",
    bool((o["oracle_auc_truth"] - o["target_auc"]).abs().max() < 0.015) and bool((mf["miss"] - mf["pi"]).abs().max() < 0.04) and bool((mf[mf["pi"] == 0]["miss"] == 0).all()),
    {"max_abs_oracle_gap": float((o["oracle_auc_truth"] - o["target_auc"]).abs().max()), "max_abs_missing_gap": float((mf["miss"] - mf["pi"]).abs().max())})
ct4 = pd.read_csv(RES / "exp4/contrasts.csv")
ok, msg = frame_equal(sim_contrasts(R4), ct4)
rec("D4", "Exp 4: contrasts recomputed from the saved runs equal the saved contrasts", ok, {"result": msg, "rows": int(len(ct4))})
corrected = sim_contrasts_correct(R4)
cols_same = ["cell", "pi", "mechanism", "target_auc", "model", "contrast", "mean", "sd", "lo", "hi"]
ok_a, msg_a = frame_equal(corrected[cols_same].sort_values(cols_same[:6]).reset_index(drop=True), ct4[cols_same].sort_values(cols_same[:6]).reset_index(drop=True))
n_defect = bool((ct4["n"] == c4["reps"]).all()) and set(corrected["n"]) == set(c4["n"])
rec("D5", "Exp 4: documented labelling defect confirmed and contained: saved contrasts.csv has n == replicate count, but every other column equals the corrected recomputation from raw runs", ok_a and n_defect,
    {"other_columns_equal": ok_a, "saved_n_values": sorted(set(ct4["n"].tolist())), "true_n_values": sorted(set(corrected["n"].tolist())), "result": msg_a})
t0 = time.perf_counter()
corr = estimate_corr(X)
cid = next(i for i, c in enumerate(cells) if c == (0.5, "MNAR", 0.80, 768))
rep = 7
params = calibrate(corr, 0.80, c4.get("prevalence", 0.35))
sq = np.random.SeedSequence([SEED, 4, cid]).spawn(c4["reps"])[rep]
new = pd.DataFrame(sim_replicate(params, 768, 0.5, "MNAR", c4["models"], c4["regimes"], sq, c4["truth_n"], cid, rep)).sort_values(["regime", "model"]).reset_index(drop=True)
old = R4[(R4["cell"] == cid) & (R4["rep"] == rep)].sort_values(["regime", "model"]).reset_index(drop=True)
cols = ["auc_app", "auc_dep", "auc_truth", "brier_app", "brier_truth", "oracle_auc_truth"]
rec("E3", f"Reproduced Exp 4 replicate from scratch (cell {cid}: pi=0.5, MNAR, AUC 0.8, n=768; replicate {rep}): all AUC/Brier values bit-identical",
    len(old) == len(new) and all(np.array_equal(old[c].to_numpy(), new[c].to_numpy()) for c in cols),
    {"max_abs_diff": float(max(np.abs(old[c].to_numpy() - new[c].to_numpy()).max() for c in cols)), "seconds": round(time.perf_counter() - t0, 1)})

# ------------------------------------------------------------------ F. stop-rule gates on the actual full-run results
ref = PA[PA["regime"] == "Reg-0"].groupby("model")["auc"].mean()
rec("G1", "Stop rule 1: Reg-0 permuted-label AUC mean within 0.5 +/- 0.02 for every model (Exp 2 full run)", bool(((ref - 0.5).abs() <= 0.02).all()), {k: round(float(v), 4) for k, v in ref.items()})
z = R4[R4["pi"] == 0.0].pivot_table(index=["cell", "rep", "model"], columns="regime", values=["auc_app", "auc_dep", "auc_truth", "brier_app", "brier_truth"])
dmax = max(float(z[m].sub(z[m]["Reg-0"], axis=0).abs().to_numpy().max()) for m in ["auc_app", "auc_dep", "auc_truth", "brier_app", "brier_truth"])
rec("G2", "Stop rule 2 / negative control A: simulation with pi = 0 -> all regimes identical (max |difference| < 1e-9)", dmax < 1e-9, {"max_abs_difference": dmax, "runs_checked": int((R4["pi"] == 0.0).sum())})
t0 = time.perf_counter()
cc = complete_case_mask(X)
Xc, yc = X[cc], y[cc]
Pc, _, _ = run_grid(Xc, yc, make_splits(yc, c1["n_splits"], SEED, c1["test_size"]), c1["regimes"], c1["models"], n_jobs=4)
wide = Pc.pivot_table(index=["split", "model", "eval", "row"], columns="regime", values="p")
d3 = float(wide.sub(wide["Reg-0"], axis=0).abs().to_numpy().max())
rec("G3", f"Stop rule 3 / negative control B: real complete-case Pima (n = {int(cc.sum())}), 100 splits, 5 models -> all regimes identical (max |difference| = 0)", d3 == 0.0,
    {"n_complete_cases": int(cc.sum()), "predictions_compared": int(len(Pc)), "max_abs_difference": d3, "seconds": round(time.perf_counter() - t0, 1)})
t0 = time.perf_counter()
pt = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"], cwd=HERE, capture_output=True, text=True, timeout=3000)
rec("G4", "Stop rule 4: study test suite (label/scope isolation, controls, simulation, analysis rules) passes against the audited code", pt.returncode == 0, {"last_line": pt.stdout.strip().splitlines()[-1], "seconds": round(time.perf_counter() - t0, 1)})
rec("G5", "Stop rule 5: every reported metric is recomputable from the saved per-row predictions (see B7, B8; C3; D4)", all(c["passed"] for c in checks if c["id"] in ("B7", "B8", "C3", "D4")), {"depends_on": ["B7", "B8", "C3", "D4"]})

# ------------------------------------------------------------------ G. measured runtimes and file hashes
runtimes = {}
for exp in ("exp1", "exp2", "exp4"):
    log = RES / exp / "run.log"
    st = os.stat(log)
    runtimes[exp] = {"seconds_wall": round(st.st_mtime - st.st_ctime, 1), "method": "log file creation time to last modification time; the three experiments ran concurrently on one machine, so each wall time includes CPU contention"}
runtimes["exp1_total_task_seconds_serial"] = float(tm[["fit_s", "importance_s"]].sum().sum())
files = {str(p.relative_to(HERE)): sha(p) for exp in ("exp1", "exp2", "exp4") for p in sorted((RES / exp).glob("*")) if p.is_file() and p.name != "run.log"}
summary = {"audited_utc": datetime.now(UTC).isoformat(timespec="seconds"), "git_head": git("rev-parse", "HEAD"), "code_tag": TAG, "all_pass": all(c["passed"] for c in checks),
           "n_checks": len(checks), "n_failed": sum(not c["passed"] for c in checks), "runtimes": runtimes, "result_file_sha256": files, "checks": checks}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "AUDIT_G6.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
md = ["# G6 consistency audit", "", f"Audited {summary['audited_utc']} · code tag `{TAG}` · HEAD `{summary['git_head'][:10]}` · **{'ALL CHECKS PASSED' if summary['all_pass'] else 'FAILURES PRESENT'}** ({summary['n_checks']} checks, {summary['n_failed']} failed)", "",
      "| Check | Result | Description |", "|---|---|---|"]
md += [f"| {c['id']} | {'PASS' if c['passed'] else '**FAIL**'} | {c['description']} |" for c in checks]
(OUT / "AUDIT_G6.md").write_text("\n".join(md), encoding="utf-8")
print("\nALL PASS" if summary["all_pass"] else "\nFAILURES: " + ", ".join(c["id"] for c in checks if not c["passed"]))
sys.exit(0 if summary["all_pass"] else 1)
