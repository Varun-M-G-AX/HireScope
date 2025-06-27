import io
import re
import streamlit as st
import fitz  # PyMuPDF
import pdfplumber
import PyPDF2
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract

# Assume these are defined in your utils.py
from utils import summarize_resume, make_candidate_id, chroma_client, collection

# --- 1. PAGE CONFIGURATION & THEME ---
# Sets up the page with a title, icon, wide layout, and a custom theme.
# The theme is designed to work well in both light and dark modes with a blue accent.
st.set_page_config(
    page_title="HireFlow - Résumé Uploader",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "HireFlow: AI-Powered Résumé Processor"
    }
)

# --- 2. CORE FUNCTIONS ---
# Robust text extraction pipeline trying multiple methods for reliability.
def extract_all_text(pdf_bytes: bytes) -> str:
    """Chain-tries multiple PDF text extractors, including an OCR fallback."""
    text = ""
    # Method 1: PyMuPDF (fitz) - Often the most reliable
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "\n".join(p.get_text() for p in doc)
    except Exception:
        pass
    if text.strip(): return text

    # Method 2: pdfminer.six
    try:
        text = extract_text(io.BytesIO(pdf_bytes))
    except Exception:
        pass
    if text.strip(): return text

    # Method 3: pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        pass
    if text.strip(): return text

    # Method 4: PyPDF2
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = "".join(p.extract_text() or "" for p in reader.pages)
    except Exception:
        pass
    if text.strip(): return text

    # Method 5: OCR Fallback (Tesseract) for image-based PDFs
    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
    except Exception:
        pass
    return text

# Improved name extraction with more robust patterns.
def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    """Extracts candidate name from summary, with fallback to filename."""
    # Regex patterns looking for "Name: John Doe" type formats.
    patterns = [
        r"(?i)^name[:\-]?\s*(.+)$",
        r"(?i)^candidate(?: name)?[:\-]?\s*(.+)$",
        r"(?i)^full name[:\-]?\s*(.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, summary, re.M)
        if m: return m.group(1).strip()
    
    # Heuristic: Find a capitalized name-like string in the first few lines.
    for line in summary.splitlines()[:5]:
        line = line.strip("-• \t")
        # Matches "John Doe", "J. Doe", "John Fitzgerald Doe"
        if re.fullmatch(r"[A-Z][a-zA-Z.'-]{1,}(?:\s[A-Z][a-zA-Z.'-]{1,})+", line):
            return line.strip()
            
    # Fallback: Clean up the PDF filename.
    clean_name = re.sub(r"[_-]", " ", fallback_filename).rsplit(".", 1)[0]
    return clean_name.title()


# --- 3. SESSION STATE INITIALIZATION ---
# Using session state to hold data across reruns.
if "staged_files" not in st.session_state:
    st.session_state.staged_files = []
if "final_results" not in st.session_state:
    st.session_state.final_results = []
if "errors" not in st.session_state:
    st.session_state.errors = []


# --- 4. UI: HEADER AND INPUT FORM ---
st.title("HireFlow Résumé Processor")
st.markdown("Upload candidate résumés to automatically extract, summarize, and store their information.")

with st.container(border=True):
    st.subheader("Step 1: Upload Your Files")
    hr_name = st.text_input("👤 Your Name (HR Representative)", placeholder="e.g., Maria Garcia")
    files = st.file_uploader(
        "📂 Upload up to 10 résumé PDFs",
        type="pdf",
        accept_multiple_files=True
    )
    
    # The main trigger for the entire process.
    process_button = st.button(
        "🚀 Process Résumés",
        type="primary",
        use_container_width=True,
        disabled=not (hr_name and files)
    )

if st.sidebar.button("Clear Session and Start Over"):
    st.session_state.staged_files = []
    st.session_state.final_results = []
    st.session_state.errors = []
    st.rerun()

# --- 5. LOGIC: PROCESSING PIPELINE ---
if process_button:
    if len(files) > 10:
        st.error("⚠️ You can upload a maximum of 10 files at a time. Please reduce the count.")
        st.stop()
    
    # Reset state for the new batch
    st.session_state.staged_files = []
    st.session_state.errors = []
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0, "Starting batch processing...")
    
    for i, pdf in enumerate(files):
        try:
            status_placeholder.info(f"⚙️ Processing: `{pdf.name}`...")
            raw_text = extract_all_text(pdf.getvalue())
            
            if not raw_text or not raw_text.strip():
                st.session_state.errors.append({"filename": pdf.name, "error": "No text could be extracted."})
                continue
            
            # This is where you call your AI model
            with st.spinner(f"🤖 AI is summarizing `{pdf.name}`..."):
                summary = summarize_resume(raw_text) 
            
            name = extract_candidate_name(summary, pdf.name)
            cid = make_candidate_id(name)

            # Stage the processed data instead of saving immediately
            st.session_state.staged_files.append({
                "name": name, "cid": cid, "summary": summary, "raw": raw_text,
                "filename": pdf.name, "uploaded_by": hr_name
            })
            
        except Exception as e:
            st.session_state.errors.append({"filename": pdf.name, "error": str(e)})
        
        progress_bar.progress((i + 1) / len(files), f"Completed: `{pdf.name}`")
        
    status_placeholder.success("✅ Batch processing complete! Please review and save below.")
    progress_bar.empty()

