import io, re, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(page_title="Résumé Upload", page_icon="📂", layout="wide")

# Theme colors
theme = st.get_theme()
bg_color = theme["backgroundColor"]
txt_color = theme["textColor"]
acc_color = theme["primaryColor"]

# Header
st.markdown(f"""
<div style="background: linear-gradient(90deg, {acc_color}AA, {txt_color}10); padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
    <h1 style="color:{txt_color};">📂 HR Résumé Uploader</h1>
    <p style="color:{txt_color}CC;">Upload multiple PDFs and process them efficiently</p>
</div>
""", unsafe_allow_html=True)

# State Init
if 'stats' not in st.session_state:
    st.session_state.stats = {'processed': 0, 'errors': 0, 'total': 0}
if 'results' not in st.session_state:
    st.session_state.results = []

# Input section
col1, col2 = st.columns([3, 1])
with col1:
    hr_name = st.text_input("HR Name", placeholder="Enter your name")
    files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

with col2:
    stats = st.session_state.stats
    st.metric("Processed", stats["processed"])
    st.metric("Errors", stats["errors"])

if not hr_name:
    st.warning("Please enter your name first")
    st.stop()

if files and len(files) > 10:
    st.error("⚠️ Upload up to 10 files only.")
    st.stop()

# Extraction pipeline
def extract_all_text(pdf_bytes: bytes) -> str:
    text = ""
    methods = [
        lambda: "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf")),
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        lambda: "\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
        lambda: "".join(p.extract_text() or "" for p in PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages),
        lambda: "\n".join(pytesseract.image_to_string(img) for img in convert_from_bytes(pdf_bytes, dpi=300))
    ]
    for method in methods:
        try:
            text = method()
            if text.strip():
                break
        except: continue
    return text

def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    patterns = [
        r"(?i)^name[:\-]?\s*(.+)$",
        r"(?i)^candidate name[:\-]?\s*(.+)$",
        r"(?i)^full name[:\-]?\s*(.+)$"
    ]
    for pat in patterns:
        m = re.search(pat, summary, re.M)
        if m: return m.group(1).strip()
    for line in summary.splitlines():
        line = line.strip("-• \t")
        if line and re.fullmatch(r"[A-Z][A-Za-z .'-]{3,}", line):
            return line.strip()
    return re.sub(r"[_\-]", " ", fallback_filename).rsplit(".", 1)[0]

# Processing section
if files:
    st.session_state.stats['total'] = len(files)
    progress_bar = st.progress(0)
    log_box = st.container()
    processed_set = set()

    for idx, pdf in enumerate(files):
        progress_bar.progress((idx + 1) / len(files))
        pdf_bytes = pdf.getvalue()

        with log_box:
            st.info(f"📄 Processing `{pdf.name}`")

        try:
            raw = extract_all_text(pdf_bytes)
            if not raw.strip():
                raise Exception("No text extracted")

            with st.spinner("Generating summary..."):
                summary = summarize_resume(raw)

            name = extract_candidate_name(summary, pdf.name)
            cid = make_candidate_id(name)

            if cid in processed_set:
                continue
            processed_set.add(cid)

            existing = collection.get(where={"name": name})["ids"]
            if existing:
                if not st.checkbox(f"🔁 `{name}` exists. Overwrite?", key=f"ow_{cid}_{idx}"):
                    st.info(f"Skipped `{name}`")
                    continue
                collection.delete(where={"name": name})

            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
                ids=[cid]
            )
            if hasattr(chroma_client, "persist"):
                chroma_client.persist()

            # Update results
            st.session_state.results.append({
                "name": name,
                "cid": cid,
                "filename": pdf.name,
                "raw": raw[:700] + "..." if len(raw) > 700 else raw,
                "summary": summary[:500] + "..." if len(summary) > 500 else summary
            })
            st.session_state.stats['processed'] += 1

            with log_box:
                st.success(f"✅ Stored résumé for **{name}** (ID: `{cid}`)")

        except Exception as e:
            st.session_state.stats['errors'] += 1
            with log_box:
                st.error(f"❌ `{pdf.name}` failed: {str(e)}")

# Result Display
if st.session_state.results:
    st.markdown("## 📋 Processed Résumés")
    for r in st.session_state.results:
        with st.expander(f"👤 {r['name']}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**📝 Raw Text**")
                st.text_area("Raw", r["raw"], height=250)
            with c2:
                st.markdown("**📋 Summary**")
                st.text_area("Summary", r["summary"], height=250)

# Action buttons
if st.session_state.results:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Upload More"):
            pass  # just keeps state
    with col2:
        if st.button("🗑️ Clear All"):
            st.session_state.stats = {'processed': 0, 'errors': 0, 'total': 0}
            st.session_state.results = []
            st.rerun()