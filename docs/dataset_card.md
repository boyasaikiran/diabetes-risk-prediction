# Dataset card: Pima Indians Diabetes Database

| Item | Detail |
|---|---|
| Source | National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK); donated to UCI by Vincent Sigillito (Johns Hopkins APL), 1990 |
| Obtained via | OpenML dataset 37 (mirror of UCI). SHA-256 and download time are written to `data/raw/provenance.json` |
| License | OpenML lists "Public"; UCI asks users to follow its citation policy. **Verify terms at the source before redistributing.** The raw file is git-ignored; the app downloads it |
| Size | 768 rows, 8 features + binary outcome |
| Population | Females, ≥ 21 years, Pima Indian heritage, near Phoenix, Arizona, USA |
| Target | `Outcome`: 1 = "tested positive" for diabetes by WHO criteria (2-hour post-load plasma glucose ≥ 200 mg/dL on an oral glucose tolerance test). 268 positive / 500 negative (34.9 %) |
| Reference use | Smith et al. (1988), ADAP algorithm, ~76 % sensitivity/specificity on 192 instances |

## Features
Pregnancies (count), Glucose (2-h OGTT, mg/dL), BloodPressure (diastolic, mm Hg), SkinThickness
(triceps, mm), Insulin (2-h serum, mu U/ml), BMI (kg/m²), DiabetesPedigreeFunction (study-specific
family-history score), Age (years).

## Data quality (measured in this project, `artifacts/data_profile.json`)
- No NaN cells, 0 duplicate rows.
- **Zeros encode missing values** in: Glucose 5, BloodPressure 35, SkinThickness 227, Insulin 374, BMI 11.
  These are converted to NaN and imputed with training-fold medians. Pregnancies = 0 is valid and untouched.
- Insulin and skin-fold are missing for roughly half or a third of rows, so imputed values carry little information.

## Known biases and risks
- Single, narrow, historical population: do not generalise to other groups.
- Sampling is not representative of any general population.
- The documented outcome rule is itself a glucose criterion (2-h post-load glucose ≥ 200 mg/dL at any survey examination or in routine care), but the recorded glucose never exceeds 199 mg/dL and the timing of the classification relative to the recorded features is not documented. Treat the target as *recorded diabetes status*, not as future onset.
- Tiny sample: high variance in every estimate.
