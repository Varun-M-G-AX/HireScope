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

# ────── Enhanced CSS Styling with Theme Support ──────
st.markdown("""
<style>
/* Root variables for theme support */
:root {
    --primary-color: #4e54c8;
    --secondary-color: #8f94fb;
    --success-color: #28a745;
    --error-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
}

/* Dark theme overrides */
@media (prefers-color-scheme: dark) {
    :root {
        --success-color: #20c997;
        --error-color: #f14668;
        --warning-color: #ffd43b;
        --info-color: #339af0;
    }
}

.main-header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    padding: 2rem;
    border-radius: 15px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    text-align: center;
}

.main-header h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
}

.main-header p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
    font-size: 1.1rem;
}

.upload-section {
    background: rgba(78, 84, 200, 0.05);
    padding: 1.5rem;
    border-radius: 12px;
    border: 2px dashed rgba(78, 84, 200, 0.3);
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.upload-section:hover {
    border-color: var(--primary-color);
    background: rgba(78, 84, 200, 0.08);
}

.stats-container {
    background: linear-gradient(45deg, #f8f9fa, #e9ecef);
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
}

.alert-box {
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    font-weight: 500;
    animation: slideInUp 0.4s ease-out;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.success-box { 
    background: var(--success-color); 
    color: white;
    border-left: 4px solid rgba(255,255,255,0.3);
}

.error-box { 
    background: var(--error-color); 
    color: white;
    border-left: 4px solid rgba(255,255,255,0.3);
}

.warning-box { 
    background: var(--warning-color); 
    color: #000;
    border-left: 4px solid rgba(0,0,0,0.2);
}

.info-box { 
    background: var(--info-color); 
    color: white;
    border-left: 4px solid rgba(255,255,255,0.3);
}

.text-preview {
    background: rgba(248, 249, 250, 0.8);
    border: 1px solid #dee2e6;
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
    overflow-y: auto;
    max-height: 300px;
    white-space: pre-wrap;
    line-height: 1.4;
}

.candidate-card {
    border: 1px solid #e9ecef;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
}

.candidate-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

.candidate-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(78, 84, 200, 0.1);
}

.action-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
    justify-content: center;
}

.btn-primary {
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.btn-secondary {
    background: #6c757d;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}

@keyframes slideInUp {
    from { 
        opacity: 0; 
        transform: translateY(20px); 
    }
    to { 
        opacity: 1; 
        transform: translateY(0); 
    }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.processing {
    animation: pulse 1.5s infinite;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .main-header h1 { font-size: 2rem; }
    .main-header p { font-size: 1rem; }
    .candidate-header { flex-direction: column; text-align: center; }
    .action-buttons { flex-direction: column; }
}
</style>
""", unsafe_allow_html=True)

# ────── Header ──────
st.markdown("""
<div class="main-header">
    <h1>💼 HireScope AI</h1>
    <p>Advanced AI-Powered Résumé Management System</p>
</div>
""", unsafe_allow_html=True)

# ────── Sidebar Info ──────
with st.sidebar:
    st.markdown("### 📊 Session Statistics")
    if "stats" not in st.session_state:
        st.session_state.stats = {"processed": 0, "errors": 0, "total_uploaded": 0}
    
    st.metric("✅ Successfully Processed", st.session_state.stats["processed"])
    st.metric("❌ Errors", st.session_state.stats["errors"])
    st.metric("📁 Total Uploaded", st.session_state.stats["total_uploaded"])
    
    if st.session_state.stats["processed"] > 0:
        success_rate = (st.session_state.stats["processed"] / st.session_state.stats["total_uploaded"]) * 100
        st.metric("📈 Success Rate", f"{success_rate:.1f}%")
    
    st.markdown("---")
    st.markdown("### 🔧 System Info")
    st.info("✨ Powered by GPT-4o\n🔍 ChromaDB Vector Store\n📄 Multi-format PDF Support")

# ────── State Management ──────
if "results" not in st.session_state:
    st.session_state.results = []

