import io, re, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection
import time

st.set_page_config(page_title="Résumé Upload", page_icon="📂", layout="wide")

# Custom CSS for animations and layout
st.markdown("""
<style>
.upload-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: white;
    animation: slideInLeft 0.6s ease-out;
}

.processing-card {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(252, 182, 159, 0.3);
    animation: pulse 2s infinite;
}

.completed-card {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(168, 237, 234, 0.3);
    animation: slideInRight 0.8s ease-out;
    transform: translateX(0);
}

.error-card {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(255, 154, 158, 0.3);
    animation: shake 0.5s ease-in-out;
}

.progress-container {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
    backdrop-filter: blur(10px);
}

.side-by-side {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}

.left-panel, .right-panel {
    flex: 1;
    animation: fadeInUp 0.8s ease-out;
}

.text-display {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    line-height: 1.4;
    max-height: 400px;
    overflow-y: auto;
    margin: 0.5rem 0;
}

.candidate-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    animation: bounceIn 0.6s ease-out;
}

.candidate-avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(45deg, #667eea, #764ba2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
}

.stats-container {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}

.stat-box {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    animation: zoomIn 0.5s ease-out;
}

@keyframes slideInLeft {
    from { transform: translateX(-100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeInUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

@keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); opacity: 1; }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); }
}

@keyframes zoomIn {
    from { transform: scale(0); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
    20%, 40%, 60%, 80% { transform: translateX(10px); }
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #667eea, #764ba2);
}
</style>
""", unsafe_allow_html=True)

st.title("📂 HR Résumé Uploader")

# Header section
col1, col2 = st.columns([2, 1])
with col1:
    hr_name = st.text_input("Your (HR) name", placeholder="Enter your name...")
