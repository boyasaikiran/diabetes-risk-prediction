"""Verify bibliographic metadata and fetch abstracts (Crossref -> OpenAlex -> PubMed -> Semantic Scholar; arXiv API for arXiv IDs).
Writes research/stage2/sources_verified.json. Abstracts are used only to read; nothing is quoted in outputs."""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent / "sources_verified.json"
UA = {"User-Agent": "stage2-verify (mailto:none@example.com)"}

DOIS = {
    # --- diabetes / Pima
    "kavak": "10.1016/j.csbj.2016.12.005", "chaki": "10.1016/j.jksuci.2020.06.013", "khanam": "10.1016/j.icte.2021.02.004",
    "sisodia": "10.1016/j.procs.2018.05.122", "kaur": "10.1016/j.aci.2018.12.004", "miao": "10.1145/3463914.3463922",
    "kirbas": "10.17694/bajece.1577929", "rfegru": "10.1038/s41598-024-82420-9", "msys": "10.1007/s10916-018-0940-7",
    "collins2011": "10.1186/1741-7015-9-103", "noble2011": "10.1136/bmj.d7163",
    # --- overlap candidates
    "jaimlnn": "10.55529/jaimlnn.62.15.31", "zenodo_shap": "10.5281/zenodo.23047034", "leakfree_rs": "10.21203/rs.3.rs-9678084/v1",
    "etasr": "10.48084/etasr.14155", "thresh_math": "10.3390/math14183421", "calib_first_rs": "10.21203/rs.3.rs-8627838/v1",
    "pima_survey": "10.30880/jscdm.2025.06.01.001", "aposta": "10.23900/ra.v24i114.1893", "reliab_aware": "10.22214/ijraset.2026.84701",
    # --- methodology
    "davis": "10.1145/1143844.1143874", "saito": "10.1371/journal.pone.0118432", "vancalster2019": "10.1186/s12916-019-1466-7",
    "vancalster2016": "10.1016/j.jclinepi.2015.12.005", "vickers2006": "10.1177/0272989X06295361", "wynants2019": "10.1186/s12916-019-1425-3",
    "steyerberg": "10.1097/EDE.0b013e3181c30fb2", "wolff": "10.7326/m18-1376", "tripodai": "10.1136/bmj-2023-078378", "tripod2015": "10.1136/bmj.g7594",
    "riley2019": "10.1002/sim.7992", "kapoor": "10.1016/j.patter.2023.100804", "varma": "10.1186/1471-2105-7-91", "vabalas": "10.1371/journal.pone.0224365",
    "christodoulou": "10.1016/j.jclinepi.2019.02.004", "lundberg2020": "10.1038/s42256-019-0138-9", "ghassemi": "10.1016/s2589-7500(21)00208-9",
    "rudin": "10.1038/s42256-019-0048-x", "obermeyer": "10.1126/science.aax2342", "gianfrancesco": "10.1001/jamainternmed.2018.3763",
    "niculescu": "10.1145/1102351.1102430", "slack": "10.1145/3375627.3375830", "kumar_icml": None,
}
ARXIV = {"lundberg2017": "1705.07874", "alvarez": "1806.08049", "krishna": "2202.01602", "kumar2020": "2002.11097", "matijevic": "2602.11360"}


def get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            time.sleep(2 + i)
    return ""


def inverted(idx):
    if not idx:
        return ""
    words = {}
    for w, pos in idx.items():
        for p in pos:
            words[p] = w
    return " ".join(words[k] for k in sorted(words))


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or "")).strip()


res = {}
for key, doi in DOIS.items():
    if not doi:
        continue
    rec = {"doi": doi, "title": None, "authors": [], "n_authors": 0, "year": None, "venue": None, "volume": None, "issue": None, "pages": None, "type": None, "abstract": "", "abstract_source": None, "crossref_ok": False}
    c = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))
    if c:
        try:
            m = json.loads(c)["message"]
            au = m.get("author", [])
            rec.update(title=clean(m["title"][0]), authors=[f"{a.get('family', a.get('name', '?'))} {a.get('given', '')[:1]}".strip() for a in au[:6]], n_authors=len(au),
                       year=(m.get("issued", {}).get("date-parts") or [[None]])[0][0], venue=(m.get("container-title") or [""])[0], volume=m.get("volume"), issue=m.get("issue"),
                       pages=m.get("page") or m.get("article-number"), type=m.get("type"), crossref_ok=True)
            a = clean(m.get("abstract", ""))
            if len(a) > 120:
                rec["abstract"], rec["abstract_source"] = a, "crossref"
        except Exception:  # noqa: BLE001
            pass
    if len(rec["abstract"]) < 120:
        o = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/") + "?select=title,abstract_inverted_index,publication_year,primary_location")
        if o:
            try:
                j = json.loads(o)
                a = inverted(j.get("abstract_inverted_index"))
                if len(a) > 120:
                    rec["abstract"], rec["abstract_source"] = a, "openalex"
                if not rec["title"]:
                    rec["title"], rec["year"] = j.get("title"), j.get("publication_year")
            except Exception:  # noqa: BLE001
                pass
    if len(rec["abstract"]) < 120:
        s = get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract")
        if s:
            try:
                a = json.loads(s).get("abstract") or ""
                if len(a) > 120:
                    rec["abstract"], rec["abstract_source"] = a, "semanticscholar"
            except Exception:  # noqa: BLE001
                pass
    if len(rec["abstract"]) < 120:
        q = urllib.parse.quote(f"{doi}[AID]")
        ids = get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={q}&retmode=json")
        try:
            lst = json.loads(ids)["esearchresult"]["idlist"]
            if lst:
                x = get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={lst[0]}&retmode=xml")
                a = clean(" ".join("".join(t.itertext()) for t in ET.fromstring(x).iter("AbstractText")))
                if len(a) > 120:
                    rec["abstract"], rec["abstract_source"] = a, "pubmed"
        except Exception:  # noqa: BLE001
            pass
    res[key] = rec
    time.sleep(0.3)

for key, aid in ARXIV.items():
    x = get(f"http://export.arxiv.org/api/query?id_list={aid}")
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        e = ET.fromstring(x).find("a:entry", ns)
        au = [a.find("a:name", ns).text for a in e.findall("a:author", ns)]
        res[key] = {"arxiv": aid, "title": clean(e.find("a:title", ns).text), "authors": au[:6], "n_authors": len(au), "year": int(e.find("a:published", ns).text[:4]),
                    "venue": "arXiv preprint", "abstract": clean(e.find("a:summary", ns).text), "abstract_source": "arxiv", "crossref_ok": False, "type": "preprint"}
    except Exception as ex:  # noqa: BLE001
        res[key] = {"arxiv": aid, "error": str(ex)}
    time.sleep(0.5)

OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
lim = int(sys.argv[1]) if len(sys.argv) > 1 else 520
for k, r in res.items():
    ident = r.get("doi") or ("arXiv:" + r.get("arxiv", ""))
    print(f"\n[{k}] {r.get('title')} | {', '.join(r.get('authors', [])[:3])}{' +' + str(r['n_authors'] - 3) if r.get('n_authors', 0) > 3 else ''} | {r.get('year')} | {r.get('venue')} {r.get('volume') or ''}({r.get('issue') or ''}) {r.get('pages') or ''} | {ident} | abs:{r.get('abstract_source')}")
    print("   ", (r.get("abstract") or "(NO ABSTRACT RETRIEVED)")[:lim])
