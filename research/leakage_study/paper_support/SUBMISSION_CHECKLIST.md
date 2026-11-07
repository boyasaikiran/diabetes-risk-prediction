# SUBMISSION CHECKLIST (draft; items unchecked until evidence exists)

`[ ]` open, `[x]` done with evidence named, `[~]` partly. Nothing is checked unless the evidence is cited.

## A. Research integrity and pre-registration
- [ ] `prereg-v1` frozen files re-hashed and match `PREREG_FREEZE.txt`.
- [ ] Amendment log (§9) still empty, or each amendment dated and reported; confirmatory vs exploratory results kept separate.
- [ ] Every pre-registered hypothesis (H1–H7) reported, including null/unfavourable ones; hypothesis wording unchanged.
- [ ] Forking-path disclosure (pilot informed the SESOI; idea came from abstract-level reading of three studies) stated in the paper.
- [ ] Deviations listed: code v0.1→v0.1.1, concurrent runs, Exp 4 attempt-1 failure, analysis code written after freeze but before unblinding, `sim_contrasts` `n`-label defect, operationalisations in `analysis.py`.
- [ ] No dry-run numbers appear anywhere in the paper.
- [ ] Execution success is not described as hypothesis confirmation.

## B. Data and code provenance
- [ ] Dataset source and SHA-256 recorded; label definition and its unresolved timing caveat stated (Smith 1988 full text pending from author).
- [ ] Code tags and commits cited; repository state at submission tagged.
- [ ] Code/data availability statement matches what is actually deposited.
- [ ] AI-assistance disclosure: experiment code and tests AI-assisted (as disclosed in PREREG); manuscript prose written by the author alone.

## C. Verification (must pass before any result is written)
- [ ] Exp 4 completed; exit state and output inventory recorded.
- [ ] G6 audit: all checks passed, with evidence in `results/audit/AUDIT_G6.json`.
- [ ] Metrics recomputed from saved predictions; sample counts and split assignments verified.
- [ ] At least one experimental cell reproduced from scratch.
- [ ] Stop-rule gates verified on the full-run results.
- [ ] `verify_report.py` independent check agrees with every registered number.

## D. Statistical reporting
- [ ] Each comparison: estimand, estimate, 95% interval, method (Nadeau–Bengio for real-data splits; plain CI for independent simulation replicates), n, decision under the frozen rule.
- [ ] Holm adjustment reported only as supplementary, as pre-specified.
- [ ] No p-values from split-wise tests presented as independent evidence.
- [ ] Inconclusive results labelled inconclusive.

## E. Figures and tables
- [ ] Each has: source data file, caption, axis labels/units, abbreviation key, numbers cross-checked to artifacts.
- [ ] Generated from verified data by a script kept in the repository.
- [ ] No figure adapted from elsewhere without citation/permission.

## F. Limitations and threats to validity (must be stated)
- [ ] One dataset, 768 rows, one historical population; no clinical or external-validity claim.
- [ ] Only the tested imputation-leakage mechanisms; not "all leakage".
- [ ] Simulation assumptions (multivariate normal, logistic outcome, MCAR/MNAR with OR 1.5) and their reach.
- [ ] Model-/configuration dependence; no tuning performed.
- [ ] Outcome-timing ambiguity of the Pima label.
- [ ] Novelty claim limited to what the literature review supports.

## G. Literature and references
- [ ] Full-text findings for the three studies and Smith (1988) received from author and recorded as author-supplied.
- [ ] Every reference verified against an authoritative record (DOI/publisher/PubMed/Crossref); none invented.
- [ ] Claim-to-source matrix complete.

## H. Institutional rules (clarify with author)
- [ ] Written definition of "AI-generated content" confirmed.
- [ ] Prose is the author's own; AI use limited to what the institution permits.
- [ ] Plagiarism and novelty requirements understood; no promise of a similarity score.

## I. Venue requirements — PENDING (venue not chosen)
- [ ] Venue selected and checked from its official call/author page (reputation and indexing verified, not assumed).
- [ ] Template, page/word limit, abstract limits, keywords, citation style.
- [ ] Anonymisation (double-blind?), ethics/data/code/COI/funding/author-contribution declarations.
- [ ] Submission system, deadlines, copyright form. Author submits personally; nothing is submitted on their behalf.

## J. Final
- [ ] No critical issues open in `FINAL_AUDIT.md`.
- [ ] Reviewer-style questions answered.
