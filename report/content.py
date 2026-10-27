"""Report text. All numbers are read from artifacts/metrics.json and report/extra_facts.json."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

from docx_engine import mfrac, mparen, mr, msub, msum, msup

ROOT = Path(__file__).resolve().parent.parent
FIG = Path(__file__).resolve().parent / "figures"
SHOT = ROOT / "docs" / "screenshots"
M = json.loads((ROOT / "artifacts" / "metrics.json").read_text(encoding="utf-8"))
X = json.loads((Path(__file__).resolve().parent / "extra_facts.json").read_text(encoding="utf-8"))
T, CI = M["test"]["metrics"], M["test"]["ci95"]
CM = T["confusion_matrix"]
TR = M["train_oof"]["metrics"]
PROF = M["data_profile"]
COMP = {r["model"]: r for r in M["model_comparison"]}
IMP = M["permutation_importance_test"]
META = M["metadata"]
EX = X["example"]


def src(path: str, start: str, end: str | None = None, dedent=True) -> str:
    """Verbatim excerpt from the project source between two marker lines."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if start in ln)
    j = next((k for k in range(i + 1, len(lines)) if end and end in lines[k]), len(lines)) if end else len(lines)
    out = "\n".join(lines[i:j]).rstrip()
    return textwrap.dedent(out) if dedent else out


def ci(k, d=3):
    return f"{CI[k][0]:.{d}f}–{CI[k][1]:.{d}f}"


f3 = lambda v: f"{v:.3f}"  # noqa: E731

REFS = {  # IEEE entries, keyed
    "who": "World Health Organization, “Diabetes,” Fact sheet, 2024. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/diabetes (accessed Oct. 27, 2026).",
    "idf": "H. Sun *et al.*, “IDF Diabetes Atlas: Global, regional and country-level diabetes prevalence estimates for 2021 and projections for 2045,” *Diabetes Res. Clin. Pract.*, vol. 183, Art. no. 109119, Jan. 2022, doi: 10.1016/j.diabres.2021.109119.",
    "kavak": "I. Kavakiotis, O. Tsave, A. Salifoglou, N. Maglaveras, I. Vlahavas, and I. Chouvarda, “Machine learning and data mining methods in diabetes research,” *Comput. Struct. Biotechnol. J.*, vol. 15, pp. 104–116, 2017, doi: 10.1016/j.csbj.2016.12.005.",
    "chaki": "J. Chaki, S. Thillai Ganesh, S. Cidham, and S. Ananda Theertan, “Machine learning and artificial intelligence based diabetes mellitus detection and self-management: A systematic review,” *J. King Saud Univ. – Comput. Inf. Sci.*, vol. 34, no. 6, pp. 3204–3225, 2022, doi: 10.1016/j.jksuci.2020.06.013.",
    "sisodia": "D. Sisodia and D. S. Sisodia, “Prediction of diabetes using classification algorithms,” *Procedia Comput. Sci.*, vol. 132, pp. 1578–1585, 2018, doi: 10.1016/j.procs.2018.05.122.",
    "kaur": "H. Kaur and V. Kumari, “Predictive modelling and analytics for diabetes using a machine learning approach,” *Appl. Comput. Inform.*, vol. 18, no. 1/2, pp. 90–100, 2020, doi: 10.1016/j.aci.2018.12.004.",
    "khanam": "J. J. Khanam and S. Y. Foo, “A comparison of machine learning algorithms for diabetes prediction,” *ICT Express*, vol. 7, no. 4, pp. 432–439, 2021, doi: 10.1016/j.icte.2021.02.004.",
    "smith": "J. W. Smith, J. E. Everhart, W. C. Dickson, W. C. Knowler, and R. S. Johannes, “Using the ADAP learning algorithm to forecast the onset of diabetes mellitus,” in *Proc. Symp. Computer Applications in Medical Care*, IEEE Computer Society Press, 1988, pp. 261–265.",
    "uci": "V. Sigillito (donor), “Pima Indians Diabetes Database,” National Institute of Diabetes and Digestive and Kidney Diseases, 1990; UCI Machine Learning Repository and OpenML dataset 37. [Online]. Available: https://www.openml.org/d/37 (accessed Oct. 26, 2026).",
    "saito": "T. Saito and M. Rehmsmeier, “The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,” *PLoS ONE*, vol. 10, no. 3, Art. no. e0118432, 2015, doi: 10.1371/journal.pone.0118432.",
    "fawcett": "T. Fawcett, “An introduction to ROC analysis,” *Pattern Recognit. Lett.*, vol. 27, no. 8, pp. 861–874, 2006, doi: 10.1016/j.patrec.2005.10.010.",
    "steyerberg": "E. W. Steyerberg *et al.*, “Assessing the performance of prediction models: A framework for traditional and novel measures,” *Epidemiology*, vol. 21, no. 1, pp. 128–138, 2010, doi: 10.1097/EDE.0b013e3181c30fb2.",
    "brier": "G. W. Brier, “Verification of forecasts expressed in terms of probability,” *Mon. Weather Rev.*, vol. 78, no. 1, pp. 1–3, 1950, doi: 10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2.",
    "niculescu": "A. Niculescu-Mizil and R. Caruana, “Predicting good probabilities with supervised learning,” in *Proc. 22nd Int. Conf. Machine Learning (ICML)*, 2005, pp. 625–632, doi: 10.1145/1102351.1102430.",
    "lundberg": "S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in *Advances in Neural Information Processing Systems 30 (NIPS 2017)*, 2017, arXiv:1705.07874.",
    "ribeiro": "M. T. Ribeiro, S. Singh, and C. Guestrin, “‘Why should I trust you?’: Explaining the predictions of any classifier,” in *Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, 2016, pp. 1135–1144, doi: 10.1145/2939672.2939778.",
    "rudin": "C. Rudin, “Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead,” *Nat. Mach. Intell.*, vol. 1, no. 5, pp. 206–215, 2019, doi: 10.1038/s42256-019-0048-x.",
    "obermeyer": "Z. Obermeyer, B. Powers, C. Vogeli, and S. Mullainathan, “Dissecting racial bias in an algorithm used to manage the health of populations,” *Science*, vol. 366, no. 6464, pp. 447–453, 2019, doi: 10.1126/science.aax2342.",
    "tripod": "G. S. Collins *et al.*, “TRIPOD+AI statement: Updated guidance for reporting clinical prediction models that use regression or machine learning methods,” *BMJ*, vol. 385, Art. no. e078378, 2024, doi: 10.1136/bmj-2023-078378.",
    "pedregosa": "F. Pedregosa *et al.*, “Scikit-learn: Machine learning in Python,” *J. Mach. Learn. Res.*, vol. 12, pp. 2825–2830, 2011.",
    "hosmer": "D. W. Hosmer Jr., S. Lemeshow, and R. X. Sturdivant, *Applied Logistic Regression*, 3rd ed. Hoboken, NJ, USA: Wiley, 2013, doi: 10.1002/9781118548387.",
    "efron": "B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY, USA: Chapman & Hall, 1993.",
    "sdg3": "United Nations, “Goal 3: Ensure healthy lives and promote well-being for all at all ages,” Sustainable Development Goals. [Online]. Available: https://sdgs.un.org/goals/goal3 (accessed Oct. 27, 2026).",
}

TITLE = "DIABETES RISK PREDICTION SYSTEM USING MACHINE LEARNING AND EXPLAINABLE AI"

ABSTRACT = (
    f"Diabetes mellitus is a major and growing public-health problem, and early awareness of risk can prompt timely clinical testing. "
    f"This micro project develops an educational diabetes risk-estimation application that combines supervised machine learning with explainable AI. "
    f"The system is trained on the Pima Indians Diabetes Database (768 adult female records, eight numeric features, 34.9% labelled positive). "
    f"Physiologically impossible zero values in five measurements are treated as missing, and all preprocessing is performed inside a scikit-learn pipeline so that statistics are learned from training data only. "
    f"Seven candidates (a majority-class baseline, logistic regression, decision tree, random forest, gradient boosting, support vector machine and histogram gradient boosting) were tuned with stratified five-fold cross-validation on a 614-record training split. "
    f"Logistic regression achieved the highest cross-validated ROC-AUC ({COMP['Logistic Regression']['cv_roc_auc']:.3f} ± {COMP['Logistic Regression']['cv_roc_auc_std']:.3f}) and was selected, sigmoid-calibrated, and given a screening threshold of {META['threshold']:.3f} chosen from out-of-fold training predictions. "
    f"On the 154-record held-out test set it obtained ROC-AUC {T['roc_auc']:.3f} (95% bootstrap CI {ci('roc_auc')}), sensitivity {T['recall_sensitivity']:.3f}, specificity {T['specificity']:.3f}, precision {T['precision']:.3f} and Brier score {T['brier']:.3f}. "
    f"Permutation importance and SHAP-based local explanations show that plasma glucose is the strongest single predictor, while an exploratory training-only ablation shows that the other features still carry signal. "
    f"A Streamlit application provides validated input, a probability estimate, a per-prediction explanation and PDF/CSV report export, and 45 automated software tests pass. "
    f"The results come from one small, population-specific dataset without external validation; the system is therefore an educational prototype and not a diagnostic tool."
)
KEYWORDS = "Diabetes risk estimation; machine learning; logistic regression; probability calibration; SHAP; explainable AI; Pima Indians Diabetes Database; Streamlit."

