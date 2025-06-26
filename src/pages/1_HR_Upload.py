import io, re, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract

from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(page_title="Résumé Upload", page_icon="📂")
st.title("📂 HR Résumé Uploader")

hr_name = st.text_input("Your (HR) name")
files = st.file_uploader("Upload up to 10 résumé PDFs", type="pdf", accept_multiple_files=True)

if not hr_name:
    st.warning("Enter your name first."); st.stop()
if files and len(files) > 10:
    st.error("⚠️ Upload 10 PDFs max."); st.stop()

# ─────── extract text with multiple fallback strategies ───────
def extract_all_text(pdf_bytes: bytes) -> str:
    text = ""
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "\n".join(p.get_text() for p in doc)
    except: pass
    if not text.strip():
        try: text = extract_text(io.BytesIO(pdf_bytes))
        except: pass
    if not text.strip():
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        except: pass
    if not text.strip():
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = "".join(p.extract_text() or "" for p in reader.pages)
        except: pass
    if not text.strip():
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            text = "\n".join(pytesseract.image_to_string(img) for img in images)
        except: pass
    return text

# ─────── extract name from summary text ───────
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
        if line and re.fullmatch(r"[A-Z][A-Za-z .'-]{3,}", line):
            return line.strip()
    return re.sub(r"[_-]", " ", fallback_filename).rsplit(".", 1)[0]

# ─────── Process uploads ───────
processed = set()
if files:
    for idx, pdf in enumerate(files):
        with st.container(border=True):
            st.markdown(f"### 📄 Processing `{pdf.name}`")
            try:
                raw = extract_all_text(pdf.getvalue())
            except Exception as e:
                st.error(f"❌ Could not read `{pdf.name}`: {e}")
                continue

            if not raw.strip():
                st.error(f"❌ No text extracted from `{pdf.name}`.")
                continue

            with st.spinner("Summarising résumé…"):
                summary = summarize_resume(raw)

            name = extract_candidate_name(summary, pdf.name)
            cid  = make_candidate_id(name)
            if cid in processed:
                continue
            processed.add(cid)

            if collection.get(where={"name": name})["ids"]:
                if not st.checkbox(f"🔄 `{name}` exists. Overwrite?", key=f"ow_{cid}_{idx}"):
                    st.info(f"Skipped `{name}`.")
                    continue
                collection.delete(where={"name": name})

            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
                ids=[cid]
            )
            if hasattr(chroma_client, "persist"):
                chroma_client.persist()

            st.success(f"✅ Stored résumé for **{name}** (ID: `{cid}`)")

            # ─────── Show raw and summary side-by-side
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("📑 Raw Extracted Text"):
                    st.text_area("Raw Text", raw, height=300, key=f"raw_{cid}")
            with col2:
                with st.expander("📋 Structured Summary"):
                    st.text_area("Résumé Summary", summary, height=300, key=f"sum_{cid}")