# ────── Main Upload Section ──────
st.markdown('<div class="upload-section">', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    hr_name = st.text_input(
        "👤 HR Representative Name", 
        placeholder="Enter your full name (e.g., Jane Smith)",
        help="This will be recorded as the uploader in the system"
    )

with col2:
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    if st.button("🔄 Reset Stats", help="Clear all session statistics"):
        st.session_state.stats = {"processed": 0, "errors": 0, "total_uploaded": 0}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

files = st.file_uploader(
    "📂 Upload Candidate Résumés", 
    type="pdf", 
    accept_multiple_files=True,
    help="Select multiple PDF files (max 15 files, 10MB each)"
)

st.markdown('</div>', unsafe_allow_html=True)

# ────── Validation ──────
if not hr_name:
    st.markdown('<div class="alert-box warning-box">⚠️ Please enter your name to proceed with uploads.</div>', unsafe_allow_html=True)
    st.stop()

if files and len(files) > 15:
    st.markdown('<div class="alert-box error-box">❌ Maximum 15 files allowed per upload session.</div>', unsafe_allow_html=True)
    st.stop()

# ────── Enhanced Extraction Pipeline ──────
def extract_all_text(pdf_bytes: bytes) -> str:
    """Enhanced multi-method PDF text extraction with fallbacks"""
    extractors = [
        # Method 1: PyMuPDF (fastest, best for most PDFs)
        lambda: "\n".join(page.get_text() for page in fitz.open(stream=pdf_bytes, filetype="pdf")),
        
        # Method 2: PDFMiner (good for complex layouts)
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        
        # Method 3: PDFPlumber (excellent for tables)
        lambda: "\n".join(page.extract_text() or "" for page in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
        
        # Method 4: PyPDF2 (backup method)
        lambda: "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages),
        
        # Method 5: OCR (last resort for scanned PDFs)
        lambda: "\n".join(pytesseract.image_to_string(img, config='--psm 6') for img in convert_from_bytes(pdf_bytes, dpi=300, first_page=1, last_page=3))
    ]
    
    for i, extractor in enumerate(extractors):
        try:
            result = extractor().strip()
            if result and len(result) > 50:  # Minimum content threshold
                return result
        except Exception as e:
            continue
    
    return ""

# ────── Enhanced Name Extraction ──────
def extract_candidate_name(summary: str, fallback_filename: str) -> str:
    """Enhanced candidate name extraction with multiple fallback strategies"""
    try:
        # Try JSON parsing first
        data = json.loads(summary)
        if isinstance(data, dict) and "name" in data and data["name"].strip():
            return data["name"].strip()
    except:
        pass

    # Regex patterns for name extraction
    name_patterns = [
        r"(?i)^name[:\-]?\s*(.+)$",
        r"(?i)^full name[:\-]?\s*(.+)$",
        r"(?i)candidate[:\-]?\s*(.+)$",
        r"(?i)applicant[:\-]?\s*(.+)$"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, summary, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 50:
                return name

    # Look for name-like patterns in first few lines
    lines = summary.split('\n')[:5]
    for line in lines:
        line = line.strip("•-* \t")
        # Match typical name patterns
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', line) and len(line.split()) <= 4:
            return line

    # Fallback to filename
    return re.sub(r'[_\-]', ' ', fallback_filename).rsplit('.', 1)[0]

# ────── Process Uploaded Files ──────
if files:
    st.markdown("### 🔄 Processing Résumés")
    
    progress_bar = st.progress(0)
    status_container = st.container()
    
    for idx, file in enumerate(files):
        with status_container:
            processing_msg = st.empty()
            processing_msg.markdown(f'<div class="alert-box info-box processing">🔄 Processing {file.name}...</div>', unsafe_allow_html=True)
            
        try:
            # File validation
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise Exception("File size exceeds 10MB limit")
            
            pdf_bytes = file.getvalue()
            
            # Extract text
            raw_text = extract_all_text(pdf_bytes)
            if not raw_text or len(raw_text.strip()) < 100:
                raise Exception("Insufficient or unreadable content")

            # AI Summary
            with st.spinner("🤖 Generating AI summary..."):
                summary = summarize_resume(raw_text)

            # Extract candidate info
            candidate_name = extract_candidate_name(summary, file.name)
            candidate_id = make_candidate_id(candidate_name)

            # Check for existing candidates
            existing = collection.get(where={"name": candidate_name})
            if existing["ids"]:
                with processing_msg.container():
                    overwrite = st.checkbox(
                        f"🔄 Candidate '{candidate_name}' exists. Overwrite?", 
                        key=f"overwrite_{candidate_id}_{idx}",
                        help="This will replace the existing résumé data"
                    )
                    
                if not overwrite:
                    processing_msg.markdown(f'<div class="alert-box warning-box">⏭️ Skipped {candidate_name} (already exists)</div>', unsafe_allow_html=True)
                    continue
                
                collection.delete(where={"name": candidate_name})

            # Store in ChromaDB
            collection.add(
                documents=[summary],
                metadatas=[{
                    "candidate_id": candidate_id, 
                    "name": candidate_name, 
                    "uploaded_by": hr_name,
                    "filename": file.name,
                    "upload_timestamp": str(st.session_state.get('timestamp', 'unknown'))
                }],
                ids=[candidate_id]
            )
            
            # Persist if available
            if hasattr(chroma_client, "persist"):
                chroma_client.persist()

            # Store results
            st.session_state.results.append({
                "name": candidate_name,
                "candidate_id": candidate_id,
                "filename": file.name,
                "raw_text": raw_text[:1500],  # Store more text for preview
                "summary": summary[:1500],
                "status": "success"
            })
            
            # Update stats
            st.session_state.stats["processed"] += 1
            st.session_state.stats["total_uploaded"] = st.session_state.stats.get("total_uploaded", 0) + 1

            processing_msg.markdown(f'''
                <div class="alert-box success-box">
                    ✅ Successfully processed <strong>{candidate_name}</strong><br>
                    📋 ID: <code>{candidate_id}</code> | 📄 File: {file.name}
                </div>
            ''', unsafe_allow_html=True)

        except Exception as e:
            st.session_state.stats["errors"] += 1
            st.session_state.stats["total_uploaded"] = st.session_state.stats.get("total_uploaded", 0) + 1
            
            processing_msg.markdown(f'''
                <div class="alert-box error-box">
                    ❌ Failed to process <strong>{file.name}</strong><br>
                    🔍 Error: {str(e)}
                </div>
            ''', unsafe_allow_html=True)

        # Update progress
        progress_bar.progress((idx + 1) / len(files))

    progress_bar.empty()

# ────── Results Display ──────
if st.session_state.results:
    st.markdown("---")
    st.markdown("### 📋 Processed Candidates")
    
    # Filter and search
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search candidates", placeholder="Enter name or keyword...")
    with col2:
        show_raw = st.checkbox("📄 Show raw text", help="Display extracted raw text alongside summaries")
    
    # Filter results
    filtered_results = st.session_state.results
    if search_term:
        filtered_results = [r for r in st.session_state.results 
                          if search_term.lower() in r["name"].lower() or 
                             search_term.lower() in r["summary"].lower()]
    
    st.markdown(f"**Showing {len(filtered_results)} of {len(st.session_state.results)} candidates**")
    
    # Display results
    for result in filtered_results:
        st.markdown(f'''
            <div class="candidate-card">
                <div class="candidate-header">
                    <h3>👤 {result["name"]}</h3>
                    <span style="background: rgba(78, 84, 200, 0.1); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem;">
                        📁 {result["filename"]}
                    </span>
                </div>
        ''', unsafe_allow_html=True)
        
        if show_raw:
            tab1, tab2 = st.tabs(["📊 AI Summary", "📄 Raw Text"])
            with tab1:
                st.markdown(f'<div class="text-preview">{result["summary"]}</div>', unsafe_allow_html=True)
            with tab2:
                st.markdown(f'<div class="text-preview">{result["raw_text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("**🤖 AI-Generated Summary:**")
            st.markdown(f'<div class="text-preview">{result["summary"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Action buttons
    st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Upload More Résumés", help="Clear current results and upload new files"):
            st.rerun()
    
    with col2:
        if st.button("💾 Export Results", help="Download processing results as JSON"):
            results_json = json.dumps(st.session_state.results, indent=2)
            st.download_button(
                "📥 Download JSON",
                results_json,
                f"hirescope_results_{len(st.session_state.results)}_candidates.json",
                "application/json"
            )
    
    with col3:
        if st.button("🗑️ Clear All Results", help="Remove all processed results from this session"):
            st.session_state.results.clear()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ────── Footer ──────
st.markdown("---")
st.markdown("""
<div style="text-align: center; opacity: 0.7; padding: 1rem;">
    <p>💼 <strong>HireScope AI</strong> - Powered by Advanced AI Technology<br>
    🔒 Secure • 🚀 Fast • 🎯 Accurate</p>
</div>
""", unsafe_allow_html=True)