# --- 6. UI & LOGIC: DUPLICATE HANDLING AND SAVING ---
if st.session_state.staged_files:
    with st.container(border=True):
        st.subheader("Step 2: Review & Save to Database")
        
        duplicates_to_resolve = []
        processed_names = {f['name'] for f in st.session_state.staged_files}
        
        # Check for duplicates already in the database
        existing_in_db = collection.get(where={"name": {"$in": list(processed_names)}})['ids']

        for data in st.session_state.staged_files:
            if data["name"] in existing_in_db:
                duplicates_to_resolve.append(data)
        
        # Form to handle all duplicates at once
        with st.form("save_to_db_form"):
            if duplicates_to_resolve:
                st.warning("⚠️ Some candidates already exist. Choose whether to overwrite them.")
                overwrite_choices = {}
                for dup in duplicates_to_resolve:
                    label = f"Overwrite **{dup['name']}** (from `{dup['filename']}`)"
                    overwrite_choices[dup['name']] = st.checkbox(label, value=True)
            else:
                st.info("✅ All candidates appear to be new. Ready to save.")
                overwrite_choices = {}

            save_button = st.form_submit_button("💾 Save to Database", use_container_width=True, type="primary")

        # Logic to execute after form submission
        if save_button:
            with st.spinner("Saving data..."):
                saved_count = 0
                st.session_state.final_results = [] # Clear previous results
                
                for data in st.session_state.staged_files:
                    name = data["name"]
                    # If it's a duplicate and the user unchecked the box, skip it.
                    if name in overwrite_choices and not overwrite_choices.get(name):
                        st.toast(f"Skipped {name}", icon="🚫")
                        continue
                    
                    # If it's a duplicate and we're overwriting, delete the old entry.
                    if name in overwrite_choices and overwrite_choices.get(name):
                        collection.delete(where={"name": name})

                    # Add the new or updated entry to ChromaDB.
                    collection.add(
                        documents=[data["summary"]],
                        metadatas=[{"candidate_id": data["cid"], "name": name, "uploaded_by": data["uploaded_by"]}],
                        ids=[data["cid"]]
                    )
                    st.session_state.final_results.append(data)
                    saved_count += 1
                
                # Persist changes to the database if the client supports it.
                if hasattr(chroma_client, "persist"):
                    chroma_client.persist()

            st.success(f"🎉 Success! {saved_count} résumés have been saved to the database.")
            st.session_state.staged_files = [] # Clear the stage
            # A short delay before rerun can improve UX
            import time; time.sleep(1)
            st.rerun()

# --- 7. UI: FINAL RESULTS DISPLAY ---
if st.session_state.errors:
    with st.container(border=True):
        st.subheader("Processing Errors")
        for err in st.session_state.errors:
            st.error(f"**File:** `{err['filename']}` - **Error:** {err['error']}", icon="❌")

if st.session_state.final_results:
    with st.container(border=True):
        st.subheader(f"Step 3: Review Successfully Processed Résumés ({len(st.session_state.final_results)})")
        
        for res in st.session_state.final_results:
            with st.expander(f"👤 **{res['name']}** (from file: `{res['filename']}`)", expanded=False):
                tab1, tab2 = st.tabs(["🤖 AI Summary", "📄 Raw Text"])
                with tab1:
                    st.markdown(res['summary'])
                with tab2:
                    st.text_area("Extracted Text", res['raw'], height=300, key=f"raw_{res['cid']}")