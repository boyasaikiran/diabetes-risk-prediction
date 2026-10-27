"""CSV and PDF report generation (in memory; nothing is written to disk)."""
from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.predict import Prediction
from src.validation import FIELD_SPECS

DISCLAIMER = (
    "This is a model-generated estimate from an educational project. It is NOT a medical "
    "diagnosis and cannot confirm or rule out diabetes. Please consult a qualified "
    "healthcare professional for assessment."
)
LIMITATIONS = (
    "The model was trained on 768 records from a single study of adult females of Pima "
    "Indian heritage (Arizona, USA, 1990s) and may not generalise to other people. The "
    "outcome label follows a glucose-tolerance criterion whose timing relative to the measurements is undocumented. Probabilities are calibrated "
    "to that dataset's prevalence and have not been clinically validated."
)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _interpretation(p: Prediction) -> str:
    side = "at or above" if p.above_threshold else "below"
    return (f"The model's estimated probability is {p.probability:.0%}, {side} its screening "
            f"threshold of {p.threshold:.0%}. The threshold is a model operating point chosen "
            f"to favour sensitivity, not an established medical cut-off.")


def build_csv(p: Prediction) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["section", "item", "value"])
    w.writerow(["meta", "generated", _now()])
    w.writerow(["meta", "model", f"{p.model_name} v{p.model_version}"])
    for k, v in p.inputs.items():
        w.writerow(["input", f"{FIELD_SPECS[k].label} ({FIELD_SPECS[k].unit})",
                    "not provided" if v != v else f"{v:g}"])
    w.writerow(["output", "estimated_probability", f"{p.probability:.4f}"])
    w.writerow(["output", "screening_threshold", f"{p.threshold:.4f}"])
    w.writerow(["output", "interpretation", _interpretation(p)])
    if p.explanation:
        for c in p.explanation["contributions"]:
            w.writerow(["explanation", c["label"], f"{c['contribution']:+.4f}"])
    w.writerow(["note", "disclaimer", DISCLAIMER])
    w.writerow(["note", "limitations", LIMITATIONS])
    return buf.getvalue().encode("utf-8")


def build_pdf(p: Prediction) -> bytes:
    st = getSampleStyleSheet()
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            title="Diabetes risk estimate (model-generated)")

    def table(rows, widths):
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6f2f6")),
            ("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    s: list = [Paragraph("Diabetes Risk Estimate — Model-Generated Report", st["Title"]),
               Paragraph(f"Generated {_now()} · {p.model_name} v{p.model_version}", st["Normal"]),
               Spacer(1, 6), Paragraph(f"<b>{DISCLAIMER}</b>", st["Normal"]), Spacer(1, 8),
               Paragraph("Submitted inputs", st["Heading2"])]
    rows = [["Field", "Value", "Unit"]] + [
        [FIELD_SPECS[k].label, "not provided" if v != v else f"{v:g}", FIELD_SPECS[k].unit]
        for k, v in p.inputs.items()]
    s += [table(rows, [80 * mm, 40 * mm, 40 * mm]), Spacer(1, 8),
          Paragraph("Model output", st["Heading2"]), Paragraph(_interpretation(p), st["Normal"])]
    if p.explanation:
        s += [Spacer(1, 8), Paragraph("Which inputs influenced this estimate", st["Heading2"])]
        rows = [["Input", "Effect on estimate (percentage points)"]] + [
            [c["label"], f"{c['contribution'] * 100:+.1f}"] for c in p.explanation["contributions"]]
        s += [table(rows, [90 * mm, 70 * mm]), Spacer(1, 4),
              Paragraph(p.explanation["plain_language"], st["Normal"])]
    s += [Spacer(1, 8), Paragraph("Limitations", st["Heading2"]),
          Paragraph(LIMITATIONS, st["Normal"])]
    doc.build(s)
    return out.getvalue()
