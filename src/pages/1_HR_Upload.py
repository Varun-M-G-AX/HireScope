import io, re, json, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract

# Ensure these are correctly defined and accessible in your utils.py
from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(
    page_title="HireScope - Upload Résumés",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Management ---
if "results" not in st.session_state:
    st.session_state.results = []
if "stats" not in st.session_state:
    st.session_state.stats = {"processed": 0, "errors": 0, "total_uploaded": 0}

# --- Header UI ---
st.title("💼 HireScope AI")
st.markdown("Unlock the potential of your hiring process with **AI-powered Résumé Management**.")

# --- Sidebar Metrics ---
with st.sidebar:
    st.subheader("📊 Session Statistics")
    st.markdown("Track your résumé processing progress.")
    st.metric("Résumés Processed", st.session_state.stats["processed"])
    st.metric("Processing Errors", st.session_state.stats["errors"])
    st.metric("Total Uploaded", st.session_state.stats["total_uploaded"])
    st.markdown("---")
    if st.button("🔄 Reset All Stats", help="Clear all session statistics and processed results."):
        st.session_state.stats = {"processed": 0, "errors": 0, "total_uploaded": 0}
        st.session_state.results.clear()
        st.rerun()

# --- HR Upload Form ---
st.subheader("📥 Upload Résumés")
st.markdown("Effortlessly upload and process candidate résumés.")

with st.form("hr_upload_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        hr_name = st.text_input(
            "Your name (HR representative)",
            placeholder="e.g., Jane Doe",
            help="Enter your name for tracking uploads."
        )
    with col2:
        files = st.file_uploader(
            "Upload up to 15 Résumé PDFs",
            type="pdf",
            accept_multiple_files=True,
            help="Select PDF files (maximum 15) for AI processing."
        )

    submitted = st.form_submit_button("🚀 Start Processing")

# --- Extractor Functions (No UI Changes Needed Here) ---
def extract_all_text(pdf_bytes):
    """
    Attempts to extract text from a PDF using multiple libraries,
    prioritizing methods that yield more content.
    """
    extractors = [
        # PyMuPDF (fitz) for general text extraction
        lambda: "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf")),
        # pdfminer.six for robust text extraction
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        # pdfplumber for text extraction with layout awareness
        lambda: "\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
        # PyPDF2 for basic text extraction
        lambda: "".join(p.extract_text() or "" for p in PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages),
        # pytesseract (OCR) as a fallback for scanned PDFs
        lambda: "\n".join(pytesseract.image_to_string(img, config='--psm 6') for img in convert_from_bytes(pdf_bytes, dpi=300))
    ]
    for ext in extractors:
        try:
            out = ext()
            # Return if significant text is extracted
            if out and len(out.strip()) > 100:
                return out
        except Exception as e:
            # print(f"Extractor failed: {ext.__name__}, Error: {e}") # For debugging
            continue
    return ""

def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    """
    Extracts candidate name from the AI-generated summary (preferably JSON),
    or falls back to pattern matching or filename.
    """
    # Try to parse as JSON first, as summarize_resume is designed to return JSON
    try:
        data = json.loads(summary)
        if isinstance(data, dict) and data.get("name"):
            return data["name"].strip()
    except json.JSONDecodeError:
        pass # Not a valid JSON, proceed to other methods

    # Fallback 1: Regex patterns for "Name:" or "Full Name:"
    patterns = [r"(?i)^name[:\-]?\s*(.+)$", r"(?i)^full name[:\-]?\s*(.+)$"]
    for p in patterns:
        match = re.search(p, summary, re.M)
        if match:
            return match.group(1).strip()

    # Fallback 2: Look for capitalized words in the first few lines
    for line in summary.split("\n")[:5]: # Check first 5 lines
        line = line.strip("- ")
        # Simple heuristic: two capitalized words (likely first and last name)
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", line):
            return line

    # Fallback 3: Use the filename
    return fallback_filename.rsplit(".", 1)[0].replace("_", " ").title() # Title case for better display