B: list = []  # blocks
add = B.append

# =============================================================== CHAPTER 1
add(("ch", 1, "INTRODUCTION"))
add(("h2", "1.1", "Background of the Selected Problem"))
add(("p", "Diabetes is a chronic disease that occurs when the pancreas does not produce enough insulin or when the body cannot effectively use the insulin it produces [@who]. The World Health Organization (WHO) reports that the number of people living with diabetes rose from 200 million in 1990 to 830 million in 2022, and that diabetes was the direct cause of 1.6 million deaths in 2021 [@who]. The International Diabetes Federation (IDF) Diabetes Atlas, using a different methodology and an adult population aged 20–79 years, estimated a global prevalence of 10.5% (536.6 million people) in 2021 and projected 12.2% (783.2 million people) by 2045 [@idf]. Both sources describe a large and rising burden."))
add(("p", "Early risk assessment matters because diabetes can remain undiagnosed for some time, and Kaur and Kumari note that undiagnosed diabetes can increase the risk of serious complications such as stroke and diabetic nephropathy [@kaur]. A tool that helps a person or a student understand which measurements are associated with higher estimated risk may encourage appropriate confirmatory testing. Such a tool, however, can only *estimate* risk within the data it was built from; it cannot diagnose diabetes, which requires clinical testing and professional judgement."))
add(("p", "Machine learning (ML) is widely applied in diabetes research. A systematic review by Kavakiotis *et al.* found that prediction and diagnosis was the most popular application category, that about 85% of the methods used were supervised, that support vector machines were the most widely used algorithm and that clinical datasets were mainly used [@kavak]. A later review screened 107 publications on automated detection, diagnosis and self-management of diabetes and organised them by datasets, pre-processing, feature extraction, classification and performance measures [@chaki]. These reviews show that the technique is well established; they also show why quality of evaluation matters, since results depend heavily on the data and on how a model is validated."))
add(("p", "ML models also have well-known limitations in healthcare. They learn only from the data supplied, so a small or unrepresentative dataset limits generalisation; a model can be accurate but poorly calibrated, so that its probabilities cannot be taken at face value [@steyerberg]; and complex models can be difficult to interpret, which Rudin argues is a serious concern for high-stakes decisions [@rudin]. Reporting guidance such as TRIPOD+AI exists precisely because prediction models are often described incompletely [@tripod]."))
add(("p", "**Problem addressed.** This project asks a deliberately narrow, educational question: *how can a small public diabetes dataset be turned into a transparent, reproducible and honestly evaluated risk-estimation application whose every prediction is accompanied by an explanation and a clear statement of its limits?* The project does not claim to improve on clinical practice."))

add(("h2", "1.2", "Industry Relevance"))
add(("p", "Predictive analytics is used in healthcare for risk stratification, prioritising people for screening, population-health management and clinical decision support. The value of such systems depends on more than accuracy. Obermeyer *et al.* showed that a widely used commercial algorithm exhibited substantial racial bias because it used health-care cost as a proxy for health need, which illustrates how design choices that look technical can have large equity consequences [@obermeyer]. The following considerations shaped the design of this project."))
add(("bul", [
    "**Interpretability.** Rudin argues for inherently interpretable models in high-stakes settings rather than post-hoc explanations of black boxes [@rudin]. This project therefore compares complex models against logistic regression and prefers the simpler model when performance is statistically indistinguishable (Section 3.7).",
    "**Reliability and calibration.** Steyerberg *et al.* recommend that discrimination and calibration should always be reported for a prediction model [@steyerberg]. The project reports ROC-AUC, PR-AUC, the Brier score and a calibration curve.",
    "**Privacy.** Health data are sensitive. The application requests no names or identifiers, sends nothing to third-party services and keeps history only in the browser session.",
    "**Fairness and representativeness.** The dataset covers only adult women of Pima Indian heritage; results cannot be assumed to hold for other groups (Section 5.12).",
    "**Clinical validation and reporting.** TRIPOD+AI describes expected reporting for prediction models [@tripod]. A clinically deployable product would additionally require external and prospective validation and regulatory review, which are outside the scope of this project.",
]))
add(("tbl", "proto", "Educational prototype (this project) compared with a clinically deployable product.",
     ["Aspect", "This project (educational prototype)", "Clinically deployable product"],
     [["Data", "768 records, one historical study", "Large, representative, current, multi-site data"],
      ["Validation", "Internal: cross-validation and one held-out test split", "External and prospective validation, subgroup analysis"],
      ["Regulation", "None claimed", "Regulatory assessment and quality management"],
      ["Monitoring", "Not implemented", "Continuous performance and drift monitoring"],
      ["Intended use", "Learning and demonstration only", "Defined clinical use case and workflow"]],
     [1500, 3900, 4000], {}))

add(("h2", "1.3", "Aim and Objective of the Micro Project"))
add(("p", "**Aim.** To design, implement and evaluate an educational, explainable machine-learning application that estimates diabetes risk from structured health measurements, and to document its methodology, results and limitations honestly."))
add(("p", "The measurable objectives, and the implemented feature or evidence corresponding to each, are listed in {T:obj}."))
add(("tbl", "obj", "Objectives and the implemented features that address them.",
     ["No.", "Objective", "Implemented feature (module)", "Evidence"],
     [["O1", "Analyse a documented diabetes dataset", "Dataset download, schema check and profiling (`data_loader.py`)", "`artifacts/data_profile.json`; Section 3.2"],
      ["O2", "Build a reproducible preprocessing pipeline", "Zero-to-missing conversion, median imputation, scaling inside one pipeline (`preprocessing.py`)", "4 preprocessing tests; Section 3.4"],
      ["O3", "Train and compare ML models", "Seven candidates, one CV protocol (`train.py`)", "{T:cv}"],
      ["O4", "Evaluate with suitable metrics", "Metrics, bootstrap CIs, curves (`evaluate.py`)", "{T:test}"],
      ["O5", "Explain predictions", "SHAP permutation explainer with fallback (`explainability.py`)", "Additivity test; Section 5.9"],
      ["O6", "Provide an interactive, validated application", "Streamlit app with input validation (`app.py`, `validation.py`)", "{F:home}–{F:pred}; 16 validation tests"],
      ["O7", "Export a downloadable report", "PDF and CSV generation (`report_generator.py`)", "3 report tests; {F:report}"],
      ["Future", "External validation, fairness analysis, deployment hardening", "Not implemented", "Section 6.3"]],
     [700, 2500, 3600, 2600], {"sz": 18}))

add(("h2", "1.4", "Link to SDG / KITS Technology Mission"))
add(("p", "**United Nations Sustainable Development Goal 3.** SDG 3 is titled “Ensure healthy lives and promote well-being for all at all ages” [@sdg3]. Its Target 3.4 aims, by 2030, to reduce by one third premature mortality from non-communicable diseases through prevention and treatment and to promote mental health and well-being [@sdg3]. Diabetes is a non-communicable disease, so risk awareness and prevention fall within the scope of that target."))
add(("p", "The project’s connection to SDG 3 is modest and educational. It demonstrates how an understandable risk-estimation tool could support *awareness* of diabetes risk factors, and it models good practice (transparency, calibration, privacy, explicit limitations) that responsible health-AI work requires. It does not treat or diagnose anyone, it has no measured impact on health outcomes, and no such impact is claimed."))
add(("p", "**KITS Technology Mission.** [[TO BE COMPLETED BY THE STUDENT: the KITS Technology Mission framework/theme was not included in the template or project files. Insert the relevant mission statement and one or two sentences linking this project to it.]]"))

