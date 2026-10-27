"""Verify that every number in the generated reports agrees with the saved artifacts.
Independent of leakage_study.stats/analysis: re-derives the registered numbers from raw predictions with its own code.
Run after analyze.py:  ..\\..\\.venv\\Scripts\\python scripts\\verify_report.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parents[1]


def nb(d: np.ndarray, n_train: int, n_test: int) -> dict:
    d = np.asarray(d, float)
    j = len(d)
    var = d.var(ddof=1)
    se = math.sqrt((1 / j + n_test / n_train) * var)
    t = sps.t.ppf(0.975, j - 1)
    return {"mean": d.mean(), "lo": d.mean() - t * se, "hi": d.mean() + t * se, "se": se, "J": j}


def p_greater(d: np.ndarray, n_train: int, n_test: int, null: float = 0.0) -> float:
    c = nb(d, n_train, n_test)
    return float(1 - sps.t.cdf((c["mean"] - null) / c["se"], c["J"] - 1))


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(ps) - rank) * ps[i])
        out[i] = min(1.0, run)
    return out


def main(res: Path, reports: Path, out: Path, n_total: int) -> int:
    num = json.loads((out / "report_numbers.json").read_text(encoding="utf-8"))
    files = sorted(reports.glob("*.md"))
    if reports.resolve() == (HERE / "reports").resolve():
        files.append(HERE / "FULL_RUN_REPORT.md")
    text = "\n".join(p.read_text(encoding="utf-8") for p in files)
    results: list[dict] = []

    def check(name: str, expected, key: str | None = None, tol: float = 1e-9) -> None:
        rec = num.get(key) if key else None
        ok = rec is not None and abs(float(rec["value"]) - float(expected)) <= tol
        shown = rec is not None and rec["text"] in text
        results.append({"check": name, "key": key, "registered": rec["value"] if rec else None, "recomputed": float(expected), "value_agrees": bool(ok), "text_in_report": bool(shown), "pass": bool(ok and shown)})

    P = pd.read_csv(res / "exp1/predictions.csv.gz")
    auc = P.groupby(["split", "regime", "model", "eval"]).apply(lambda g: roc_auc_score(g["y"], g["p"]), include_groups=False).rename("auc").reset_index()
    n_test = int(P.groupby(["split", "regime", "model", "eval"]).size().iloc[0])
    n_train = n_total - n_test
    piv = auc.pivot_table(index=["split", "model"], columns=["regime", "eval"], values="auc")
    s = lambda m, a, b: (piv.xs(m, level="model")[a] - piv.xs(m, level="model")[b]).to_numpy()  # noqa: E731

    check("Exp 1 groups", P.groupby(["split", "regime", "model", "eval"]).ngroups, "exp1_groups")
    check("Exp 1 fitted models", P.groupby(["split", "regime", "model"]).ngroups, "exp1_fits")
    e_rf = s("RF-default", ("Reg-3", "app"), ("Reg-0", "app"))
    e_lr = s("LR", ("Reg-3", "app"), ("Reg-0", "app"))
    for tag, arr in (("h1", e_rf), ("h2", e_rf - e_lr)):
        c = nb(arr, n_train, n_test)
        for k in ("mean", "lo", "hi"):
            check(f"{tag} {k}", c[k], f"{tag}_{k}")
    label = s("RF-default", ("Reg-2", "app"), ("Reg-0", "app"))
    scope = s("RF-default", ("Reg-1", "app"), ("Reg-0", "app"))
    inter = (s("RF-default", ("Reg-3", "app"), ("Reg-2", "app")) - scope)
    for tag, arr in (("h3", label - scope), ("h3i", inter)):
        c = nb(arr, n_train, n_test)
        for k in ("mean", "lo", "hi"):
            check(f"{tag} {k}", c[k], f"{tag}_{k}")
    gaps = {r: s("RF-default", (r, "app"), (r, "dep")) for r in ("Reg-0", "Reg-1", "Reg-2", "Reg-3")}
    for r, arr in gaps.items():
        c = nb(arr, n_train, n_test)
        for k in ("mean", "lo", "hi"):
            check(f"h4 {r} gap {k}", c[k], f"h4r{r[-1]}_{k}")
    fam = [p_greater(e_rf - e_lr, n_train, n_test), p_greater(label - scope, n_train, n_test), p_greater(gaps["Reg-2"], n_train, n_test, 0.02), p_greater(gaps["Reg-3"], n_train, n_test, 0.02)]
    for name, v in zip(["H2", "H3", "H4_Reg-2", "H4_Reg-3"], holm(fam), strict=True):
        check(f"Holm adjusted p {name}", v, f"holm_{name}")

    PA = pd.read_csv(res / "exp2/permuted_auc.csv.gz")
    check("Exp 2 fits", len(PA), "exp2_rows")
    for m, v in PA[PA["regime"] == "Reg-0"].groupby("model")["auc"].mean().items():
        check(f"Reg-0 permuted AUC mean {m}", v, f"ref0_{m}")

    R4 = pd.read_csv(res / "exp4/runs.csv.gz")
    check("Exp 4 runs", len(R4), "exp4_rows")
    w = R4.pivot_table(index=["n", "mechanism", "target_auc", "model", "pi", "rep"], columns="regime", values="auc_app").reset_index()
    w["e1"] = w["Reg-3"] - w["Reg-0"]
    mean_e1 = w.groupby(["n", "mechanism", "target_auc", "model", "pi"])["e1"].mean().reset_index().sort_values("pi")
    zero_bad = mono_bad = 0
    for (_, _, _, model), g in mean_e1.groupby(["n", "mechanism", "target_auc", "model"]):
        if abs(g[g["pi"] == 0.0]["e1"].iloc[0]) > 0.005:
            zero_bad += 1
        if model in ("RF-default", "HGB") and not np.all(np.diff(g["e1"].to_numpy()) >= 0):
            mono_bad += 1
    check("H5 pi=0 violations", zero_bad, "h5_pi0_viol")
    check("H5 monotonicity violations (RF-default, HGB)", mono_bad, "h5_mono_viol")

    aud = res / "audit" / "AUDIT_G6.json"
    if aud.exists():
        rt = json.loads(aud.read_text(encoding="utf-8"))["runtimes"]
        for e in ("exp1", "exp2", "exp4"):
            check(f"measured runtime {e}", rt[e]["seconds_wall"], f"rt_{e}", tol=0.51)

    registered_unchecked = sorted(set(num) - {r["key"] for r in results})
    summary = {"n_checks": len(results), "n_failed": sum(not r["pass"] for r in results), "registered_numbers": len(num), "registered_but_not_independently_rederived": registered_unchecked, "checks": results}
    (out / "REPORT_VERIFICATION.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(f"{summary['n_checks'] - summary['n_failed']}/{summary['n_checks']} report numbers verified; {len(registered_unchecked)} registered numbers not independently re-derived")
    for r in results:
        if not r["pass"]:
            print("FAIL", r)
    return 0 if summary["n_failed"] == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(HERE / "results"))
    ap.add_argument("--reports", default=str(HERE / "reports"))
    ap.add_argument("--out", default=str(HERE / "results" / "analysis"))
    ap.add_argument("--n-total", type=int, default=768)
    a = ap.parse_args()
    sys.exit(main(Path(a.results), Path(a.reports), Path(a.out), a.n_total))
