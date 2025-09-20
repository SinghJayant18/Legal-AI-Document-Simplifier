# utils/pdf_maker.py
import os
from datetime import datetime
from typing import List, Dict
from fpdf import FPDF

def _add_wrapped(pdf: FPDF, text: str, w: float = 0):
    pdf.multi_cell(w, 6, txt=text)
    pdf.ln(1)

def create_case_report(query: str, retrieved_docs: List[Dict], analysis_text: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    filename = f"case_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = os.path.join(out_dir, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_title("Case Reference Report")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Case Reference Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "User Query / Document:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    _add_wrapped(pdf, query)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Prominent Matches:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    if retrieved_docs:
        for i, d in enumerate(retrieved_docs[:5], 1):
            _add_wrapped(pdf, f"{i}. {d.get('source')} (similarity: {d.get('similarity'):.2f})")
            _add_wrapped(pdf, f"   Snippet: {d.get('content')[:500]}")
    else:
        _add_wrapped(pdf, "No strong matches found.")

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "AI Analysis:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    _add_wrapped(pdf, analysis_text)

    pdf.output(out_path)
    return filename