# =============================================================== CHAPTER 2
add(("ch", 2, "LITERATURE REVIEW"))
add(("h2", "2.1", "Scope and Approach"))
add(("p", "This chapter reviews (i) existing diabetes-prediction approaches, particularly those that use the same Pima dataset, (ii) the evaluation concepts that this project relies on (class imbalance, discrimination, calibration and thresholds) and (iii) explainability, fairness and reporting concerns. Sources were chosen from peer-reviewed journals and conference proceedings and verified against Crossref and PubMed records. The review is a focused, selective one prepared for a micro project; it is **not** a systematic review, and statements about individual studies are based on their published abstracts and the cited details."))
add(("h2", "2.2", "Machine Learning in Diabetes Research"))
add(("p", "Kavakiotis *et al.* reviewed applications of ML and data-mining tools in diabetes research, grouped into prediction and diagnosis, diabetic complications, genetic background and environment, and health-care management, with prediction and diagnosis the most popular [@kavak]. They report that 85% of the algorithms used were supervised and 15% unsupervised (association rules), that support vector machines were the most successful and widely used algorithm, and that clinical datasets predominated [@kavak]. Chaki *et al.* reviewed 107 publications from Scopus and PubMed on detection, diagnosis and self-management and organised the literature into datasets, pre-processing, feature extraction, ML-based classification, AI-based assistants and performance measures; they also list open research issues in the field [@chaki]. Together these reviews justify the choice of supervised classification and the inclusion of SVMs among the candidates in this project."))
add(("h2", "2.3", "Studies Using the Pima Indians Diabetes Database"))
add(("p", "The Pima Indians Diabetes Database originates from a National Institute of Diabetes and Digestive and Kidney Diseases study and was donated to the UCI repository in 1990; its documentation records 768 instances, all female patients at least 21 years old of Pima Indian heritage [@uci]. In the original use of the data, Smith *et al.* applied the ADAP learning algorithm, which produced a real-valued prediction converted to a binary decision using a cut-off of 0.448; the dataset documentation reports sensitivity and specificity of 76% on 192 held-out instances after training on 576 [@smith][@uci]."))
add(("p", "Many later studies use the same data. Sisodia and Sisodia compared decision tree, SVM and naïve Bayes on this database using precision, accuracy, F-measure and recall, reporting that naïve Bayes achieved the highest accuracy (76.30%) and verifying results with ROC curves [@sisodia]. Kaur and Kumari developed five models (linear-kernel SVM, RBF-kernel SVM, k-nearest neighbour, artificial neural network and multifactor dimensionality reduction) on the same data using R [@kaur]. Khanam and Foo applied seven ML algorithms and a neural network to the 768-patient dataset; they report that logistic regression and SVM performed well and that a neural network with two hidden layers reached 88.6% accuracy [@khanam]. The accuracy figures of different studies are not directly comparable, because the studies use different data splits, preprocessing choices and protocols."))
add(("h2", "2.4", "Evaluation, Class Imbalance, Calibration and Thresholds"))
add(("p", "Class imbalance and the choice of metrics affect how results should be read. Fawcett describes ROC analysis, including the area under the ROC curve as a threshold-independent summary of ranking quality [@fawcett]. Saito and Rehmsmeier show that ROC plots can be visually deceptive on imbalanced data and that precision–recall plots can give a more accurate picture of future classification performance because they involve the fraction of true positives among positive predictions [@saito]. Steyerberg *et al.* review traditional measures, namely the Brier score for overall performance, the concordance statistic for discrimination and goodness-of-fit measures for calibration, and recommend that discrimination and calibration should always be reported [@steyerberg]. The Brier score itself was introduced by Brier for verifying probability forecasts [@brier]."))
add(("p", "Probability calibration is a separate concern from discrimination. Niculescu-Mizil and Caruana studied the quality of probabilities produced by supervised learning methods and compared calibration methods such as Platt scaling (sigmoid) and isotonic regression [@niculescu]. This motivates the sigmoid calibration and the calibration curve used in this project. Choosing a decision threshold is a separate step: a default of 0.5 is not necessarily appropriate for a screening-style tool that prefers to miss fewer cases, so the threshold here is chosen explicitly from training-set predictions (Section 3.8)."))
add(("h2", "2.5", "Explainable AI, Fairness and Reporting"))
add(("p", "Lundberg and Lee introduced SHAP, a unified framework that assigns each feature an additive contribution to an individual prediction [@lundberg]. Ribeiro *et al.* proposed LIME, which explains individual predictions by fitting a local interpretable approximation [@ribeiro]. Rudin cautions that explaining a black-box model is not the same as using an inherently interpretable one and that explanations can be misleading in high-stakes settings [@rudin]. Obermeyer *et al.* provide a concrete example of how an algorithm’s choice of target variable can embed bias [@obermeyer]. TRIPOD+AI provides updated reporting guidance for clinical prediction models built with regression or ML [@tripod]. These works motivate three design decisions: prefer an interpretable model when performance is comparable, attach explanations to every prediction while stating that they are associations, and document limitations explicitly."))
add(("tbl", "lit", "Comparative summary of the principal reviewed works.",
     ["Ref.", "Objective / focus", "Data and method", "Principal finding (as reported)", "Relevance / limitation"],
     [["[@kavak]", "Review of ML in diabetes research", "Systematic review of applications and tools", "Prediction/diagnosis most popular; 85% supervised; SVM most used", "Supports supervised models; not a performance benchmark"],
      ["[@chaki]", "Review of detection, diagnosis and self-management", "107 publications (Scopus, PubMed)", "Organises field by data, preprocessing, models and metrics; lists open issues", "Motivates careful preprocessing and metrics"],
      ["[@sisodia]", "Early diabetes prediction", "Pima data; decision tree, SVM, naïve Bayes", "Naïve Bayes highest accuracy, 76.30%", "Accuracy-centred in abstract; calibration not mentioned there"],
      ["[@kaur]", "Diabetes classification in R", "Pima data; five models (SVM-linear, SVM-RBF, k-NN, ANN, MDR)", "Comparative evaluation of five models", "Numerical results not reproduced here"],
      ["[@khanam]", "Compare ML algorithms", "Pima data (768 patients); seven ML algorithms and NN", "LR and SVM work well; two-hidden-layer NN reached 88.6% accuracy", "Protocol-specific accuracy; not comparable to this work"],
      ["[@smith]", "Original use of the data", "ADAP algorithm; 576 train / 192 test", "Sensitivity and specificity about 76%", "Historical; different method and split"],
      ["[@saito]", "ROC vs. PR on imbalanced data", "Analytical and empirical study", "PR plots more informative on imbalanced data", "Motivates reporting PR-AUC"],
      ["[@steyerberg]", "Performance of prediction models", "Framework of traditional and novel measures", "Report discrimination and calibration always", "Motivates Brier score and calibration plot"],
      ["[@niculescu]", "Probability quality", "Compares supervised learners and calibration methods", "Calibration affects probability quality", "Motivates sigmoid calibration"],
      ["[@lundberg]", "Model explanation", "SHAP additive feature attributions", "Unified additive explanation framework", "Basis of local explanations"],
      ["[@rudin]", "Interpretability in high-stakes use", "Position paper", "Prefer inherently interpretable models", "Motivates choosing logistic regression"],
      ["[@obermeyer]", "Bias in a health algorithm", "Analysis of a commercial algorithm", "Cost used as proxy for need created racial bias", "Motivates fairness caution"]],
     [800, 1700, 2100, 2500, 2300], {"sz": 17}))
add(("h2", "2.6", "Research Gap and Contribution of this Project"))
add(("p", "From the studies reviewed, a consistent pattern is visible in the Pima-based work: the abstracts of [@sisodia], [@kaur] and [@khanam] emphasise classifier comparison and, where numbers are given, accuracy. Meanwhile the evaluation literature recommends reporting discrimination *and* calibration [@steyerberg], using precision–recall information on imbalanced data [@saito], preferring interpretable models in high-stakes settings [@rudin] and reporting limitations transparently [@tripod]. The abstracts reviewed do not mention probability calibration, uncertainty intervals or per-prediction explanations. Because only abstracts and cited details were examined, this should be read as a **gap in what was reviewed**, not as a claim that no prior study addresses these aspects."))
add(("p", "This project does not claim scientific novelty. Its contribution is educational and technical: it integrates, in one reproducible and tested software artefact, (i) a leakage-safe evaluation protocol, (ii) a consistent comparison of seven candidates, (iii) probability calibration with an explicit screening threshold, (iv) bootstrap confidence intervals, (v) additive local explanations and (vi) an application with input validation and exportable reports, while documenting the dataset’s limitations."))

# =============================================================== CHAPTER 3
add(("ch", 3, "METHODOLOGY"))
add(("h2", "3.1", "Problem Formulation"))
add(("p", "The task is supervised binary classification. Let *x* ∈ ℝ^{8} be the vector of eight measurements and *y* ∈ {0, 1} the label, where *y* = 1 indicates that the person was labelled diabetic in the dataset. The goal is a function that returns an estimated probability p̂ = P(*y* = 1 | *x*) and a screening flag obtained by comparing p̂ with a threshold τ. The probability is an estimate *within the dataset’s population*; it is not a personal clinical risk."))
add(("h2", "3.2", "Dataset Provenance and Characteristics"))
add(("p", "The data are the Pima Indians Diabetes Database from the National Institute of Diabetes and Digestive and Kidney Diseases, donated to the UCI repository in 1990 and mirrored on OpenML (dataset 37), where the licence field is “Public” [@uci]. The file used by this project was downloaded on 26 October 2026 and its SHA-256 digest is recorded in `data/raw/provenance.json` (779e408f…c655b49). The cohort comprises 768 females aged at least 21 years of Pima Indian heritage living near Phoenix, Arizona, USA [@uci]. The class variable is 1 for “tested positive for diabetes” according to the dataset documentation, which states that the diagnostic variable follows WHO criteria, namely 2-hour post-load plasma glucose of at least 200 mg/dL at any survey examination or when found during routine medical care [@uci]. The documentation does not state when the recorded measurements were taken relative to that classification, and the highest recorded glucose in the file is 199 mg/dL, so the target is described in this report as *recorded diabetes status* and not as future onset. There are 268 positive (34.9%) and 500 negative records ({F:profile}). The OpenML licence field should be verified against the terms of the original source before any redistribution of the raw file; for that reason the raw data are not committed to the project repository."))
rows = []
desc = {"Pregnancies": "Number of times pregnant", "Glucose": "Plasma glucose concentration 2 h after an oral glucose tolerance test",
        "BloodPressure": "Diastolic blood pressure (mm Hg)", "SkinThickness": "Triceps skin-fold thickness (mm)",
        "Insulin": "2-hour serum insulin (mu U/ml)", "BMI": "Body mass index (kg/m²)", "DiabetesPedigreeFunction": "Diabetes pedigree function (study-specific family-history score)",
        "Age": "Age (years)"}
