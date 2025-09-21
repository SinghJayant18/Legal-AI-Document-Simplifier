# utils/rag_handler.py
from typing import List, Dict, Tuple
import os, datetime, textwrap
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm


# utils/rag_handler.py (no big changes needed)
# Just make sure when calling query_collection, you do:

from utils.embedder import load_chroma_collection, query_collection

def handle_query(query: str):
    collection = load_chroma_collection()
    results = query_collection(collection, query, k=6)

    best_sim = max((d.get("similarity") or 0) for d in results) if results else 0
    if best_sim < 0.78:
        results = []

    answer = generate_response(query, results)
    return answer, results

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_response(query: str, retrieved_docs: List[Dict] | None) -> str:
    context = "No internal references retrieved."
    if retrieved_docs:
        context = "\n".join([f"- {d.get('content','')[:600]} [source: {d.get('source')}]" for d in retrieved_docs])

    prompt = f"""
You are an Indian legal assistant.
Task: Answer with 6 sections:
1. Overview / Meaning
2. IPC Codes / Acts / Amendments / Sections
3. Prominent Cases (with one-line relevance)
4. Precautions
5. Pros & Cons of Filing Case
6. Suggested Solution (based on past verdicts)

User Input:
{query}

Context (may be empty):
{context}

Always end with: "Disclaimer: This is not legal advice."
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        out = model.generate_content(prompt)
        return out.text or "No response generated."
    except Exception as e:
        return f"LLM error: {str(e)}"

# --- PDF report (simpler than pdf_maker) ---
def _wrap(c: canvas.Canvas, txt: str, x: float, y: float, max_w: float, leading=14):
    for para in txt.split("\n"):
        for line in textwrap.wrap(para, width=int(max_w/6)):
            c.drawString(x, y, line)
            y -= leading
        if para.strip():
            y -= leading*0.3
    return y

def generate_case_pdf(query: str, answer_text: str, retrieved_docs: List[Dict] | None, reports_dir="files") -> Tuple[str,str]:
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"case_report_{ts}.pdf"
    path = os.path.join(reports_dir, filename)

    c = canvas.Canvas(path, pagesize=A4)
    W,H = A4
    x,y = 2*cm, H-2*cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x,y,"Case Reference Report")
    y -= 20
    c.setFont("Helvetica",10)
    c.drawString(x,y,f"Query: {query[:100]}")
    y -= 14

    if retrieved_docs:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x,y,"Prominent Matches")
        y -= 16
        c.setFont("Helvetica",10)
        for i,d in enumerate(retrieved_docs[:3],1):
            y = _wrap(c,f"{i}. {d.get('source')} | {d.get('similarity'):.2f}",x,y,W-4*cm)
            snippet = (d.get("content") or "")[:400]
            if snippet: y = _wrap(c,"Snippet: "+snippet,x+10,y,W-4*cm,12)
            y -= 4
            if y<3*cm: c.showPage(); x,y=2*cm,H-2*cm
    else:
        c.drawString(x,y,"No matches found.")
        y -= 14

    c.setFont("Helvetica-Bold",12)
    c.drawString(x,y,"AI Analysis")
    y -= 16
    c.setFont("Helvetica",10)
    y = _wrap(c,answer_text,x,y,W-4*cm,12)

    c.setFont("Helvetica-Oblique",9)
    c.drawString(x,2*cm,"Disclaimer: This report is for educational purposes only.")
    c.save()
    return filename,f"/files/{filename}"
