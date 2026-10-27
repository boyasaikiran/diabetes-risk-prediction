"""Stage 2 discovery: query Crossref for candidate sources per topic. Output is only a candidate list;
nothing here is cited until verified by verify_sources.py."""
import json
import sys
import time
import urllib.parse
import urllib.request

QUERIES = {
    "T1 diabetes ML (Pima)": ["Pima Indians diabetes dataset machine learning classification comparison",
                               "diabetes prediction machine learning Pima SHAP explainable",
                               "Pima Indians diabetes calibration logistic regression"],
    "T2 Pima limitations / data quality": ["Pima Indians diabetes dataset limitations zero values missing data quality",
                                           "problems with the Pima Indians diabetes dataset"],
    "T3/T4 imbalance, ROC vs PR": ["precision-recall ROC relationship Davis Goadrich",
                                   "imbalanced classification evaluation metrics medical"],
    "T5 calibration": ["calibration achilles heel of predictive analytics",
                       "calibration hierarchy risk models",
                       "calibration of machine learning clinical prediction models review"],
    "T6 thresholds": ["decision curve analysis evaluating prediction models net benefit",
                      "threshold selection screening prediction model sensitivity specificity trade-off"],
    "T7/T8 explainability, SHAP": ["from local explanations to global understanding with explainable AI for trees",
                                   "disagreement problem in explainable machine learning",
                                   "robustness of interpretability methods stability explanations",
                                   "false hope of current approaches to explainable artificial intelligence in health care",
                                   "SHAP explanation stability instability feature attribution"],
    "T9 bias, fairness, generalizability": ["potential biases in machine learning algorithms using electronic health record data",
                                           "machine learning healthcare generalizability external validation"],
    "T10 reporting & validation": ["PROBAST tool to assess risk of bias prediction model",
                                   "TRIPOD statement transparent reporting multivariable prediction model",
                                   "minimum sample size for developing a multivariable prediction model"],
    "T11 leakage, selection bias, small data": ["leakage and the reproducibility crisis in machine learning-based science",
                                                "over-fitting in model selection and subsequent selection bias in performance evaluation",
                                                "bias in error estimation when using cross-validation for model selection",
                                                "machine learning algorithm validation with a limited sample size"],
    "T12 overlap: ML vs LR, diabetes risk": ["systematic review no performance benefit of machine learning over logistic regression clinical prediction",
                                             "prediction models for diabetes systematic review methodology reporting",
                                             "explainable machine learning diabetes prediction SHAP calibration external validation"],
}
UA = {"User-Agent": "stage2-discovery (mailto:none@example.com)"}
only = sys.argv[1:]
for topic, qs in QUERIES.items():
    if only and not any(o in topic for o in only):
        continue
    print("\n#####", topic)
    for q in qs:
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": 5, "select": "DOI,title,author,issued,container-title,type,is-referenced-by-count"})
        try:
            items = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))["message"]["items"]
        except Exception as e:  # noqa: BLE001
            print("ERR", q, e)
            continue
        print("  Q:", q)
        for m in items:
            au = m.get("author", [])
            a1 = (au[0].get("family", "?") + (" et al." if len(au) > 1 else "")) if au else "?"
            yr = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
            print(f"    - {a1} {yr} | {m['title'][0][:100]} | {(m.get('container-title') or [''])[0][:45]} | cited {m.get('is-referenced-by-count')} | {m['DOI']}")
        time.sleep(0.5)