for f, d in desc.items():
    s = PROF["feature_summary"][f]
    rows.append([f"`{f}`", d, f"{s['min']:g} – {s['max']:g}", f"{s['median']:g}", str(PROF["zero_counts"][f])])
add(("tbl", "features", "Input features of the Pima dataset (computed from the 768 raw records).",
     ["Feature", "Description", "Min – max (raw)", "Median", "Zeros"], rows, [2700, 3400, 1300, 900, 900], {"sz": 18, "aligns": ["left", "left", "center", "center", "center"]}))
add(("p", "The dataset documentation does not state the unit of the glucose variable; the application form labels it mg/dL, which is the conventional unit for the 2-hour oral-glucose-tolerance reading, and this assumption is noted as a limitation. The *Diabetes Pedigree Function* is a score specific to the original study and is not a standard clinical measure; it is therefore optional in the application."))
add(("fig", "profile", "data_profile.png", "Class distribution and number of zero values treated as missing for each feature (source: `artifacts/data_profile.json`).", 6.0, "Class distribution and zero counts of the Pima dataset."))
add(("h2", "3.3", "Data-Quality Checks and Handling of Invalid Measurements"))
add(("p", "The profiling step (`profile_dataset`) found no null cells and no duplicate rows. However, five measurements contain zeros that are physiologically impossible for a living person: plasma glucose (5 records), diastolic blood pressure (35), triceps skin-fold thickness (227), serum insulin (374) and BMI (11). The dataset’s documentation states “Missing Attribute Values: None”, so these zeros are an encoding of missing measurements rather than true values [@uci]. By contrast, zero pregnancies (111 records) is valid and is left unchanged. Roughly 49% of insulin and 30% of skin-fold values are missing, so imputed values for these two features carry little information; this is later reflected in their negligible importance (Section 5.9)."))
add(("p", "Handling is implemented as the first pipeline step (`ZeroToNaN`), which converts zeros in the five configured columns to missing values; a median imputer then replaces them using training-split medians. The application never silently substitutes zero for a blank field: blank optional inputs are passed as missing and the user is told that training medians were used (Section 4.7)."))
add(("h2", "3.4", "Training/Test Split and Preprocessing Pipeline"))
add(("p", "The 768 records were split once with a stratified 80/20 split (`random_state` = 42) into a training set of 614 records (214 positive, 400 negative; 34.9% positive) and a held-out test set of 154 records (54 positive, 100 negative). The test set is not used for tuning, model selection, calibration or threshold selection."))
add(("p", "Preprocessing is a scikit-learn `Pipeline` consisting of (1) `ZeroToNaN`, (2) median imputation and (3) standardisation of all eight features, followed by the classifier. Because all steps are inside the pipeline, their parameters are learned from training data only: within cross-validation they are refitted on each training fold, and the saved model applies the same fitted parameters at prediction time. For a feature value *x*, the standardised value is"))
add(("eq", "zscore", msub(mr("z"), mr("j")) + mr(" = ") + mfrac(msub(mr("x"), mr("j")) + mr(" − ") + msub(mr("μ"), mr("j")), msub(mr("σ"), mr("j")))))
add(("p", "where μ_{j} and σ_{j} are the training-set mean and standard deviation of feature *j* after imputation. Median imputation replaces a missing value of feature *j* with the training median of that feature. No categorical encoding is required because all eight features are numeric, and no resampling is used: the 35/65 class imbalance is handled through appropriate metrics and, for logistic regression, an optional class-weight setting chosen by cross-validation."))
add(("tbl", "leak", "Where each operation is fitted and whether the test set is involved.",
     ["Operation", "Fitted or decided on", "Uses test set?"],
     [["Zero → missing conversion", "Stateless rule (no fitting)", "No"],
      ["Median imputation and scaling", "Training folds / training split", "No"],
      ["Hyperparameter search", "5-fold CV on training split", "No"],
      ["Model selection (CV ROC-AUC, one-SE rule)", "CV results on training split", "No"],
      ["Calibration decision and sigmoid fit", "Training split (out-of-fold Brier)", "No"],
      ["Decision threshold", "Out-of-fold training predictions", "No"],
      ["Final performance, bootstrap CIs", "Held-out test split", "Yes, once"],
      ["Permutation importance (descriptive)", "Held-out test split", "Yes, descriptive only"]],
     [4000, 3500, 1900], {}))
add(("h2", "3.5", "Candidate Models and Hyperparameter Search"))
add(("p", "Seven candidates were compared under one protocol ({T:grid}). A majority-class baseline (`DummyClassifier` with the class prior) provides a reference. Logistic regression models the log-odds of the positive class as a linear function of the standardised inputs,"))
add(("eq", "logit", mr("P(y = 1 | x) = ") + mfrac(mr("1"), mr("1 + ") + msup(mr("e"), mr("−(") + msub(mr("β"), mr("0")) + mr(" + ") + msup(mr("β"), mr("T")) + mr("x)"))) ))
add(("p", "and is fitted by minimising the L2-regularised logistic loss; in scikit-learn the parameter *C* is the inverse regularisation strength, so a smaller *C* means stronger regularisation [@pedregosa][@hosmer]. Decision trees, random forests and gradient-boosting methods are tree-based models; the SVM uses a radial-basis-function kernel, with probabilities obtained through a calibration wrapper."))
add(("tbl", "grid", "Candidate models and the hyperparameter grids searched (all with 5-fold stratified CV, random seed 42).",
     ["Model", "Hyperparameter grid", "Combinations"],
     [["Baseline (majority class)", "Class prior only", "1"],
      ["Logistic Regression", "C ∈ {0.01, 0.1, 1, 10}; class_weight ∈ {none, balanced}", "8"],
      ["Decision Tree", "max_depth ∈ {2, 3, 4, 6}; min_samples_leaf ∈ {5, 15, 30}", "12"],
      ["Random Forest (300 trees)", "max_depth ∈ {3, 5, none}; min_samples_leaf ∈ {3, 8}", "6"],
      ["Gradient Boosting", "n_estimators ∈ {50, 100, 200}; learning_rate ∈ {0.03, 0.1}; max_depth ∈ {2, 3}", "12"],
      ["SVM (RBF)", "C ∈ {0.3, 1, 3}; gamma ∈ {scale, 0.05}; calibrated wrapper", "6"],
      ["HistGradientBoosting", "learning_rate ∈ {0.03, 0.1}; max_depth ∈ {2, 3}; max_iter ∈ {100, 200}; l2 ∈ {0, 1}", "16"]],
     [2400, 5700, 1300], {"sz": 19, "aligns": ["left", "left", "center"]}))
