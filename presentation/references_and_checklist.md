# References (all cited on slide 15)

1. World Health Organization. *Diabetes* (fact sheet). https://www.who.int/news-room/fact-sheets/detail/diabetes
   Used for: 830 million people with diabetes in 2022 (200 million in 1990); 1.6 million deaths directly caused in 2021; definition of diabetes. Fetched and checked while building this deck (page dated 14 Nov 2024).
2. Smith JW, Everhart JE, Dickson WC, Knowler WC, Johannes RS (1988). Using the ADAP learning algorithm to forecast the onset of diabetes mellitus. *Proc. Symposium on Computer Applications in Medical Care*, 261–265. (Citation as given in the dataset documentation.)
3. Pima Indians Diabetes Database — UCI: https://archive.ics.uci.edu/ml/datasets/pima+indians+diabetes ; OpenML mirror: https://www.openml.org/d/37
4. Pedregosa F et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR* 12:2825–2830. Docs: https://scikit-learn.org/stable/
5. Lundberg SM, Lee S-I (2017). A unified approach to interpreting model predictions. *NeurIPS* 30. Docs: https://shap.readthedocs.io

Not used: IDF statistics (not retrieved, so none are quoted).

# Final quality checklist

| Check | Status |
|---|---|
| Exactly 15 slides, 16:9 (13.33 x 7.5 in) | Verified with python-pptx |
| Editable shapes, text, native charts and tables | Yes (no slide is a picture) |
| Speaker notes on all slides (79–133 words each, ~1,650 total ≈ 11 min) | Verified |
| File validity | `validate.py` passed |
| Text overflow | Checked with a Calibri-metrics script (`check_fit.py`): 0 flags. **Not checked by rendering** (no PowerPoint/LibreOffice on this machine) — open the file and flip through once |
| All numbers from real runs | Dataset profile and metrics from `artifacts/metrics.json`; WHO numbers verified at source |
| Illustrative content labelled | Slide 11 example (default demo inputs, approximate) and slide 12 wireframe are labelled |
| Placeholders to fill | Slide 1: name, registration no., college, guide, year |
| PDF export | **Not produced** (no renderer available). In PowerPoint: File → Export → PDF |
| Fonts | Calibri throughout (Inter/Aptos not used, since they may be missing on other machines) |
