# utils.py must define summarize_resume and make_candidate_id properly for this to work.

import io, re, json, streamlit as st, fitz, pdfplumber, PyPDF2
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="HireScope AI - Resume Processor",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
# Track stats, results, and staged files in session
if "results" not in st.session_state:
    st.session_state.results = []
if "stats" not in st.session_state:
    st.session_state.stats = {"processed": 0, "errors": 0}
if "processed_files_data" not in st.session_state:
    st.session_state.processed_files_data = []


# --- HEADER ---
st.title("💼 HireScope AI")
st.caption("A Smart AI-Powered Résumé Management & Analysis Tool")


# --- CORE FUNCTIONS (Unchanged, but vital for context) ---

def extract_all_text(pdf_bytes):
    """Chain-tries multiple PDF text extractors for robustness, includes OCR fallback."""
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
            # Return if we got a meaningful amount of text
            if out and len(out.strip()) > 100:
                return out
        except Exception:
            continue
    return ""

def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    """Extracts candidate name from summary JSON, then tries regex, and falls back to filename."""
    try:
        data = json.loads(summary)
        if isinstance(data, dict) and data.get("name"):
            return data["name"].strip()
    except (json.JSONDecodeError, AttributeError):
        pass

    # Regex patterns to find name
    patterns = [r"(?i)^name[:\-]?\s*(.+)$", r"(?i)^full name[:\-]?\s*(.+)$"]
    for p in patterns:
        match = re.search(p, summary, re.M)
        if match: return match.group(1).strip()
    
    # Heuristic: Find a capitalized name-like pattern in the first few lines
    for line in summary.split("\n")[:5]:
        line = line.strip("- ")
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", line):
            return line

    # Fallback to a cleaned-up filename
    return fallback_filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()


# --- SIDEBAR ---
with st.sidebar:
    st.subheader("📊 Session Stats")
    st.metric("✅ Résumés Processed", st.session_state.stats["processed"])
    st.metric("❌ Errors Encountered", st.session_state.stats["errors"])
    
    st.divider()
    
    if st.button("Clear Session & Reset Stats", use_container_width=True):
        st.session_state.stats = {"processed": 0, "errors": 0}
        st.session_state.results.clear()
        st.session_state.processed_files_data.clear()
        st.rerun()

# --- MAIN PAGE LAYOUT ---

# --- STEP 1: UPLOAD & PROCESS ---
with st.container(border=True):
    st.subheader("Step 1: Upload Résumés")
    col1, col2 = st.columns([2, 3])
    with col1:
        hr_name = st.text_input("Your Name (HR Representative)", placeholder="e.g., Jane Doe")
    with col2:
        files = st.file_uploader(
            "Upload up to 15 Résumé PDFs at a time",
            type="pdf",
            accept_multiple_files=True,
            help="You can drag and drop multiple PDF files here."
        )

    process_button = st.button("Process Résumés", type="primary", use_container_width=True, disabled=not (hr_name and files))

if process_button:
    if len(files) > 15:
        st.error("❌ You can upload a maximum of 15 files at a time. Please reduce the number of files.")
        st.stop()
    
    st.session_state.processed_files_data = []
    st.session_state.stats["errors"] = 0 # Reset errors for this batch
    
    st.subheader("🔄 Processing Files...")
    progress_bar = st.progress(0, "Initializing...")
    
    for i, pdf in enumerate(files):
        try:
            progress_bar.progress((i) / len(files), f"Reading {pdf.name}...")
            raw_text = extract_all_text(pdf.getvalue())
            if not raw_text.strip():
                raise ValueError("No text could be extracted from this PDF.")
            
            progress_bar.progress((i + 0.5) / len(files), f"Summarizing {pdf.name} with AI...")
            with st.spinner(f"🤖 AI is summarizing {pdf.name}..."):
                summary = summarize_resume(raw_text) # Assumes this is a call to a powerful LLM
            
            candidate_name = extract_candidate_name(summary, pdf.name)
            candidate_id = make_candidate_id(candidate_name)

            # Stage the data instead of writing directly
            st.session_state.processed_files_data.append({
                "name": candidate_name,
                "cid": candidate_id,
                "summary": summary,
                "raw": raw_text,
                "filename": pdf.name,
                "uploaded_by": hr_name
            })
            
        except Exception as e:
            st.session_state.stats["errors"] += 1
            st.warning(f"⚠️ Could not process {pdf.name}. Reason: {e}")
    
    progress_bar.progress(1.0, "Processing complete! Ready for next step.")

