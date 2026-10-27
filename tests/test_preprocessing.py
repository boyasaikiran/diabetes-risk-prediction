import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.data_loader import FEATURES, TARGET
from src.preprocessing import ZeroToNaN, build_model_pipeline


def test_zero_to_nan_only_for_configured_columns():
    df = pd.DataFrame([dict.fromkeys(FEATURES, 0.0)])
    out = ZeroToNaN().fit(df).transform(df)
    assert out["Glucose"].isna().all() and out["Insulin"].isna().all()
    assert out["Pregnancies"].iloc[0] == 0 and out["Age"].iloc[0] == 0  # valid zeros kept


def test_pipeline_handles_missing_and_is_deterministic(synth):
    pipe = build_model_pipeline(LogisticRegression(max_iter=500)).fit(synth[FEATURES], synth[TARGET])
    x = synth[FEATURES].head(3).copy()
    x.loc[0, "BMI"] = np.nan
    p1, p2 = pipe.predict_proba(x), pipe.predict_proba(x)
    assert np.isfinite(p1).all() and np.array_equal(p1, p2)


def test_imputer_statistics_come_from_training_data_only(synth):
    train = synth.iloc[:150]
    pipe = build_model_pipeline(LogisticRegression()).fit(train[FEATURES], train[TARGET])
    imp = pipe.named_steps["prep"].named_steps["columns"].named_transformers_["num"]["impute"]
    ins = train["Insulin"].replace(0, np.nan).median()  # zeros are missing, so excluded
    assert np.isclose(imp.statistics_[FEATURES.index("Insulin")], ins)
    assert np.isclose(imp.statistics_[FEATURES.index("Age")], train["Age"].median())


def test_column_order_does_not_change_predictions(synth):
    pipe = build_model_pipeline(LogisticRegression(max_iter=500)).fit(synth[FEATURES], synth[TARGET])
    shuffled = synth[FEATURES[::-1]].head(5)
    assert np.allclose(pipe.predict_proba(shuffled), pipe.predict_proba(synth[FEATURES].head(5)))
