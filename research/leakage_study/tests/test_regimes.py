"""Test group 1 (label isolation) and 2 (scope isolation): prove which regimes read labels / fit on all rows."""
import numpy as np
import pytest
from leakage_study.regimes import REGIMES, apply_regime

ALL = list(REGIMES)


def run(name, X, y, s):
    return apply_regime(name, X, y, s.train_idx, s.test_idx)


def same(a, b):
    return np.array_equal(a, b)


@pytest.mark.parametrize("name", ALL)
def test_outputs_have_no_missing_values(toy, toy_split, name):
    X, y = toy
    r = run(name, X, y, toy_split)
    assert not np.isnan(r.X_train).any() and not np.isnan(r.X_test_app).any() and not np.isnan(r.X_test_dep).any()
    assert r.X_train.shape[0] == len(toy_split.train_idx) and r.X_test_app.shape[0] == len(toy_split.test_idx)


@pytest.mark.parametrize("name", ["Reg-0", "Reg-1"])
def test_label_free_regimes_ignore_every_label(toy, toy_split, name):
    X, y = toy
    rng = np.random.default_rng(1)
    a, b = run(name, X, y, toy_split), run(name, X, rng.permutation(y), toy_split)
    assert same(a.X_train, b.X_train) and same(a.X_test_app, b.X_test_app) and same(a.X_test_dep, b.X_test_dep)


@pytest.mark.parametrize("name", ["Reg-0", "Reg-1", "Reg-2", "Reg-3"])
def test_deployment_matrix_never_depends_on_labels(toy, toy_split, name):
    X, y = toy
    a, b = run(name, X, y, toy_split), run(name, X, 1 - y, toy_split)
    assert same(a.X_test_dep, b.X_test_dep)


def flipped_test_labels(y, s):
    y2 = y.copy()
    y2[s.test_idx] = 1 - y[s.test_idx]
    return y2


@pytest.mark.parametrize("name", ["Reg-0", "Reg-1", "Reg-4"])
def test_heldout_labels_do_not_affect_regimes_that_do_not_use_them(toy, toy_split, name):
    X, y = toy
    a, b = run(name, X, y, toy_split), run(name, X, flipped_test_labels(y, toy_split), toy_split)
    assert same(a.X_train, b.X_train) and same(a.X_test_app, b.X_test_app)


def test_reg2_uses_heldout_true_labels_but_only_training_statistics(toy, toy_split):
    X, y = toy
    a, b = run("Reg-2", X, y, toy_split), run("Reg-2", X, flipped_test_labels(y, toy_split), toy_split)
    assert same(a.X_train, b.X_train)               # training imputation unaffected by held-out labels
    assert not same(a.X_test_app, b.X_test_app)    # held-out imputation uses the held-out row's true label


def test_reg3_uses_all_labels_and_all_rows(toy, toy_split):
    X, y = toy
    a, b = run("Reg-3", X, y, toy_split), run("Reg-3", X, flipped_test_labels(y, toy_split), toy_split)
    assert not same(a.X_test_app, b.X_test_app)
    assert not same(a.X_train, b.X_train)          # global class medians include held-out labels


def modified_heldout_features(X, s):
    X2 = X.copy()
    X2[s.test_idx] = np.where(np.isnan(X[s.test_idx]), np.nan, X[s.test_idx] * 1.7 + 5)
    return X2


@pytest.mark.parametrize("name", ["Reg-0", "Reg-2", "Reg-4"])
def test_training_only_regimes_ignore_heldout_features_when_imputing_training_rows(toy, toy_split, name):
    X, y = toy
    a, b = run(name, X, y, toy_split), run(name, modified_heldout_features(X, toy_split), y, toy_split)
    assert same(a.X_train, b.X_train)


@pytest.mark.parametrize("name", ["Reg-1", "Reg-3"])
def test_global_regimes_leak_heldout_features_into_training_rows(toy, toy_split, name):
    X, y = toy
    a, b = run(name, X, y, toy_split), run(name, modified_heldout_features(X, toy_split), y, toy_split)
    assert not same(a.X_train, b.X_train)


@pytest.mark.parametrize("name,equal", [("Reg-0", True), ("Reg-4", True), ("Reg-1", False), ("Reg-2", False), ("Reg-3", False)])
def test_apparent_equals_deployment_only_for_label_free_training_only_regimes(toy, toy_split, name, equal):
    X, y = toy
    r = run(name, X, y, toy_split)
    assert same(r.X_test_app, r.X_test_dep) == equal


def test_reg4_heldout_values_depend_on_observed_features_not_labels(toy, toy_split):
    X, y = toy
    r = run("Reg-4", X, y, toy_split)
    assert same(r.X_test_app, r.X_test_dep)


def test_unknown_regime_rejected(toy, toy_split):
    with pytest.raises(ValueError):
        run("Reg-9", *toy, toy_split)
