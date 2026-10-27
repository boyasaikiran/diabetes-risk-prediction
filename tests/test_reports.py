from src.report_generator import DISCLAIMER, build_csv, build_pdf
from tests.conftest import VALID


def test_csv_contains_required_sections(predictor):
    txt = build_csv(predictor.predict(VALID)).decode()
    for needle in ["generated", "Plasma glucose", "estimated_probability", "disclaimer",
                   "limitations", "not provided", DISCLAIMER[:30]]:
        assert needle in txt


def test_pdf_is_valid_pdf(predictor):
    pdf = build_pdf(predictor.predict(VALID))
    assert pdf.startswith(b"%PDF") and len(pdf) > 1500


def test_reports_do_not_claim_diagnosis(predictor):
    txt = build_csv(predictor.predict(VALID)).decode().lower()
    assert "you have diabetes" not in txt and "not a medical diagnosis" in txt
