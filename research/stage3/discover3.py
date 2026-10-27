"""Stage 3 targeted overlap search for directions C (explanation stability) and E (missing-data handling).
OpenAlex relevance-ranked search; prints hits with an abstract snippet so overlap can be judged by reading."""
import json
import sys
import time
import urllib.parse
import urllib.request

Q = {
    "C": ["variance of SHAP explanations across retrained models same data tabular clinical prediction",
          "explanation instability model retraining random seed feature attribution tabular healthcare",
          "predictive multiplicity Rashomon set variable importance clinical prediction",
          "underspecification machine learning credibility same performance different behaviour",
          "bootstrap confidence intervals for SHAP values feature attributions uncertainty",
          "sources of variability in feature importance resampling imputation seed decomposition"],
    "E": ["effect of missing data imputation on Shapley feature importance explanations",
          "imputation method impact on calibration of clinical prediction models simulation",
          "missing indicator method versus imputation clinical prediction model development deployment",
          "missing data should be handled differently for prediction than for explanation",
          "Pima Indians diabetes zero values treated as missing imputation sensitivity calibration explanation",
          "informative missingness measurement not taken clinical prediction model glucose insulin"],
}
which = sys.argv[1:] or list(Q)
UA = {"User-Agent": "stage3-discovery (mailto:none@example.com)"}


def inv(idx):
    if not idx:
        return ""
    w = {p: t for t, ps in idx.items() for p in ps}
    return " ".join(w[i] for i in sorted(w))


for d in which:
    for q in Q[d]:
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "per-page": 6, "select": "doi,title,publication_year,type,primary_location,cited_by_count,abstract_inverted_index"})
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
        except Exception as e:  # noqa: BLE001
            print("ERR", q, e)
            continue
        print(f"\n## [{d}] {q}  (hits {r['meta']['count']})")
        for w in r["results"]:
            venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
            print(f"  - {w['publication_year']} | {w['title'][:105]} | {venue[:38]} | {w['type']} | cited {w['cited_by_count']} | {w.get('doi')}")
            print("      ", inv(w.get("abstract_inverted_index"))[:230])
        time.sleep(0.4)
