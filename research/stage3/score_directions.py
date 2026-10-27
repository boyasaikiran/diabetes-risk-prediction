"""Stage 3 scoring of candidate research directions (A-H) with an explicit rubric and weight-sensitivity check.
Scores are my judgements from the Stage 2/3 evidence (abstract-level); they are transparent so you can challenge them."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

CRITERIA = [  # key, label, baseline weight, what a 5 means
    ("gap", "Evidence that a gap exists", 15, "Searches found no study doing this; reasons to expect a real gap"),
    ("overlap", "Low overlap with existing work", 20, "No close prior publication found (5) ... several close works (1)"),
    ("importance", "Scientific importance", 10, "Changes how the community should evaluate/interpret results"),
    ("feasible", "Technical feasibility", 10, "Doable with existing code and data"),
    ("compute", "Low computational cost", 5, "Minutes on a laptop CPU"),
    ("data", "Low extra-data requirement", 5, "No new dataset needed"),
    ("stats", "Statistical validity achievable", 10, "Clear design supports credible inference despite n = 768"),
    ("risk", "Low risk of inconclusive/trivial result", 10, "Result informative whichever way it falls"),
    ("student", "Suitability for a student conference paper", 5, "Scope fits a short paper"),
    ("method", "Methodological (not merely applied) contribution", 10, "Contributes a protocol, diagnostic or evaluation method"),
]
KEYS = [c[0] for c in CRITERIA]

D = {  # direction: (name, scores in KEYS order, notes)
    "A": ("Calibration-aware risk estimation", [2, 1, 3, 5, 5, 5, 3, 3, 4, 2],
          "Calibration-focused Pima work already exists (calib_first_rs preprint, leakfree_rs preprint, reliab_aware). Calibration is under-reported in general (christodoulou 79%), but that is not a Pima gap."),
    "B": ("Decision-threshold trade-off analysis", [2, 2, 3, 5, 5, 5, 3, 3, 4, 2],
          "thresh_math sweeps thresholds 0.30-0.70 on Pima with repeated leakage-free CV; wynants2019 argues thresholds are ad hoc. Screening-sensitivity-target thresholds with uncertainty not seen, but incremental."),
    "C": ("Explanation stability (local SHAP / importance)", [3, 1, 3, 4, 4, 5, 3, 2, 4, 3],
          "Heavily covered: jaimlnn (permutation importance on Pima, resampling), zenodo_shap, attrimp/hypclass/stablerank preprints, JBHI Rashomon, krishna, alvarez. For logistic regression, interventional SHAP is analytic (beta_j x (x_j - background mean)), so stability is expected to be high and the result trivial."),
    "D": ("Multi-family performance + calibration comparison", [1, 1, 2, 5, 4, 5, 4, 4, 4, 1],
          "Already done repeatedly (aposta, leakfree_rs, jaimlnn, etasr); christodoulou shows LR is competitive in general."),
    "E": ("Robustness to missingness / perturbation (as originally defined)", [3, 2, 3, 5, 5, 5, 4, 3, 4, 3],
          "General clinical-prediction missing-data methodology is strong (sisk2023, jce2024imp, sim2025, sperrin2020); explainability under imputation has a Twente conference paper and a 2026 thesis; msys studied Pima zeros. Only a Pima-specific application would remain."),
    "F": ("Why Pima results may not generalise (documentary + external)", [3, 3, 4, 2, 5, 1, 2, 2, 2, 2],
          "Needs external datasets with compatible features (none in the project) and the 1988 paper's full text for outcome timing (unread). Cross-dataset work exists but with different feature sets (aposta)."),
    "G": ("Integrated reproducible evaluation framework", [1, 1, 2, 4, 4, 5, 3, 3, 3, 2],
          "leakfree_rs, aposta, etasr, reliab_aware already present 'frameworks'; integration alone is not a defensible novelty claim."),
    "H1": ("Reporting/leakage audit of Pima-based ML papers", [3, 4, 3, 3, 5, 3, 3, 3, 3, 2],
           "No Pima-specific audit found (search not exhaustive); audits exist elsewhere (kapoor, christodoulou). Needs systematic search + full texts; meta-research rather than a method, which may not satisfy a 'methodological contribution' expectation."),
    "H2": ("Label-aware imputation as a leakage source: quantify inflation and detect it (canary diagnostic)", [3, 4, 4, 5, 5, 5, 4, 4, 5, 3],
           "Three Pima studies describe outcome-conditional imputation (msys 'group median'; pima_leaksafe 'class-conditional medians'; Khan 2026 'group-median') and report AUC 0.93-0.956, far above leakage-safe 0.83-0.85; no study quantifying this mechanism was found (not exhaustive). Exploratory pilot (training split only): RF AUC 0.840 -> 0.938 with the leaky pipeline; label-permutation canary 0.49 (valid) vs 0.857 (leaky)."),
}
SCHEMES = {
    "Baseline weights": [c[2] for c in CRITERIA],
    "Equal weights": [10] * 10,
    "Novelty-heavy (gap 25, overlap 30, method 15)": [25, 30, 5, 5, 2, 2, 5, 5, 1, 15 - 5],
}


def total(scores, w):
    return sum(s * x for s, x in zip(scores, w, strict=True)) / sum(w)


rows = []
for k, (name, sc, note) in D.items():
    row = {"direction": k, "name": name, **dict(zip(KEYS, sc, strict=True)), "total_baseline_/5": round(total(sc, SCHEMES["Baseline weights"]), 2)}
    for sname, w in list(SCHEMES.items())[1:]:
        row[f"total_{sname.split(' (')[0].lower().replace(' ', '_')}_/5"] = round(total(sc, w), 2)
    row["notes"] = note
    rows.append(row)
with open(HERE / "direction_scores.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def rank(scheme):
    w = SCHEMES[scheme]
    return {k: i + 1 for i, k in enumerate(sorted(D, key=lambda d: -total(D[d][1], w)))}


ranks = {s: rank(s) for s in SCHEMES}
md = ["| Dir. | Direction | " + " | ".join(c[1] for c in CRITERIA) + " | **Weighted /5** | Rank (baseline / equal / novelty-heavy) |", "|" + "---|" * (len(CRITERIA) + 4)]
for k in sorted(D, key=lambda d: -total(D[d][1], SCHEMES["Baseline weights"])):
    name, sc, _ = D[k]
    md.append(f"| {k} | {name} | " + " | ".join(str(s) for s in sc) + f" | **{total(sc, SCHEMES['Baseline weights']):.2f}** | {ranks['Baseline weights'][k]} / {ranks['Equal weights'][k]} / {ranks['Novelty-heavy (gap 25, overlap 30, method 15)'][k]} |")
(HERE / "scores_table.md").write_text("\n".join(md), encoding="utf-8")
(HERE / "rubric_table.md").write_text("\n".join(["| Criterion | Weight | A score of 5 means |", "|---|---|---|"] + [f"| {c[1]} | {c[2]} | {c[3]} |" for c in CRITERIA]), encoding="utf-8")
(HERE / "direction_notes.md").write_text("\n".join(f"- **{k} — {D[k][0]}:** {D[k][2]}" for k in D), encoding="utf-8")
print("\n".join(md))
print(json.dumps({s: ranks[s] for s in SCHEMES}, indent=0))