add(("h2", "3.6", "Cross-Validation"))
add(("p", "Every candidate was tuned with `GridSearchCV` using stratified 5-fold cross-validation on the 614-record training set (shuffled, seed 42). For each parameter combination the following scores were averaged over the five validation folds: ROC-AUC (the refit criterion), PR-AUC (average precision), Brier score, recall at a 0.5 threshold and accuracy. Because the best combination is picked from the same folds that score it, the reported cross-validated score is slightly optimistic; this is one reason the held-out test set is kept separate."))
add(("h2", "3.7", "Final Model Selection and Probability Calibration"))
add(("p", "The selection rule is: take the model with the highest mean cross-validated ROC-AUC; among all models whose mean ROC-AUC lies within one standard error (SE = SD/√5) of that best value, choose the one with the lowest interpretability rank (baseline < logistic regression < decision tree < random forest < gradient boosting < SVM < histogram gradient boosting). In the recorded run, logistic regression had both the best mean ROC-AUC and the lowest rank among eligible models, so the rule selected it."))
add(("p", "Sigmoid (Platt-type) calibration maps a classifier’s raw score *s* to a probability [@niculescu]:"))
add(("eq", "platt", msub(mr("p"), mr("cal")) + mr(" = ") + mfrac(mr("1"), mr("1 + exp(A·s + B)"))))
add(("p", "where *A* and *B* are fitted on held-out folds. The project fits `CalibratedClassifierCV` with five stratified folds; the final model is an average over the five fitted logistic-regression/sigmoid pairs. Calibration is kept only if it lowers the out-of-fold Brier score on the training split; in the recorded run the score improved from {BR0} to {BR1}, so calibration was retained."))
add(("h2", "3.8", "Decision-Threshold Selection"))
add(("p", "A risk-estimation tool intended for screening-style awareness should favour sensitivity, since a missed case is generally more costly than an additional follow-up. The threshold τ^{*} is therefore chosen as the largest value for which the out-of-fold sensitivity on the training split is at least 0.80:"))
add(("eq", "thr", msup(mr("τ"), mr("*")) + mr(" = max{ τ : ") + msub(mr("Sens"), mr("OOF")) + mr("(τ) ≥ 0.80 }")))
add(("p", "In the recorded run τ^{*} = {THR}. This is an *operating point* of this model on this dataset and is not an established medical cut-off; consequently the application reports “at or above / below the model’s screening threshold” and does not assign low/medium/high categories."))
add(("h2", "3.9", "Evaluation Metrics"))
add(("p", "Let TP, FP, TN and FN be the true-positive, false-positive, true-negative and false-negative counts at threshold τ^{*}, and *N* the number of records. The metrics are defined below ({T:metrics} gives practical meanings)."))
add(("eq", "sens", mr("Sensitivity (recall) = ") + mfrac(mr("TP"), mr("TP + FN"))))
add(("eq", "spec", mr("Specificity = ") + mfrac(mr("TN"), mr("TN + FP"))))
add(("eq", "prec", mr("Precision = ") + mfrac(mr("TP"), mr("TP + FP")) + mr(",    ") + msub(mr("F"), mr("1")) + mr(" = ") + mfrac(mr("2 · Precision · Recall"), mr("Precision + Recall"))))
add(("eq", "acc", mr("Accuracy = ") + mfrac(mr("TP + TN"), mr("N"))))
add(("eq", "brier", mr("Brier = ") + mfrac(mr("1"), mr("N")) + msum(mr("i=1"), mr("N"), msup(mparen(msub(mr("p"), mr("i")) + mr(" − ") + msub(mr("y"), mr("i"))), mr("2")))))
add(("eq", "auc", mr("ROC-AUC = P(") + msub(mr("s"), mr("+")) + mr(" > ") + msub(mr("s"), mr("−")) + mr(")")))
add(("tbl", "metrics", "Evaluation metrics and their practical meaning.",
     ["Metric", "Meaning in this project"],
     [["Sensitivity", "Of the people labelled positive, the fraction the model flags. Low sensitivity means missed cases (false negatives)."],
      ["Specificity", "Of the people labelled negative, the fraction not flagged. Low specificity means false alarms."],
      ["Precision", "Of the people flagged, the fraction labelled positive. Depends on prevalence."],
      ["F1-score", "Harmonic mean of precision and recall; balances the two."],
      ["Accuracy", "Fraction of correct decisions; can mislead when classes are imbalanced."],
      ["ROC-AUC", "Probability that a random positive receives a higher score than a random negative; threshold-free [@fawcett]."],
      ["PR-AUC", "Area under the precision–recall curve (average precision); informative with imbalance [@saito]."],
      ["Brier score", "Mean squared error of the predicted probabilities; lower is better [@brier]. A constant prediction of the prevalence scores about 0.227 here."],
      ["Calibration curve", "Observed positive fraction against mean predicted probability in bins; a diagonal line is ideal."]],
     [1900, 7500], {}))
add(("p", "Here s_{+} and s_{−} are the scores of a randomly chosen positive and negative record. Because the test set is small, 95% confidence intervals were computed with a stratified percentile bootstrap [@efron]: positives and negatives are resampled separately with replacement 1000 times (seed 42), each metric is recomputed at the fixed threshold τ^{*} and the 2.5th and 97.5th percentiles are reported."))
add(("h2", "3.10", "Explainability Methodology"))
add(("p", "Two complementary explanations are produced. **Global:** permutation importance on the held-out test set measures the decrease in ROC-AUC when one feature is shuffled (30 repeats); it describes how much the fitted model relies on a feature. **Local:** for each prediction the application uses SHAP’s permutation explainer [@lundberg] on the *entire saved pipeline’s predicted probability*, with a 100-row sample of the training data as the background distribution. SHAP contributions are additive in probability units:"))
add(("eq", "shap", mr("p(x) = ") + msub(mr("φ"), mr("0")) + mr(" + ") + msum(mr("j=1"), mr("8"), msub(mr("φ"), mr("j")))))
add(("p", "where φ_{0} is the average model output over the background sample and φ_{j} is the contribution of feature *j* to this prediction. If SHAP fails for any reason, a simpler occlusion explanation is used (each feature replaced in turn by its background median) and the method name is shown. In all cases the explanation describes how the model uses its inputs; it does not establish causation, and correlated inputs can share or distort contributions."))
add(("h2", "3.11", "System Workflow"))
add(("p", "{F:workflow} shows the two flows of the system. Offline training (`python -m src.train`) runs once, writes the model and metrics, and performs the single test evaluation. At prediction time, the Streamlit application loads the saved pipeline, validates the user’s input, applies the same preprocessing, computes a calibrated probability, compares it with the threshold, computes the SHAP explanation and offers a report. The application never retrains at start-up."))
add(("fig", "workflow", "workflow.png", "System workflow: (A) offline training and (B) prediction-time inference.", 6.3, "Workflow diagram of offline training and prediction-time inference."))
add(("fig", "split", "split_protocol.png", "Data split and validation protocol used for tuning, selection and final evaluation.", 5.8, "Split and cross-validation diagram."))
add(("h2", "3.12", "Ethical Considerations and Limitations of the Method"))
add(("bul", [
    "**Not diagnostic.** The application states on every page and report that it is an educational estimate and not a diagnosis.",
    "**Data representativeness.** All training records come from one study of adult women of Pima heritage; no claim is made for other populations.",
    "**Label definition.** The documented label rule is a glucose-tolerance criterion applied at any survey examination or in routine care; its timing relative to the recorded features is not documented, so the target is treated as recorded diabetes status and not as future onset.",
    "**Privacy.** No identifiers are collected; health inputs are not sent to third parties; reports are generated in memory.",
    "**No clinical validation.** Internal validation on one test split cannot establish clinical usefulness [@tripod].",
]))

# =============================================================== CHAPTER 4
add(("ch", 4, "FABRICATION/SIMULATION/PROGRAM OR CODE/DESIGN"))
add(("p", "This project is a software system, so this chapter documents the *program and design*: the development environment, structure, modules, interface, testing and execution. Code excerpts below are copied verbatim from the project files."))
add(("h2", "4.1", "Development Environment and Tools"))
add(("tbl", "env", "Software environment used to produce and verify the results.",
     ["Component", "Version / detail"],
     [["Operating system", "Windows 11 Home (AMD64 processor); CPU only, no GPU"],
      ["Python", f"{META['versions']['python']} (virtual environment)"],
      ["scikit-learn", f"{META['versions']['scikit_learn']} [@pedregosa]"],
      ["pandas / NumPy / SciPy", f"{META['versions']['pandas']} / {META['versions']['numpy']} / 1.18.1"],
      ["SHAP", "0.54.1 [@lundberg]"],
      ["Streamlit / Plotly", "1.66.1 / 7.1.0"],
      ["Matplotlib / ReportLab", "3.11.2 / 5.1.0"],
      ["joblib / PyYAML", "1.6.0 / 6.0.3"],
      ["pytest / Ruff", "9.1.1 / 0.17.2"]],
     [3000, 6400], {}))
