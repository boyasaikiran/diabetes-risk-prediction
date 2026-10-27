"""Overlap/gap check: OpenAlex searches for combinations of our candidate research directions.
Prints total hits and the top results so overlap can be judged by reading titles/abstract snippets."""
import json
import time
import urllib.parse
import urllib.request

QUERIES = [
    "Pima Indians diabetes SHAP explanation stability",
    "Pima Indians diabetes feature importance stability repeated cross-validation",
    "Pima Indians diabetes probability calibration Brier score",
    "Pima Indians diabetes nested cross-validation",
    "Pima Indians diabetes imputation zero values sensitivity analysis robustness",
    "diabetes prediction explanation stability across resampled training sets",
    "diabetes risk model calibration decision threshold sensitivity specificity trade-off",
    "Pima Indians diabetes data leakage preprocessing",
]
UA = {"User-Agent": "stage2-overlap (mailto:none@example.com)"}
for q in QUERIES:
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "per-page": 8, "select": "id,doi,title,publication_year,type,primary_location,cited_by_count,abstract_inverted_index"})
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
    except Exception as e:  # noqa: BLE001
        print("ERR", q, e)
        continue
    print(f"\n## {q}  (total hits: {d['meta']['count']})")
    for w in d["results"]:
        venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        print(f"  - {w['publication_year']} | {w['title'][:110]} | {venue[:40]} | {w['type']} | cited {w['cited_by_count']} | {w.get('doi')}")
    time.sleep(0.4)
