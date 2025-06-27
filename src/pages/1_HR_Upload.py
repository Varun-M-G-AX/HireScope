import io, re, json, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(page_title="Upload Candidate Résumés", page_icon="📂", layout="wide")

# ────── CSS Styling ──────
st.markdown("""
<style>
.upload-header {
    background: linear-gradient(90deg, #4e54c8, #8f94fb);
    padding: 1.2rem 2rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.success-box, .error-box {
    border-radius: 6px;
    padding: 0.8rem;
    margin: 0.5rem 0;
    color: white;
    font-weight: 500;
    animation: slideIn 0.3s ease-out;
}
.success-box { background: #28a745; }
.error-box { background: #dc3545; }
.text-box {
    background: #f9f9f9;
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.88rem;
    font-family: monospace;
    overflow-y: auto;
    max-height: 250px;
    white-space: pre-wrap;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>
""", unsafe_allow_html=True)

# ────── Header ──────
st.markdown("""
<div class="upload-header">
    <h2>📂 HR Candidate Résumé Uploader</h2>
    <p>Upload and parse PDF résumés. Results are stored in your ChromaDB vector store.</p>
</div>
""", unsafe_allow_html=True)

# ────── State ──────
if "results" not in st.session_state:
    st.session_state.results = []
if "stats" not in st.session_state:
    st.session_state.stats = {"processed": 0, "errors": 0}

# ────── Inputs ──────
cols = st.columns([4, 1])
with cols[0]:
    hr_name = st.text_input("Your Name (HR)", placeholder="e.g., Jane Smith")
    files = st.file_uploader("Upload Résumés (PDF only)", type="pdf", accept_multiple_files=True)
with cols[1]:
    st.metric("Processed", st.session_state.stats["processed"])
    st.metric("Errors", st.session_state.stats["errors"])

if not hr_name:
    st.warning("Please enter your name.")
    st.stop()
if files and len(files) > 10:
    st.error("Upload a maximum of 10 files at once.")
    st.stop()

# ────── Extraction Pipeline ──────
def extract_all_text(pdf_bytes: bytes) -> str:
    extractors = [
        lambda: "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf")),
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        lambda: "\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
        lambda: "".join(p.extract_text() or "" for p in PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages),
        lambda: "\n".join(pytesseract.image_to_string(img) for img in convert_from_bytes(pdf_bytes, dpi=300))
    ]
    for extractor in extractors:
        try:
            result = extractor()
            if result.strip():
                return result
        except: pass
    return ""

# ────── Name from JSON summary ──────
def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    try:
        data = json.loads(summary)
        if "name" in data:
            return data["name"].strip()
    except: pass

    # fallback regex
    pats = [r"(?i)^name[:\-]?\s*(.+)$", r"(?i)^full name[:\-]?\s*(.+)$"]
    for pat in pats:
        m = re.search(pat, summary, re.M)
        if m:
            return m.group(1).strip()

    for line in summary.splitlines():
        line = line.strip("-• \t")
        if re.fullmatch(r"[A-Z][A-Za-z .'-]{3,}", line):
            return line
    return re.sub(r"[_\-]", " ", fallback_filename).rsplit(".", 1)[0]

# ────── Process Uploaded PDFs ──────
if files:
    bar = st.progress(0)
    for idx, file in enumerate(files):
        try:
            pdf_bytes = file.getvalue()
            raw = extract_all_text(pdf_bytes)
            if not raw.strip(): raise Exception("Empty or non-extractable content")

            with st.spinner("Summarising résumé with GPT-4o..."):
                summary = summarize_resume(raw)

            name = extract_candidate_name(summary, file.name)
            cid = make_candidate_id(name)

            existing = collection.get(where={"name": name})
            if existing["ids"]:
                if not st.checkbox(f"Overwrite {name}?", key=f"ck_{cid}_{idx}"):
                    st.info(f"Skipped {name}")
                    continue
                collection.delete(where={"name": name})

            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
                ids=[cid]
            )
            if hasattr(chroma_client, "persist"): chroma_client.persist()

            st.session_state.results.append({
                "name": name,
                "cid": cid,
                "filename": file.name,
                "raw": raw[:1200],
                "summary": summary[:1200]
            })
            st.session_state.stats["processed"] += 1

            st.markdown(f"""
                <div class='success-box'>
                    ✅ Stored résumé for <b>{name}</b> &mdash; ID: <code>{cid}</code>
                </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.session_state.stats["errors"] += 1
            st.markdown(f"<div class='error-box'>❌ Error with {file.name}: {e}</div>", unsafe_allow_html=True)

        bar.progress((idx + 1) / len(files))

# ────── Show Results ──────
if st.session_state.results:
    st.subheader("📝 Processed Résumés")
    for res in st.session_state.results:
        with st.expander(f"👤 {res['name']} — {res['filename']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Raw Text:**")
                st.markdown(f"<div class='text-box'>{res['raw']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("**Summary:**")
                st.markdown(f"<div class='text-box'>{res['summary']}</div>", unsafe_allow_html=True)

    colA, colB = st.columns(2)
    with colA:
        if st.button("🔄 Upload More"):
            pass
    with colB:
        if st.button("🗑️ Clear All"):
            st.session_state.results.clear()
            st.session_state.stats = {"processed": 0, "errors": 0}
            st.rerun()