add(("h2", "4.2", "Hardware and Software Requirements"))
add(("bul", [
    "**Hardware:** any modern laptop or desktop CPU; no GPU is required. Training the seven candidates took roughly 25 seconds on the development machine (from log timestamps).",
    "**Software:** Python 3.12, the packages in `requirements.txt`, and a web browser. Internet access is needed only once, to download the dataset from OpenML.",
    "**Optional:** Docker, for container-based deployment (a `Dockerfile` is provided; see Section 4.12).",
]))
add(("h2", "4.3", "Project Directory Structure"))
add(("code", """diabetes-risk-prediction/
|-- app.py                  Streamlit application (5 pages)
|-- config/config.yaml      seed, paths, CV folds, threshold target
|-- src/
|   |-- config.py           configuration loader, logging
|   |-- data_loader.py      download, schema check, profiling
|   |-- preprocessing.py    ZeroToNaN + imputer + scaler pipeline
|   |-- train.py            tuning, selection, calibration, test
|   |-- evaluate.py         metrics, bootstrap CI, figures
|   |-- validation.py       input field specifications and checks
|   |-- predict.py          Predictor class (loads saved model)
|   |-- explainability.py   SHAP / occlusion explanations
|   `-- report_generator.py PDF and CSV reports
|-- ui/                     components.py, styles.css
|-- tests/                  7 test files, 45 tests
|-- models/  artifacts/     generated model, metrics, figures
|-- docs/                   dataset card, model card, methodology ...
|-- Dockerfile, requirements.txt, README.md"""))
add(("h2", "4.4", "System Architecture"))
add(("p", "The presentation layer (`app.py`, `ui/`) calls four service modules: input validation, the predictor, the explainer and the report generator. The predictor and explainer both depend on the single saved artefact `models/model.joblib`, which bundles the fitted pipeline, a 100-row background sample and metadata (feature order, threshold, training prevalence and feature ranges). Training-time modules are used only by `src.train` ({F:arch})."))
add(("fig", "arch", "architecture.png", "Software architecture of the system (modules and their dependencies).", 6.0, "Architecture diagram of the application modules."))
add(("h2", "4.5", "Dataset Loading and Preprocessing Implementation"))
add(("p", "`data_loader.py` downloads the dataset with `sklearn.datasets.fetch_openml`, renames OpenML’s column names to the project’s names, converts the target to 0/1, caches a CSV and writes the provenance record. `check_schema` rejects empty data, missing columns, non-numeric features and non-binary targets; these paths are covered by tests. The zero-to-missing rule is a small scikit-learn transformer:"))
add(("code", src("src/preprocessing.py", "class ZeroToNaN", "def build_preprocessor")))
add(("p", "The transformer is stateless: it only converts zeros in the five configured columns. Because `build_model_pipeline` places it in the same pipeline as the imputer, scaler and classifier, the saved model applies exactly the same preprocessing as training."))
add(("h2", "4.6", "Model-Training Module"))
add(("p", "`train.py` performs the protocol of Chapter 3: split, grid searches, selection, calibration decision, threshold choice and a single test evaluation, and then writes `model.joblib`, `metadata.json`, `metrics.json`, `model_comparison.csv` and figures. The threshold rule of Section 3.8 is implemented as follows:"))
add(("code", src("src/train.py", "def choose_threshold", "def run(")))
add(("p", "The function scans the unique out-of-fold probabilities and keeps the largest one whose sensitivity meets the target. A unit test checks that the resulting threshold achieves the target sensitivity on simulated data."))
add(("h2", "4.7", "Prediction Module, Validation and Error Handling"))
add(("p", "`validation.py` defines a `FieldSpec` for each input (label, unit, help text, range, required flag, integer flag). `validate_inputs` returns a result object with cleaned values or field-specific error messages; it rejects unknown fields, non-numeric text, booleans, NaN/Inf, out-of-range values (for example glucose of 0 or 900) and fractional values for integer fields. Blank optional fields become NaN so that the pipeline imputes them. The ranges are plausibility limits for catching typing or unit errors; they are not clinical reference ranges."))
add(("p", "`Predictor` in `predict.py` loads the saved bundle once, raises `ModelNotFoundError` with a clear message when the artefact is missing or corrupt, and exposes `predict`:"))
add(("code", src("src/predict.py", "def predict(self", None)))
add(("p", "Invalid input raises `InvalidInputError`, whose message is shown to the user; unexpected exceptions in the app are logged without health values and replaced by a generic message. The predictor also warns when a value lies outside the range seen in training and lists the fields that were imputed."))
add(("h2", "4.8", "Explainability Module"))
add(("p", "`explain_prediction` applies SHAP’s permutation explainer to the complete pipeline’s probability output, so the explanation corresponds to the number the user sees. The core of the implementation is:"))
add(("code", src("src/explainability.py", "        def f(a", "    except Exception")))
add(("p", "The contributions are sorted by magnitude and converted to a short non-causal sentence. A test asserts that the baseline value plus the sum of the contributions equals the predicted probability (to six decimal places), and another test forces SHAP to fail and verifies that the occlusion fallback is used."))
add(("h2", "4.9", "Streamlit Interface and Model-Insights Visualisations"))
add(("p", "The interface has five pages: *Home* (summary, key test metrics and disclaimer), *Risk Estimation* (validated form, probability, explanation and report download), *Model Insights* (comparison table, test metrics with confidence intervals, confusion matrix, ROC, PR, calibration and importance plots), *Session History* (in-memory table with a clear button) and *About* (method, limits and privacy). {F:home} to {F:insights} show the implemented application; all screenshots were captured from the running application with illustrative inputs, not patient data."))
add(("fig", "home", "SHOT:01_home.png", "Home page of the application (captured from the running app).", 6.0, "Screenshot of the Home page showing project title, disclaimer and key metrics."))
add(("fig", "valerr", "SHOT:03c_validation_error.png", "Risk Estimation page showing a validation error for a non-numeric entry in an optional field.", 6.0, "Screenshot of the Risk Estimation form with a validation error message."))
add(("fig", "pred", "SHOT:04c_prediction.png", "Prediction screen for an illustrative input (pregnancies 1, glucose 150, BMI 33.5, age 45; optional fields blank), with the SHAP-based explanation and report downloads.", 4.6, "Screenshot of the prediction result with probability and contribution chart."))
add(("fig", "insights", "SHOT:05a_insights_tables.png", "Model Insights page (upper part): cross-validated model comparison and held-out test metrics with 95% confidence intervals.", 6.0, "Screenshot of the Model Insights tables."))
add(("h2", "4.10", "PDF and CSV Report Generation"))
add(("p", "`report_generator.py` builds the report in memory (no file is written to the server): a timestamp, model name and version, the submitted inputs, the probability and threshold interpretation, the contribution table, a plain-language explanation, the disclaimer and the dataset limitations. The PDF uses ReportLab and the CSV uses the standard library. {F:report} shows the first page of a report generated by the application for the example input of {F:pred}."))
add(("fig", "report", "sample_report_page.png", "First page of the PDF report generated by the application for the illustrative input (rendered from `report/sample_report.pdf`).", 4.3, "First page of the generated PDF report."))
add(("h2", "4.11", "Testing Approach"))
add(("p", "The 45 automated tests (pytest) check software behaviour: dataset loading and schema errors, zero-handling and imputer fitting, input validation and error messages, feature order, probability range, additivity of explanations, fallback behaviour, report content and the application’s behaviour when the model is missing. {T:tests} summarises them. These tests establish that the code behaves as designed; they do not establish clinical validity."))
add(("tbl", "tests", "Automated test suite (45 tests; all passed in the final run, about 5.8 s).",
     ["Test file", "Tests", "What is verified"],
     [["`test_validation.py`", "16", "Required fields, invalid types, out-of-range values, fractional integers, zero glucose, unknown fields"],
      ["`test_prediction.py`", "11", "Missing/corrupt model, feature order, probability range, warnings, SHAP additivity, fallback"],
      ["`test_data_loader.py`", "6", "CSV loading, missing file, empty data, wrong schema, non-numeric/non-binary data, profiling"],
      ["`test_preprocessing.py`", "4", "Zero-to-NaN rule, missing handling, training-only imputer statistics, column-order invariance"],
      ["`test_reports.py`", "3", "CSV content, valid PDF, no diagnostic claims"],
      ["`test_train_utils.py`", "3", "Known metric values, threshold meets target, bootstrap interval brackets estimate"],
      ["`test_app.py`", "2", "Error message when model missing; end-to-end estimate in headless app"]],
     [2600, 900, 5900], {"sz": 19, "aligns": ["left", "center", "left"]}))
add(("p", "Static analysis with Ruff reported no findings for the whole repository in the final run."))
add(("h2", "4.12", "Installation and Execution Instructions"))
add(("code", """python -m venv .venv
.venv\\Scripts\\activate            (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
python -m src.train                downloads data, trains, evaluates, saves model
pytest -q                          runs the 45 tests
streamlit run app.py               launches the application"""))
add(("p", "A `Dockerfile` that installs the requirements and runs `python -m src.train` at build time is included for container deployment, and the deployment guide in `docs/deployment.md` covers Streamlit Community Cloud and Hugging Face Spaces. **The Docker image and cloud deployment were not built or run during this project**, so they are provided as unverified configuration."))

# =============================================================== CHAPTER 5
add(("ch", 5, "RESULTS AND INTERPRETATION"))
add(("p", "All numbers in this chapter are read from the files written by the actual training run (`artifacts/metrics.json`, seed 42) or computed from the saved model on the same seeded split. Training the whole pipeline twice with the same seed gave identical metrics."))
add(("h2", "5.1", "Dataset and Split Summary"))
add(("tbl", "split", "Dataset and split summary.",
     ["Set", "Records", "Positive", "Negative", "Positive rate"],
     [["Full dataset", "768", "268", "500", "34.9%"],
      ["Training split", "614", str(X["train_pos"]), str(X["train_neg"]), f"{META['training_prevalence']:.1%}"],
      ["Held-out test split", "154", str(X["test_pos"]), str(X["test_neg"]), f"{X['test_pos'] / 154:.1%}"]],
     [2800, 1500, 1500, 1500, 2100], {"aligns": ["left", "center", "center", "center", "center"]}))
add(("h2", "5.2", "Candidate-Model Comparison (Cross-Validation)"))
order = ["Logistic Regression", "SVM (RBF)", "Random Forest", "HistGradientBoosting", "Gradient Boosting", "Decision Tree", "Baseline (majority class)"]
rows = [[n.replace(" (majority class)", ""), f"{COMP[n]['cv_roc_auc']:.3f} ± {COMP[n]['cv_roc_auc_std']:.3f}", f3(COMP[n]["cv_pr_auc"]), f3(COMP[n]["cv_brier"]),
         f3(COMP[n]["cv_recall_at_0.5"]), f3(COMP[n]["cv_accuracy"])] for n in order]
