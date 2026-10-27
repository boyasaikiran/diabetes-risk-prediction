"""Verify metadata and read abstracts for the Stage 3 overlap sources (same method as stage2/verify_sources.py).
Writes research/stage3/sources3_verified.json"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "stage3-verify (mailto:none@example.com)"}
DOIS = {
    "hypclass": "10.48550/arxiv.2603.15821", "attrimp": "10.5281/zenodo.19468379", "stablerank": "10.1016/j.nxmate.2026.103038",
    "rashomon_jbhi": "10.1109/jbhi.2024.3443069", "multiplicity_aaai": "10.1609/aaai.v37i9.26227", "intervalshap": "10.48550/arxiv.2610.11953",
    "uncert_afa": "10.48550/arxiv.2311.17446", "sisk2023": "10.1177/09622802231165001", "jce2024imp": "10.1016/j.jclinepi.2024.111539",
    "sim2025": "10.1002/sim.70203", "sperrin2020": "10.1016/j.jclinepi.2020.03.028", "bremen2026": "10.26092/elib/6231",
    "pima_leaksafe": "10.64252/3a8wqx36", "knn_imp_bmcmrm": "10.1186/s12874-024-02324-0", "reportmethods2012": "10.1371/journal.pmed.1001221",
}


def get(url):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            time.sleep(2 + i)
    return ""


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or "")).strip()


def inv(idx):
    if not idx:
        return ""
    w = {p: t for t, ps in idx.items() for p in ps}
    return " ".join(w[i] for i in sorted(w))


res = {}
for k, doi in DOIS.items():
    rec = {"doi": doi, "title": None, "authors": [], "n_authors": 0, "year": None, "venue": None, "type": None, "abstract": "", "abstract_source": None, "crossref_ok": False}
    c = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))
    try:
        m = json.loads(c)["message"]
        au = m.get("author", [])
        rec.update(title=clean(m["title"][0]), authors=[f"{a.get('family', a.get('name', '?'))} {a.get('given', '')[:1]}".strip() for a in au[:6]], n_authors=len(au),
                   year=(m.get("issued", {}).get("date-parts") or [[None]])[0][0], venue=(m.get("container-title") or [""])[0], type=m.get("type"), crossref_ok=True)
        a = clean(m.get("abstract", ""))
        if len(a) > 120:
            rec["abstract"], rec["abstract_source"] = a, "crossref"
    except Exception:  # noqa: BLE001
        pass
    if len(rec["abstract"]) < 120:
        try:
            j = json.loads(get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/") + "?select=title,abstract_inverted_index,publication_year,authorships,primary_location,type"))
            a = inv(j.get("abstract_inverted_index"))
            if len(a) > 120:
                rec["abstract"], rec["abstract_source"] = a, "openalex"
            if not rec["title"]:
                rec.update(title=j.get("title"), year=j.get("publication_year"), type=j.get("type"),
                           authors=[x["author"]["display_name"] for x in j.get("authorships", [])[:6]], n_authors=len(j.get("authorships", [])),
                           venue=((j.get("primary_location") or {}).get("source") or {}).get("display_name", ""))
        except Exception:  # noqa: BLE001
            pass
    if len(rec["abstract"]) < 120:
        try:
            a = json.loads(get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract")).get("abstract") or ""
            if len(a) > 120:
                rec["abstract"], rec["abstract_source"] = a, "semanticscholar"
        except Exception:  # noqa: BLE001
            pass
    if len(rec["abstract"]) < 120:
        try:
            ids = json.loads(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=" + urllib.parse.quote(doi + "[AID]")))["esearchresult"]["idlist"]
            if ids:
                x = get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids[0]}&retmode=xml")
                a = clean(" ".join("".join(t.itertext()) for t in ET.fromstring(x).iter("AbstractText")))
                if len(a) > 120:
                    rec["abstract"], rec["abstract_source"] = a, "pubmed"
        except Exception:  # noqa: BLE001
            pass
    res[k] = rec
    time.sleep(0.3)
(HERE / "sources3_verified.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
lim = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
for k, r in res.items():
    print(f"\n[{k}] {r['title']} | {', '.join(r['authors'][:3])}{' +' + str(r['n_authors'] - 3) if r['n_authors'] > 3 else ''} | {r['year']} | {r['venue']} | {r['type']} | {r['doi']} | abs:{r['abstract_source']}")
    print("   ", r["abstract"][:lim] or "(NO ABSTRACT)")
