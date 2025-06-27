# utils.py must define summarize_resume and make_candidate_id properly for this to work.

import io, re, json, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(
    page_title="HireScope - Upload Résumés", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Track stats and results in session
if "results" not in st.session_state:
    st.session_state.results = []
if "stats" not in st.session_state:
    st.session_state.stats = {"processed": 0, "errors": 0, "total_uploaded": 0}

# Header UI
st.title("💼 HireScope AI")
st.caption("Smart AI-Powered Résumé Management")

# Sidebar metrics
with st.sidebar:
    st.subheader("📊 Session Stats")
    st.metric("Processed", st.session_state.stats["processed"])
    st.metric("Errors", st.session_state.stats["errors"])
    st.metric("Uploaded", st.session_state.stats["total_uploaded"])
    if st.button("Reset Stats"):
        st.session_state.stats = {"processed": 0, "errors": 0, "total_uploaded": 0}
        st.session_state.results.clear()
        st.rerun()

# Input form
st.subheader("👤 HR Upload Form")
col1, col2 = st.columns([3, 1])
with col1:
    hr_name = st.text_input("Your name (HR rep)", placeholder="e.g., Jane Doe")
with col2:
    files = st.file_uploader("Upload up to 15 Résumé PDFs", type="pdf", accept_multiple_files=True)

# Guards
if not hr_name:
    st.warning("Please enter your name.")
    st.stop()
if files and len(files) > 15:
    st.error("You can upload a maximum of 15 files.")
    st.stop()

# Extractor

def extract_all_text(pdf_bytes):
    extractors = [
        lambda: "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf")),
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        lambda: "\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
        lambda: "".join(p.extract_text() or "" for p in PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages),
        lambda: "\n".join(pytesseract.image_to_string(img, config='--psm 6') for img in convert_from_bytes(pdf_bytes, dpi=300))
    ]
    for ext in extractors:
        try:
            out = ext()
            if out and len(out.strip()) > 100:
                return out
        except: continue
    return ""

# Extract name (enhanced)
def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    try:
        data = json.loads(summary)
        if isinstance(data, dict) and data.get("name"):
            return data["name"].strip()
    except: pass

    patterns = [r"(?i)^name[:\-]?\s*(.+)$", r"(?i)^full name[:\-]?\s*(.+)$"]
    for p in patterns:
        match = re.search(p, summary, re.M)
        if match: return match.group(1).strip()

    for line in summary.split("\n")[:5]:
        line = line.strip("- ")
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", line):
            return line

    return fallback_filename.rsplit(".", 1)[0].replace("_", " ")

# Processing files
if files:
    st.subheader("🔄 Processing Files")
    bar = st.progress(0)
    for i, pdf in enumerate(files):
        status = st.empty()
        status.info(f"Processing {pdf.name}...")
        st.session_state.stats["total_uploaded"] += 1
        try:
            raw = extract_all_text(pdf.getvalue())
            if not raw.strip(): raise Exception("No text extracted")
            with st.spinner("Summarizing with GPT-4o..."):
                summary = summarize_resume(raw)
            name = extract_candidate_name(summary, pdf.name)
            cid = make_candidate_id(name)

            # Dup check
            if collection.get(where={"name": name})["ids"]:
                if not st.checkbox(f"Overwrite {name}?", key=f"ow_{cid}_{i}"):
                    status.warning(f"Skipped {name}")
                    continue
                collection.delete(where={"name": name})

            # Save
            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
                ids=[cid]
            )
            if hasattr(chroma_client, "persist"): chroma_client.persist()

            st.session_state.stats["processed"] += 1
            st.session_state.results.append({
                "name": name,
                "cid": cid,
                "summary": summary[:1200],
                "raw": raw[:1200],
                "filename": pdf.name
            })
            status.success(f"Stored résumé for {name} (ID: {cid})")
        except Exception as e:
            st.session_state.stats["errors"] += 1
            status.error(f"Error in {pdf.name}: {e}")
        bar.progress((i + 1) / len(files))

# Show summaries
if st.session_state.results:
    st.subheader("📃 Results")
    for res in st.session_state.results:
        with st.expander(f"👤 {res['name']} — {res['filename']}"):
            tab1, tab2 = st.tabs(["Summary", "Raw Text"])
            with tab1:
                st.text_area("Summary", res['summary'], height=200)
            with tab2:
                st.text_area("Raw", res['raw'], height=200)