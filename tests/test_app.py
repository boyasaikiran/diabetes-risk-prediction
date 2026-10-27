"""App-level error handling using Streamlit's headless AppTest."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_shows_error_when_model_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("DRP_MODEL_DIR", str(tmp_path))
    from src.config import load_config

    load_config.cache_clear()
    try:
        at = AppTest.from_file(APP, default_timeout=60).run()
    finally:
        load_config.cache_clear()
    assert not at.exception
    assert any("not found" in e.value for e in at.error)


def test_end_to_end_estimate_with_trained_model():
    """Runs only when `python -m src.train` has produced a model (not clinical validation)."""
    import pytest

    from src.config import load_config, resolve

    if not (resolve(load_config()["paths"]["model_dir"]) / "model.joblib").exists():
        pytest.skip("trained model not available")
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Risk Estimation").run()
    at.button[0].click().run()
    assert not at.exception and not at.error
    assert len(at.session_state["history"]) == 1
