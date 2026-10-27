"""One-off correction of the 'glucose is circular / re-expresses the label' wording (see research/stage1/STAGE1_AUDIT.md, W1)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ABL = "glucose alone 0.799 ± 0.034, all features except glucose 0.768 ± 0.015, all eight features 0.845 ± 0.013"

EDITS = [
    # ---------------- E-report content
    ("report/content.py",
     "show that plasma glucose dominates the model, which is expected because the dataset’s label is itself defined from a glucose-tolerance criterion. ",
     "show that plasma glucose is the strongest single predictor, while an exploratory training-only ablation shows that the other features still carry signal. "),
    ("report/content.py",
     "which states that the diagnostic variable follows WHO criteria [@uci].",
     "which states that the diagnostic variable follows WHO criteria, namely 2-hour post-load plasma glucose of at least 200 mg/dL at any survey examination or when found during routine medical care [@uci]. The documentation does not state when the recorded measurements were taken relative to that classification, and the highest recorded glucose in the file is 199 mg/dL, so the target is described in this report as *recorded diabetes status* and not as future onset."),
    ("report/content.py",
     "**Label definition.** The label is defined from a glucose-tolerance criterion, so glucose is partly circular as a predictor.",
     "**Label definition.** The documented label rule is a glucose-tolerance criterion applied at any survey examination or in routine care; its timing relative to the recorded features is not documented, so the target is treated as recorded diabetes status and not as future onset."),
    ("report/content.py",
     "This pattern is expected because the dataset’s label is itself based on glucose; the model largely re-expresses that criterion and should not be presented as discovering independent risk factors.",
     f"An exploratory ablation on the training split only (same five folds; test set not used) gave cross-validated ROC-AUC of {ABL}. Glucose is therefore the strongest single predictor, but the other features together still carry signal. Because the documented outcome rule is itself a glucose criterion and its timing relative to the features is unknown, these associations should not be presented as independent risk factors."),
    ("report/content.py",
     "(iii) Performance rests almost entirely on glucose, which is part of the label definition.",
     "(iii) Glucose is the strongest single predictor, and the dataset documentation does not settle how the recorded glucose relates in time to the outcome classification."),
    ("report/content.py",
     "The label depends on a glucose-tolerance criterion, so the model largely predicts the outcome of a test that uses one of its inputs.",
     "The documented label rule uses a glucose-tolerance criterion at any survey examination or in routine care, and the timing between the recorded measurements and that classification is not documented, so the target is recorded diabetes status and not necessarily future onset."),
    ("report/content.py",
     "Plasma glucose dominates the model; insulin, blood pressure and skin-fold thickness contribute almost nothing. This reflects how the label is defined.",
     "Plasma glucose is the strongest single predictor; insulin, blood pressure and skin-fold thickness contribute almost nothing by permutation importance, while an exploratory training-only ablation shows the remaining features still carry signal (ROC-AUC 0.768 without glucose, 0.845 with all eight)."),
    ("report/content.py",
     "dependence on a glucose-defined label;",
     "an outcome whose timing relative to the features is undocumented;"),
    # ---------------- supporting pack
    ("report/build_support.py",
     "and the label is defined by a glucose-tolerance criterion so glucose is partly circular.",
     "and the outcome’s timing relative to the features is undocumented (label rule: 2-h glucose ≥ 200 mg/dL at any examination or in routine care, yet recorded glucose never exceeds 199)."),
    ("report/build_support.py",
     "far above others; the label itself comes from a glucose-tolerance criterion, so the model largely re-expresses it.",
     "far above others, and glucose alone gives a training CV ROC-AUC of 0.799. The other features still add signal (0.768 without glucose, 0.845 with all). The documented label rule is itself a glucose criterion, so a strong association is expected, but the recorded glucose cannot be the exact value that defined the label (maximum 199) and the timing is undocumented."),
    # ---------------- slides
    ("presentation/build_deck.js",
     "glucose drives almost everything, and the label itself comes from a glucose criterion, so the model largely restates that criterion.",
     "glucose is the strongest single predictor, but a training-only ablation shows the other features still carry signal, with ROC-AUC 0.768 without glucose and 0.845 with all eight, and the timing of the outcome relative to the features is not documented."),
    ("presentation/build_deck.js",
     "The label is based on a glucose-tolerance criterion, so glucose is partly circular.",
     "The outcome’s timing relative to the recorded features is undocumented, so I describe it as recorded diabetes status."),
    ("presentation/build_deck.js",
     "Glucose dominates; label is glucose-based, so partly circular.",
     "Glucose is the strongest predictor; the other features still add signal."),
    ("presentation/build_deck.js",
     "Label is glucose-based; glucose dominates",
     "Outcome timing undocumented; glucose strongest"),
    ("docs/presentation_outline.md",
     "glucose dominates and is part of the label; other features add little",
     "glucose is the strongest predictor, other features still add signal; outcome timing is undocumented"),
    # ---------------- docs
    ("docs/dataset_card.md",
     "- Outcome is defined from glucose; including glucose as a feature is partly circular.",
     "- The documented outcome rule is itself a glucose criterion (2-h post-load glucose ≥ 200 mg/dL at any survey examination or in routine care), but the recorded glucose never exceeds 199 mg/dL and the timing of the classification relative to the recorded features is not documented. Treat the target as *recorded diabetes status*, not as future onset."),
    ("docs/model_card.md",
     "Glucose dominates the model and is part of the label definition; other features add little.",
     "Glucose is the strongest single predictor (training-split CV ROC-AUC 0.799 alone, 0.768 without it, 0.845 with all eight features), but the other features carry signal too. The timing of the outcome relative to the features is undocumented, so the target is recorded diabetes status, not future onset."),
    ("README.md",
     "- The label follows a WHO glucose-tolerance criterion, so glucose is nearly part of the target. The model\n  largely re-expresses that criterion; it is not discovering independent risk factors.",
     "- The documented label is a WHO glucose-tolerance criterion applied at any survey examination or in routine care; the timing\n  relative to the recorded features is not documented and recorded glucose never exceeds 199 mg/dL. The target is therefore\n  *recorded diabetes status*, not future onset. Glucose is the strongest predictor, but a training-only ablation shows the other\n  features still carry signal (CV ROC-AUC 0.799 glucose alone, 0.768 without glucose, 0.845 all)."),
    # ---------------- application and generated reports
    ("app.py",
     "The label marks diabetes by a WHO glucose-tolerance criterion. Results ",
     "The label records diabetes status by a WHO glucose-tolerance criterion (timing relative to the measurements is undocumented). Results "),
    ("app.py",
     "The outcome follows a WHO glucose-tolerance criterion, so glucose\nis strongly tied to the label by construction.",
     "The outcome follows a WHO glucose-tolerance criterion applied at any\nexamination or in routine care; its timing relative to the measurements is undocumented. Glucose is the strongest predictor, but the other\nfeatures still carry signal."),
    ("src/report_generator.py",
     "outcome label reflects a glucose-tolerance criterion.",
     "outcome label follows a glucose-tolerance criterion whose timing relative to the measurements is undocumented."),
]

missing = 0
for rel, old, new in EDITS:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    if old not in t:
        print("NOT FOUND:", rel, "|", old[:70])
        missing += 1
        continue
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("ok", rel)

# any remaining wording?
pat = re.compile(r"partly circular|re-express|restates that criterion|glucose-defined|by construction\.|part of the label", re.I)
for rel in ["README.md", "app.py", "src/report_generator.py", "report/content.py", "report/build_support.py", "presentation/build_deck.js", "docs/model_card.md", "docs/dataset_card.md", "docs/presentation_outline.md", "docs/methodology.md"]:
    for n, ln in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
        if pat.search(ln):
            print("REMAINING", rel, n, ln[:140])
print("missing:", missing)
