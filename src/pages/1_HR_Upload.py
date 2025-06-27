import io, re, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(page_title="Résumé Upload", page_icon="📂", layout="wide")

# ── Styles for dark/light and animations
st.markdown("""
<style>
.upload-header {
    background: linear-gradient(90deg, #5e60ce, #7209b7);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1.5rem;
}

.processing-item, .success-item, .error-item {
    background: var(--background-secondary);
    border-left: 4px solid var(--primary-color);
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 5px;
    animation: slideIn 0.3s ease-out;
}

.success-item { border-color: #28a745; }
.error-item { border-color: #dc3545; }

.text-preview {
    background: var(--background-secondary);
    border: 1px solid var(--secondary-background-color);
    border-radius: 5px;
    padding: 0.75rem;
    font-family: monospace;
    font-size: 0.85rem;
    max-height: 280px;
    overflow-y: auto;
    white-space: pre-wrap;
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# ── Header
st.markdown("""
<div class="upload-header">
    <h1>📂 HR Résumé Uploader</h1>
    <p>Upload multiple PDFs and process them efficiently</p>
</div>
""", unsafe_allow_html=True)

# ── Session state
if "results" not in st.session_state:
    st.session_state.results = []
if "stats" not in st.session_state:
    st.session_state.stats = {"processed": 0, "errors": 0}

# ── Input
col1, col2 = st.columns([3, 1])
with col1:
    hr_name = st.text_input("👤 Your (HR) Name", placeholder="e.g., Jane Doe")
    files = st.file_uploader("📎 Upload Résumé PDFs (max 10)", type="pdf", accept_multiple_files=True)

with col2:
    st.metric("✅ Processed", st.session_state.stats["processed"])
    st.metric("❌ Errors", st.session_state.stats["errors"])

if not hr_name:
    st.warning("Please enter your name to continue.")
    st.stop()
if files and len(files) > 10:
    st.error("⚠️ Maximum 10 files allowed.")
    st.stop()

# ── Text extraction fallback pipeline
def extract_all_text(pdf_bytes: bytes) -> str:
    methods = [
        lambda: "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf")),
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        lambda: "\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
        lambda: "".join(p.extract_text() or "" for p in PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages),
        lambda: "\n".join(pytesseract.image_to_string(img) for img in convert_from_bytes(pdf_bytes, dpi=300))
    ]
    for m in methods:
        try:
            txt = m()
            if txt.strip():
                return txt
        except: pass
    return ""

# ── Extract name fallback helper
def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    patterns = [
        r"(?i)^name[:\-]?\s*(.+)$",
        r"(?i)^candidate name[:\-]?\s*(.+)$",
        r"(?i)^full name[:\-]?\s*(.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, summary, re.M)
        if m: return m.group(1).strip()
    for line in summary.splitlines():
        line = line.strip("-• \t")
        if re.fullmatch(r"[A-Z][A-Za-z .'-]{3,}", line): return line.strip()
    return re.sub(r"[_-]", " ", fallback_filename).rsplit(".", 1)[0]

# ── Process uploads
processed_ids = set()
if files:
    bar = st.progress(0)
    total = len(files)

    for idx, pdf in enumerate(files):
        pdf_bytes = pdf.getvalue()
        bar.progress((idx + 1) / total)

        with st.container():
            st.markdown(f'<div class="processing-item">🔄 Processing <code>{pdf.name}</code></div>', unsafe_allow_html=True)

        try:
            raw = extract_all_text(pdf_bytes)
            if not raw.strip(): raise Exception("No extractable text")

            with st.spinner("Summarising résumé with GPT‑4o…"):
                summary = summarize_resume(raw)

            name = extract_candidate_name(summary, pdf.name)
            cid = make_candidate_id(name)
            if cid in processed_ids: continue
            processed_ids.add(cid)

            # Check if exists
            if collection.get(where={"name": name})["ids"]:
                if not st.checkbox(f"🔄 `{name}` exists. Overwrite?", key=f"ow_{cid}_{idx}"):
                    st.info(f"Skipped `{name}`."); continue
                collection.delete(where={"name": name})

            # Store in ChromaDB
            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
                ids=[cid]
            )
            if hasattr(chroma_client, "persist"): chroma_client.persist()

            # Save results
            st.session_state.results.append({
                "name": name,
                "cid": cid,
                "filename": pdf.name,
                "raw": raw.strip(),
                "summary": summary.strip()
            })
            st.session_state.stats["processed"] += 1

            st.markdown(f'<div class="success-item">✅ Stored résumé for <b>{name}</b> (ID: <code>{cid}</code>)</div>', unsafe_allow_html=True)

        except Exception as e:
            st.session_state.stats["errors"] += 1
            st.markdown(f'<div class="error-item">❌ Error with `{pdf.name}`: {str(e)}</div>', unsafe_allow_html=True)

    bar.progress(1.0)

# ── Results
if st.session_state.results:
    st.subheader("📄 Processed Résumés")
    for i, r in enumerate(st.session_state.results):
        with st.expander(f"👤 {r['name']} – {r['filename']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📃 Raw Text:**")
                st.markdown(f'<div class="text-preview">{r["raw"]}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown("**📋 Summary:**")
                st.markdown(f'<div class="text-preview">{r["summary"]}</div>', unsafe_allow_html=True)

    colA, colB = st.columns(2)
    with colA:
        if st.button("🔄 Upload More Résumés"):
            pass
    with colB:
        if st.button("🗑️ Clear All Results"):
            st.session_state.results.clear()
            st.session_state.stats = {"processed": 0, "errors": 0}
            st.rerun()