# --- STEP 2: HANDLE DUPLICATES & SAVE ---
if st.session_state.processed_files_data:
    with st.container(border=True):
        st.subheader("Step 2: Review & Save to Database")
        
        # Identify duplicates (in DB or in the current upload batch)
        duplicates_to_resolve = []
        processed_names = set()

        for data in st.session_state.processed_files_data:
            is_db_dup = collection.get(where={"name": data["name"]})["ids"]
            is_batch_dup = data["name"] in processed_names
            if is_db_dup or is_batch_dup:
                duplicates_to_resolve.append({
                    "data": data,
                    "reason": "Already in database" if is_db_dup else "Duplicate in this upload"
                })
            processed_names.add(data["name"])

        # Form to resolve duplicates if any exist
        if duplicates_to_resolve:
            st.info(f"Found {len(duplicates_to_resolve)} potential duplicate(s). Please review and confirm.")
            with st.form("duplicate_resolution_form"):
                overwrite_choices = {}
                for dup in duplicates_to_resolve:
                    name = dup["data"]["name"]
                    reason = dup["reason"]
                    label = f"Overwrite **{name}**? (Reason: {reason})"
                    overwrite_choices[name] = st.checkbox(label, value=True, key=f"ow_{dup['data']['cid']}")
                
                submitted = st.form_submit_button("Confirm Overwrites and Save All Résumés", use_container_width=True)
        else:
            # If no duplicates, provide a simple save button
            with st.form("save_form"):
                 st.success("✅ All résumés are new. Ready to save to the database.")
                 submitted = st.form_submit_button("Save All to Database", use_container_width=True, type="primary")
                 overwrite_choices = {} # No overwrites needed

        # Processing logic after form submission
        if submitted:
            with st.spinner("💾 Saving to database... Please wait."):
                final_results = []
                # Clear previous results to show only the current batch
                st.session_state.results.clear()
                
                for data in st.session_state.processed_files_data:
                    name = data["name"]
                    cid = data["cid"]

                    # Skip if it's a duplicate and user chose not to overwrite
                    if name in overwrite_choices and not overwrite_choices[name]:
                        st.warning(f"Skipped duplicate: {name}")
                        continue
                    
                    # If it's a duplicate and user wants to overwrite, delete old entry first
                    if name in overwrite_choices and overwrite_choices[name]:
                         collection.delete(where={"name": name})

                    # Add to ChromaDB
                    collection.add(
                        documents=[data["summary"]],
                        metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": data["uploaded_by"]}],
                        ids=[cid]
                    )
                    
                    st.session_state.stats["processed"] += 1
                    result_entry = {
                        "name": name,
                        "cid": cid,
                        "summary": data['summary'][:1200], # Truncate for display
                        "raw": data['raw'][:1200],       # Truncate for display
                        "filename": data['filename']
                    }
                    st.session_state.results.append(result_entry)
                    final_results.append(result_entry)

                if hasattr(chroma_client, "persist"):
                    chroma_client.persist()

                st.success(f"🎉 Successfully processed and saved {len(final_results)} résumés!")
                # Clear the staged data after processing
                st.session_state.processed_files_data = []
                st.rerun() # Rerun to reflect stat changes and show results cleanly


# --- STEP 3: REVIEW RESULTS ---
if st.session_state.results:
    with st.container(border=True):
        st.subheader(f"Step 3: Review Latest Batch Results ({len(st.session_state.results)} candidates)")
        for res in st.session_state.results:
            with st.expander(f"👤 **{res['name']}** — (from `{res['filename']}`)", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📄 AI Summary")
                    st.text_area("Summary", res['summary'], height=300, key=f"summary_{res['cid']}")
                with col2:
                    st.subheader("📝 Raw Extracted Text")
                    st.text_area("Raw Text", res['raw'], height=300, key=f"raw_{res['cid']}")