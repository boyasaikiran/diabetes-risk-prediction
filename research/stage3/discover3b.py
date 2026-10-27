import json
import time
import urllib.parse
import urllib.request

Q=["imputation using outcome label target leakage inflated performance class-conditional mean median",
   "class-wise median imputation by outcome class data leakage diabetes dataset inflated accuracy",
   "Pima Indians diabetes imputation by class median leakage",
   "data leakage imputation before train test split inflated performance quantified simulation",
   "supervised imputation uses outcome leakage prediction model deployment outcome unavailable",
   "label leakage in preprocessing medical tabular benchmarks diabetes overoptimistic"]
UA={"User-Agent":"stage3 (mailto:none@example.com)"}
def inv(idx):
    if not idx:
        return ""
    w={p:t for t,ps in idx.items() for p in ps}; return " ".join(w[i] for i in sorted(w))
for q in Q:
    u="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":q,"per-page":7,"select":"doi,title,publication_year,type,primary_location,cited_by_count,abstract_inverted_index"})
    r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))
    print(f"\n## {q} (hits {r['meta']['count']})")
    for w in r["results"]:
        v=((w.get("primary_location") or {}).get("source") or {}).get("display_name","")
        print(f"  - {w['publication_year']} | {w['title'][:105]} | {v[:36]} | {w['type']} | cited {w['cited_by_count']} | {w.get('doi')}")
        print("      ",inv(w.get("abstract_inverted_index"))[:260])
    time.sleep(0.4)