add(("tbl", "cv", "Five-fold cross-validation results on the 614-record training split (mean ± SD across folds for ROC-AUC).",
     ["Model", "ROC-AUC", "PR-AUC", "Brier", "Recall @ 0.5", "Accuracy"], rows, [2700, 1700, 1200, 1100, 1500, 1200],
     {"sz": 19, "aligns": ["left", "center", "center", "center", "center", "center"]}))
add(("p", "The four best models, logistic regression (0.845), SVM (0.844), random forest (0.842) and histogram gradient boosting (0.835), lie within about one fold-to-fold standard deviation of one another (SD ≈ 0.013–0.019); the differences between them are therefore not meaningful given 614 training records. The decision tree (0.791) is clearly lower and the baseline, by construction, has ROC-AUC 0.5. Recall at the default 0.5 threshold is low for all models except balanced logistic regression (0.720), which motivates choosing the threshold explicitly rather than using 0.5."))
add(("fig", "cvplot", "cv_comparison.png", "Cross-validated ROC-AUC of the candidates (bars: mean over folds; whiskers: SD across folds).", 5.2, "Bar chart of cross-validated ROC-AUC for each model."))
add(("h2", "5.3", "Selected-Model Justification"))
add(("p", f"Logistic regression with *C* = 0.1 and balanced class weights had the highest mean cross-validated ROC-AUC and is also the most interpretable of the competitive models, so the selection rule of Section 3.7 chose it. Its standardised coefficients, averaged across the five calibration folds, are listed in {{T:coef}}. All are positive, i.e. higher values are associated with higher estimated probability. Glucose has the largest coefficient ({X['lr_coefficients']['Glucose']['mean']:.2f}), followed by BMI ({X['lr_coefficients']['BMI']['mean']:.2f}) and pregnancies ({X['lr_coefficients']['Pregnancies']['mean']:.2f}); blood pressure, skin-fold thickness and insulin have coefficients close to zero. Coefficients show associations learned from this dataset and are not evidence of causation."))
rows = [[f"`{f}`", f"{v['mean']:+.3f}", f"{v['sd']:.3f}"] for f, v in sorted(X["lr_coefficients"].items(), key=lambda kv: -abs(kv[1]["mean"]))]
add(("tbl", "coef", "Standardised logistic-regression coefficients (mean and SD across the five calibration folds; intercept ≈ −0.237).",
     ["Feature", "Mean coefficient", "SD across folds"], rows, [3800, 2800, 2800], {"aligns": ["left", "center", "center"]}))
add(("h2", "5.4", "Held-Out Test-Set Evaluation"))
rows = [["ROC-AUC", f3(T["roc_auc"]), ci("roc_auc"), f3(TR["roc_auc"])],
        ["PR-AUC", f3(T["pr_auc"]), ci("pr_auc"), f3(TR["pr_auc"])],
        ["Sensitivity (recall)", f3(T["recall_sensitivity"]), ci("recall_sensitivity"), f3(TR["recall_sensitivity"])],
        ["Specificity", f3(T["specificity"]), ci("specificity"), f3(TR["specificity"])],
        ["Precision", f3(T["precision"]), ci("precision"), f3(TR["precision"])],
        ["F1-score", f3(T["f1"]), ci("f1"), f3(TR["f1"])],
        ["Accuracy", f3(T["accuracy"]), ci("accuracy"), f3(TR["accuracy"])],
        ["Brier score", f3(T["brier"]), ci("brier"), f3(TR["brier"])]]
add(("tbl", "test", f"Performance of the final model at threshold {META['threshold']:.4f}. Test column: held-out test set (n = 154); last column: out-of-fold predictions on the training split (n = 614) for comparison.",
     ["Metric", "Test value", "95% bootstrap CI (test)", "Out-of-fold train"], rows, [2600, 1500, 2900, 2400],
     {"aligns": ["left", "center", "center", "center"]}))
add(("p", f"The ROC-AUC of {T['roc_auc']:.3f} indicates that a randomly chosen positive record receives a higher score than a randomly chosen negative record about 81% of the time. The 95% interval ({ci('roc_auc')}) is wide because only 154 records, of which 54 are positive, were available. The out-of-fold training ROC-AUC ({TR['roc_auc']:.3f}) is higher than the test value, but the test estimate lies inside its own interval and the difference is of the size expected from sampling variability; with one split it cannot be attributed to overfitting or to chance. The Brier score is {T['brier']:.3f} on the test set and {TR['brier']:.3f} out-of-fold; for reference, always predicting the training prevalence scores about 0.227."))
add(("h2", "5.5", "Confusion Matrix"))
add(("p", f"At the screening threshold the model produced {CM['tp']} true positives, {CM['fp']} false positives, {CM['fn']} false negatives and {CM['tn']} true negatives ({{F:cm}}). Sensitivity is {CM['tp']}/{CM['tp'] + CM['fn']} = {T['recall_sensitivity']:.3f}: the model flagged 44 of the 54 positive records. Specificity is {CM['tn']}/{CM['tn'] + CM['fp']} = {T['specificity']:.3f}: 33 of the 100 negative records were flagged. Precision is {T['precision']:.3f}, meaning that about four in ten flagged records were labelled negative. This trade-off follows directly from choosing a threshold that favours sensitivity."))
add(("fig", "cm", "confusion_matrix.png", "Confusion matrix on the held-out test set (n = 154) at threshold 0.294.", 3.6, "Confusion matrix heat map."))
add(("h2", "5.6", "ROC and Precision–Recall Curves"))
add(("p", f"{{F:roc}} shows the ROC curve (AUC {T['roc_auc']:.3f}); the curve lies well above the chance diagonal across most of its range. {{F:pr}} shows the precision–recall curve; its area (average precision {T['pr_auc']:.3f}) should be compared with the no-skill level equal to the positive rate, about 0.35, so the model carries real signal, but precision falls as recall rises, in line with the precision of {T['precision']:.3f} at the chosen operating point. The curves are step-like because the test set is small."))
add(("fig", "roc", "roc_curve.png", "ROC curve on the held-out test set.", 3.7, "ROC curve."))
add(("fig", "pr", "pr_curve.png", "Precision–recall curve on the held-out test set.", 3.7, "Precision-recall curve."))
add(("h2", "5.7", "Calibration Assessment"))
bins = M["test"]["curves"]["calibration"]
rows = [[str(i + 1), str(X["calibration_bin_sizes"][i]), f"{bins['mean_predicted'][i]:.3f}", f"{bins['fraction_positive'][i]:.3f}"] for i in range(len(bins["mean_predicted"]))]
add(("tbl", "calib", "Calibration on the test set: eight quantile bins of predicted probability.",
     ["Bin", "Records", "Mean predicted", "Observed positive fraction"], rows, [1200, 1800, 2800, 3600], {"aligns": ["center"] * 4}))
add(("p", f"Sigmoid calibration lowered the out-of-fold Brier score on the training split from {M['brier_raw_vs_calibrated_train_oof'][0]:.4f} to {M['brier_raw_vs_calibrated_train_oof'][1]:.4f}, which is why it was retained. On the test set ({{F:cal}} and {{T:calib}}) the points follow the diagonal approximately: observed fractions are close to predicted ones in the middle bins, and the highest-probability bin is slightly over-confident (predicted 0.845, observed 0.750). Each bin holds only 19–20 records, so a bin’s observed fraction can move by about ±0.1 from one record; the plot indicates reasonable but unproven calibration. In addition, the probabilities are calibrated to a dataset whose prevalence is 35%, and would not transfer to a population with a different prevalence."))
add(("fig", "cal", "calibration.png", "Calibration curve on the held-out test set (eight quantile bins).", 3.7, "Calibration curve."))
add(("h2", "5.8", "Failure-Case Analysis"))
fn, fp, tp, tn = X["false_negatives"], X["false_positives"], X["true_positives"], X["true_negatives"]
rows = [[nm, str(d["n"]), f"{d['median']['Glucose']:g}", f"{d['median']['BMI']:g}", f"{d['median']['Age']:g}", f"{d['mean_prob']:.2f}"]
        for nm, d in [("True positives", tp), ("False negatives", fn), ("False positives", fp), ("True negatives", tn)]]
add(("tbl", "fail", "Median raw measurements and mean predicted probability by outcome type on the test set.",
     ["Group", "n", "Median glucose", "Median BMI", "Median age", "Mean predicted p"], rows, [2400, 800, 1700, 1500, 1500, 1500],
     {"sz": 19, "aligns": ["left"] + ["center"] * 5}))
add(("p", f"The ten false negatives have a median glucose of {fn['median']['Glucose']:g}, close to that of true negatives ({tn['median']['Glucose']:g}) and far below true positives ({tp['median']['Glucose']:g}), and they are younger (median {fn['median']['Age']:g} years). The model, which relies mostly on glucose, therefore had little information with which to separate them from negatives. Conversely, the 33 false positives have a median glucose of {fp['median']['Glucose']:g} and median BMI of {fp['median']['BMI']:g}, which are higher than for true negatives; they look like positives on the measured variables. With only 10 and 33 cases, these descriptions are indicative and not statistical conclusions."))
add(("h2", "5.9", "Explainability Results"))
imp_sorted = sorted(IMP.items(), key=lambda kv: -kv[1]["mean"])
rows = [[f"`{k}`", f"{v['mean']:+.4f}", f"{v['std']:.4f}"] for k, v in imp_sorted]
add(("tbl", "imp", "Permutation importance on the test set (decrease in ROC-AUC when the feature is shuffled; 30 repeats).",
     ["Feature", "Mean decrease", "SD"], rows, [3800, 2800, 2800], {"aligns": ["left", "center", "center"]}))