with col2:
    if 'upload_stats' not in st.session_state:
        st.session_state.upload_stats = {'processed': 0, 'errors': 0, 'total': 0}
    
    st.markdown(f"""
    <div class="stats-container">
        <div class="stat-box">
            <h4>📊 {st.session_state.upload_stats['processed']}</h4>
            <small>Processed</small>
        </div>
        <div class="stat-box">
            <h4>❌ {st.session_state.upload_stats['errors']}</h4>
            <small>Errors</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

files = st.file_uploader("Upload up to 10 résumé PDFs", type="pdf", accept_multiple_files=True)

if not hr_name:
    st.warning("Enter your name first.")
    st.stop()

if files and len(files) > 10:
    st.error("⚠️ Upload 10 PDFs max.")
    st.stop()

def extract_all_text(pdf_bytes: bytes) -> str:
    text = ""
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "\n".join(p.get_text() for p in doc)
    except:
        pass
    
    if not text.strip():
        try:
            text = extract_text(io.BytesIO(pdf_bytes))
        except:
            pass
    
    if not text.strip():
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        except:
            pass
    
    if not text.strip():
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = "".join(p.extract_text() or "" for p in reader.pages)
        except:
            pass
    
    if not text.strip():
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            text = "\n".join(pytesseract.image_to_string(img) for img in images)
        except:
            pass
    
    return text

def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    patterns = [
        r"(?i)^name[:\-]?\s*(.+)$",
        r"(?i)^candidate name[:\-]?\s*(.+)$",
        r"(?i)^full name[:\-]?\s*(.+)$",
    ]
    
    for pat in patterns:
        m = re.search(pat, summary, re.M)
        if m:
            return m.group(1).strip()
    
    for line in summary.splitlines():
        line = line.strip("-• \t")
        if line and re.fullmatch(r"[A-Z][A-Za-z .'-]{3,}", line):
            return line.strip()
    
    return re.sub(r"[_-]", " ", fallback_filename).rsplit(".", 1)[0]

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = set()
if 'completed_resumes' not in st.session_state:
    st.session_state.completed_resumes = []

# Upload processing with animations
if files:
    st.session_state.upload_stats['total'] = len(files)
    
    # Progress overview
    progress_container = st.container()
    with progress_container:
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        overall_progress = st.progress(0)
        status_text = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Processing area
    processing_area = st.container()
    
    # Completed resumes area (side by side)
    completed_area = st.container()
    
    for idx, pdf in enumerate(files):
        # Update overall progress
        progress = (idx) / len(files)
        overall_progress.progress(progress)
        status_text.text(f"Processing {idx + 1}/{len(files)}: {pdf.name}")
        
        with processing_area:
            # Processing animation
            st.markdown(f"""
            <div class="processing-card">
                <h4>🔄 Processing: {pdf.name}</h4>
                <p>Extracting text and generating summary...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Small delay for animation effect
            time.sleep(0.3)
        
        try:
            raw = extract_all_text(pdf.getvalue())
        except Exception as e:
            with processing_area:
                st.markdown(f"""
                <div class="error-card">
                    <h4>❌ Error: {pdf.name}</h4>
                    <p>Could not read PDF: {e}</p>
                </div>
                """, unsafe_allow_html=True)
            st.session_state.upload_stats['errors'] += 1
            continue
        
        if not raw.strip():
            with processing_area:
                st.markdown(f"""
                <div class="error-card">
                    <h4>❌ No text extracted: {pdf.name}</h4>
                    <p>PDF appears to be empty or unreadable.</p>
                </div>
                """, unsafe_allow_html=True)
            st.session_state.upload_stats['errors'] += 1
            continue
        
        # Generate summary
        with st.spinner("Summarizing résumé..."):
            summary = summarize_resume(raw)
        
        name = extract_candidate_name(summary, pdf.name)
        cid = make_candidate_id(name)
        
        if cid in st.session_state.processed:
            continue
        
        st.session_state.processed.add(cid)
        
        # Check for existing candidate
        overwrite = False
        if collection.get(where={"name": name})["ids"]:
            overwrite = st.checkbox(f"🔄 `{name}` exists. Overwrite?", key=f"ow_{cid}_{idx}")
            if not overwrite:
                st.info(f"Skipped `{name}`.")
                continue
            collection.delete(where={"name": name})
        
        # Store in database
        collection.add(
            documents=[summary],
            metadatas=[{"candidate_id": cid, "name": name, "uploaded_by": hr_name}],
            ids=[cid]
        )
        
        if hasattr(chroma_client, "persist"):
            chroma_client.persist()
        
        # Add to completed resumes
        st.session_state.completed_resumes.append({
            'name': name,
            'cid': cid,
            'raw': raw,
            'summary': summary,
            'filename': pdf.name
        })
        
        st.session_state.upload_stats['processed'] += 1
        
        # Clear processing animation
        processing_area.empty()
        
        # Show completed animation
        with completed_area:
            st.markdown(f"""
            <div class="completed-card">
                <div class="candidate-header">
                    <div class="candidate-avatar">{name[0].upper()}</div>
                    <div>
                        <h3>✅ {name}</h3>
                        <small>ID: {cid} | File: {pdf.name}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Side by side text display
            st.markdown('<div class="side-by-side">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Raw Extracted Text")
                raw_display = raw[:2000].replace('\n', '<br>').replace(' ', '&nbsp;')
                truncated_msg = '<br><i>... (truncated)</i>' if len(raw) > 2000 else ''
                st.markdown(f"""
                <div class="text-display">
                    {raw_display}
                    {truncated_msg}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("#### 📋 Structured Summary")
                summary_display = summary.replace('\n', '<br>').replace(' ', '&nbsp;')
                st.markdown(f"""
                <div class="text-display">
                    {summary_display}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")
    
    # Final progress update
    overall_progress.progress(1.0)
    status_text.text(f"✅ Completed processing {len(files)} files!")
    
    # Summary statistics
    if st.session_state.completed_resumes:
        st.markdown(f"""
        <div class="upload-card">
            <h3>🎉 Upload Complete!</h3>
            <p>Successfully processed <strong>{st.session_state.upload_stats['processed']}</strong> résumés</p>
            <p>Errors: <strong>{st.session_state.upload_stats['errors']}</strong></p>
        </div>
        """, unsafe_allow_html=True)

# Display all completed resumes if any exist
if st.session_state.completed_resumes:
    st.markdown("## 📚 All Processed Résumés")
    
    for resume in st.session_state.completed_resumes:
        with st.expander(f"👤 {resume['name']} ({resume['cid']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Raw Text:**")
                st.text_area("", resume['raw'], height=300, key=f"raw_{resume['cid']}")
            
            with col2:
                st.markdown("**Summary:**")
                st.text_area("", resume['summary'], height=300, key=f"summary_{resume['cid']}")

# Clear processed data button
if st.button("🗑️ Clear All Data"):
    st.session_state.processed = set()
    st.session_state.completed_resumes = []
    st.session_state.upload_stats = {'processed': 0, 'errors': 0, 'total': 0}
    st.experimental_rerun()