# --- Processing Files ---
if submitted: # Only proceed if form was submitted
    # Guards for Form Submission
    if not hr_name:
        st.error("❗ Please enter your name to proceed with the upload.")
        st.stop()
    if not files:
        st.info("⬆️ Please upload at least one PDF résumé to start.")
        st.stop()
    if len(files) > 15:
        st.error(f"⚠️ You've selected {len(files)} files. Please upload a maximum of 15 résumés at once.")
        st.stop()

    st.markdown("---")
    st.subheader("🚀 Processing Résumés")
    st.info("Please wait while we process your uploaded résumés. This may take a few moments per file.")
    processing_bar = st.progress(0, text="Starting processing...")
    
    # Placeholder for current file status messages
    file_status_placeholder = st.empty()

    for i, pdf in enumerate(files):
        current_progress = (i + 1) / len(files)
        processing_bar.progress(current_progress, text=f"Processing **{pdf.name}**...")
        
        st.session_state.stats["total_uploaded"] += 1
        
        try:
            file_status_placeholder.info(f"Extracting text from **{pdf.name}**...")
            raw = extract_all_text(pdf.getvalue())
            
            if not raw.strip():
                raise Exception("No readable text could be extracted from the PDF.")

            file_status_placeholder.info(f"Summarizing **{pdf.name}** with AI (GPT-4o)...")
            summary = summarize_resume(raw)
            
            # If summarization failed or returned empty
            if not summary.strip():
                raise Exception("AI summarization failed to return content.")

            name = extract_candidate_name(summary, pdf.name)
            cid = make_candidate_id(name)

            # Duplicate Check
            existing_candidates_ids = collection.get(where={"name": name})["ids"]
            if existing_candidates_ids:
                # Use a unique key for the checkbox to prevent issues with multiple files
                overwrite_choice = file_status_placeholder.checkbox(
                    f"A résumé for **{name}** already exists. Overwrite it?",
                    key=f"overwrite_{cid}_{i}",
                    value=False # Default to NOT overwriting
                )
                if not overwrite_choice:
                    file_status_placeholder.warning(f"⏩ Skipped **{name}** (already exists, not overwritten).")
                    st.toast(f"Skipped {name}", icon="⏭️")
                    continue # Skip to the next file
                else:
                    collection.delete(where={"name": name})
                    file_status_placeholder.info(f"🗑️ Overwriting existing entry for **{name}**.")
                    st.toast(f"Overwriting {name}", icon="🔄")

            # Save to ChromaDB
            file_status_placeholder.info(f"Saving **{name}** to database...")
            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
                ids=[cid]
            )
            # Persist the changes to disk if the client supports it
            if hasattr(chroma_client, "persist"):
                chroma_client.persist()

            st.session_state.stats["processed"] += 1
            st.session_state.results.append({
                "name": name,
                "cid": cid,
                "summary": summary, # Store full summary
                "raw": raw,         # Store full raw text
                "filename": pdf.name
            })
            file_status_placeholder.success(f"✅ Successfully processed and stored résumé for **{name}** (ID: `{cid}`).")
            st.toast(f"Résumé for {name} saved!", icon="�") # ephemeral notification

        except Exception as e:
            st.session_state.stats["errors"] += 1
            file_status_placeholder.error(f"❌ Error processing **{pdf.name}**: {e}")
            st.toast(f"Error with {pdf.name}", icon="⚠️")

    processing_bar.progress(1.0, text="Processing complete!")
    file_status_placeholder.success("All selected résumés have been processed!")
    st.balloons() # Celebrate completion!

# --- Show Summaries ---
if st.session_state.results:
    st.markdown("---")
    st.subheader("📄 Processed Résumé Results")
    st.markdown("Review the extracted summaries and raw text for each processed résumé.")
    
    # Use st.expander for each result for a cleaner look
    for i, res in enumerate(st.session_state.results):
        with st.expander(f"**👤 {res['name']}** — *{res['filename']}* (ID: `{res['cid']}`)"):
            st.write(f"**Uploaded By:** {hr_name}") # Display who uploaded it
            tab1, tab2 = st.tabs(["AI Summary", "Raw Extracted Text"])
            with tab1:
                st.markdown("---")
                st.write("**AI-Generated Summary:**")
                # Attempt to pretty-print JSON if the summary is valid JSON
                try:
                    summary_json = json.loads(res['summary'])
                    st.json(summary_json)
                except json.JSONDecodeError:
                    st.markdown(res['summary']) # Fallback to markdown if not JSON
            with tab2:
                st.markdown("---")
                st.write("**Raw Extracted Text:**")
                st.text_area("Full Raw Text", res['raw'], height=300, key=f"raw_text_{i}", disabled=True)

st.markdown("---")
st.info("You can now head over to the **Chat** page to query your uploaded résumés!")