add(("p", f"Glucose dominates (mean decrease {IMP['Glucose']['mean']:.3f}), roughly six times the next features (BMI {IMP['BMI']['mean']:.3f}, pregnancies {IMP['Pregnancies']['mean']:.3f}). Blood pressure, skin-fold thickness and insulin are close to zero or slightly negative, i.e. shuffling them does not hurt and may help the test ROC-AUC by chance; these features add little for this model. Permutation importance can understate the importance of correlated features because the information is shared, and BMI’s large coefficient but modest importance is consistent with that possibility. An exploratory ablation on the training split only (same five folds; test set not used) gave cross-validated ROC-AUC of glucose alone 0.799 ± 0.034, all features except glucose 0.768 ± 0.015, all eight features 0.845 ± 0.013. Glucose is therefore the strongest single predictor, but the other features together still carry signal. Because the documented outcome rule is itself a glucose criterion and its timing relative to the features is unknown, these associations should not be presented as independent risk factors."))
add(("fig", "imp", "feature_importance.png", "Permutation importance of the features on the held-out test set.", 4.4, "Feature importance bar chart."))
ex = EX["contributions"]
rows = [[c["label"] + (" (not provided)" if c["imputed"] else ""), f"{c['contribution'] * 100:+.1f}"] for c in ex]
add(("p", f"{{T:local}} shows the local SHAP explanation for the illustrative input used in {{F:pred}} (pregnancies 1, glucose 150, BMI 33.5, age 45, other fields blank). The model’s baseline (average output over the background sample) is {EX['base'] * 100:.1f}% and its estimate for this input is {EX['probability'] * 100:.1f}%; the contributions sum exactly to that difference ({EX['sum_check'] * 100:.1f}% = {EX['base'] * 100:.1f}% + sum). Glucose raises the estimate by about 21 percentage points, whereas one pregnancy lowers it by about 6 points because it is below the dataset average and the coefficient is positive. Features that were not provided contribute almost nothing. The input is illustrative, not a patient, and the contributions describe model behaviour, not causes."))
add(("tbl", "local", "Local SHAP contributions for the illustrative input (percentage points of probability).",
     ["Input", "Contribution (pp)"], rows, [6200, 3200], {"aligns": ["left", "center"]}))
add(("h2", "5.10", "Application Screenshots and Software-Test Results"))
add(("p", "The application screenshots are in Chapter 4 ({F:home}–{F:insights}). The Risk Estimation page validates input before calling the model: for example, a non-numeric entry in the optional pedigree field produced the message “Diabetes pedigree function: must be a number” ({F:valerr}). In the final run, all 45 automated tests passed (pytest, about 5.8 s) and Ruff reported no findings for the repository. As emphasised in Section 4.11, these results verify software behaviour only."))
add(("h2", "5.11", "Discussion: Strengths and Weaknesses"))
add(("p", "**Strengths.** (i) The protocol avoids leakage: preprocessing is inside the pipeline, all choices use training data and the test set is scored once. (ii) Seven candidates were compared fairly and a simple model was preferred when differences were within noise, in line with [@rudin]. (iii) Calibration and uncertainty are reported, not only accuracy [@steyerberg]. (iv) Explanations correspond to the model’s actual output and satisfy an additivity check. (v) The system is reproducible, tested and privacy-conscious."))
add(("p", "**Weaknesses.** (i) A small, single-population dataset limits what can be concluded; test intervals are wide. (ii) Specificity of 0.67 and precision of 0.57 mean frequent false alarms at the chosen threshold. (iii) Glucose is the strongest single predictor, and the dataset documentation does not settle how the recorded glucose relates in time to the outcome classification. (iv) No external validation or subgroup analysis was possible. (v) The application warns about out-of-range values using ranges that include the dataset’s zero entries, so low-end outliers are less likely to trigger a warning than high-end ones; this is a minor implementation weakness."))
add(("p", "**Comparison with the literature.** The original ADAP study reported sensitivity and specificity of about 76% on 192 instances [@uci]; this project obtained sensitivity 0.815 and specificity 0.670 on 154 instances. Because the split, method, threshold and sample sizes differ, and the intervals are wide, the results should be regarded as roughly comparable in magnitude and not as an improvement. Accuracy-based comparisons with other studies [@sisodia][@khanam] are avoided for the same reason."))
add(("h2", "5.12", "Limitations of the Dataset and Interpretation"))
add(("p", "The dataset describes adult women of Pima heritage from the 1990s; results cannot be assumed for men, other ethnic groups, children or current populations, and demographic bias cannot be assessed within a single group. The documented label rule uses a glucose-tolerance criterion at any survey examination or in routine care, and the timing between the recorded measurements and that classification is not documented, so the target is recorded diabetes status and not necessarily future onset. Five measurements encode missing values as zeros and about half of insulin values are missing, so imputation influences results. A single held-out test split cannot establish clinical validity; prospective and external validation would be required [@tripod]. Feature contributions are associations and must not be read as causes."))
add(("h2", "5.13", "Verification of the Documented Results"))
add(("p", "The documented implementation (README and model card) states that logistic regression was selected, that test ROC-AUC was about 0.81 and that the threshold was about 0.29. These values were re-checked against the saved artefacts and match: selected model Logistic Regression, test ROC-AUC 0.809, threshold 0.2941, confusion matrix 44/33/10/67 (recomputed from the saved model on the seeded split). One discrepancy was found during the final audit: an earlier statement that the repository was Ruff-clean was true for the source code but not for the exploratory notebook and a helper script; these were corrected and the whole repository now passes."))

# =============================================================== CHAPTER 6
add(("ch", 6, "CONCLUSION AND FUTURE SCOPE"))
add(("h2", "6.1", "Summary of the Work"))
add(("p", "The project addressed the problem of building a transparent and honestly evaluated diabetes risk-estimation tool from a small public dataset. It implemented a reproducible pipeline for the Pima Indians Diabetes Database that treats impossible zeros as missing values, compares seven candidates with one cross-validation protocol, selects logistic regression, calibrates its probabilities, chooses a screening threshold from training data and evaluates once on a held-out test set. A Streamlit application accompanies the model with input validation, explanations, model-insight pages and PDF/CSV report export, supported by 45 automated tests."))
add(("h2", "6.2", "Verified Findings and Objectives Met"))
add(("bul", [
    f"Logistic regression achieved the best cross-validated ROC-AUC ({COMP['Logistic Regression']['cv_roc_auc']:.3f}) and was selected; the top four models were statistically indistinguishable.",
    f"On the held-out test set (n = 154): ROC-AUC {T['roc_auc']:.3f} ({ci('roc_auc')}), sensitivity {T['recall_sensitivity']:.3f}, specificity {T['specificity']:.3f}, precision {T['precision']:.3f}, Brier score {T['brier']:.3f}.",
    "Plasma glucose is the strongest single predictor; insulin, blood pressure and skin-fold thickness contribute almost nothing by permutation importance, while an exploratory training-only ablation shows the remaining features still carry signal (ROC-AUC 0.768 without glucose, 0.845 with all eight).",
    "Objectives O1–O7 ({T:obj}) were met by implemented and tested features; external validation and fairness analysis remain future work.",
]))
add(("p", "**Technical contributions.** A leakage-safe, reproducible evaluation workflow; calibrated probabilities with an explicit screening threshold and bootstrap intervals; explanations that are additive to the actual prediction, with a tested fallback; and a validated, privacy-conscious application with downloadable reports."))
add(("p", "**Principal limitations.** One small, single-population dataset; wide uncertainty intervals; frequent false alarms at the chosen threshold; an outcome whose timing relative to the features is undocumented; no external or clinical validation; Docker and cloud deployment unverified."))
add(("h2", "6.3", "Future Scope"))
add(("p", "The following are *proposed* enhancements; none has been implemented."))
add(("bul", [
    "Evaluate on larger and more diverse datasets, with external validation on data from different sources and populations.",
    "Perform fairness and subgroup analyses where sufficient data are available, and report them in line with TRIPOD+AI [@tripod].",
    "Improve and monitor calibration (for example comparing sigmoid and isotonic calibration on larger data) and add robustness tests.",
    "Add secure and optional data handling, and verify container and cloud deployments.",
    "Explore interoperable healthcare formats only after appropriate clinical and regulatory review.",
    "Improve usability and accessibility, including multilingual support and screen-reader testing.",
]))
add(("h2", "6.4", "Concluding Statement"))
add(("p", "The Diabetes Risk Prediction System is an **educational risk-estimation prototype, not a medical diagnostic system**. Its value lies in demonstrating a careful, transparent machine-learning workflow and in showing honestly how much (and how little) can be concluded from a small public dataset. Any use beyond education would require external validation, clinical evidence and regulatory review."))
