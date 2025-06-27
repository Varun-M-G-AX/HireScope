import io, re, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

st.set_page_config(page_title="Résumé Upload", page_icon="📂", layout="wide")

# Minimal CSS for clean animations
st.markdown("""
<style>
.upload-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1.5rem;
}

.processing-item {
    background: #f8f9fa;
    border-left: 4px solid #ffc107;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 5px;
    animation: slideIn 0.3s ease-out;
}

.success-item {
    background: #f8f9fa;
    border-left: 4px solid #28a745;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 5px;
    animation: slideIn 0.3s ease-out;
}

.error-item {
    background: #f8f9fa;
    border-left: 4px solid #dc3545;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 5px;
    animation: slideIn 0.3s ease-out;
}

.candidate-card {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
}

.candidate-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.stat-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.text-preview {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 0.75rem;
    font-family: monospace;
    font-size: 0.85rem;
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #667eea, #764ba2);
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="upload-header">
    <h1>📂 HR Résumé Uploader</h1>
    <p>Upload multiple PDFs and process them efficiently</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
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
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <h3>{st.session_state.stats['processed']}</h3>
            <small>Processed</small>
        </div>
        <div class="stat-card">
            <h3>{st.session_state.stats['errors']}</h3>
            <small>Errors</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

if not hr_name:
    st.warning("Please enter your name first")
    st.stop()

if files and len(files) > 10:
    st.error("Maximum 10 files allowed")
    st.stop()

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
        except:
            continue
    
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

# Processing
if files:
    st.session_state.stats['total'] = len(files)
    
    # Progress section
    progress_bar = st.progress(0)
    status_container = st.container()
    
    processed_set = set()
    
    for idx, pdf in enumerate(files):
        # Update progress
        progress = idx / len(files)
        progress_bar.progress(progress)
        
        # Show current processing
        with status_container:
            st.markdown(f"""
            <div class="processing-item">
                <strong>🔄 Processing:</strong> {pdf.name}
            </div>
            """, unsafe_allow_html=True)
        
        try:
            raw_text = extract_all_text(pdf.getvalue())
            
            if not raw_text.strip():
                raise Exception("No text extracted")
            
            # Generate summary
            with st.spinner("Generating summary..."):
                summary = summarize_resume(raw_text)
            
            name = extract_candidate_name(summary, pdf.name)
            cid = make_candidate_id(name)
            
            if cid in processed_set:
                continue
            
            processed_set.add(cid)
            
            # Check for existing
            existing = collection.get(where={"name": name})["ids"]
            if existing:
                if not st.checkbox(f"Overwrite existing {name}?", key=f"ow_{idx}"):
                    st.info(f"Skipped {name}")
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
            
            # Add to results
            st.session_state.results.append({
                'name': name,
                'cid': cid,
                'filename': pdf.name,
                'raw': raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
                'summary': summary[:300] + "..." if len(summary) > 300 else summary
            })
            
            st.session_state.stats['processed'] += 1
            
            # Show success
            status_container.markdown(f"""
            <div class="success-item">
                <strong>✅ Completed:</strong> {name} ({pdf.name})
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.session_state.stats['errors'] += 1
            status_container.markdown(f"""
            <div class="error-item">
                <strong>❌ Error:</strong> {pdf.name} - {str(e)[:100]}
            </div>
            """, unsafe_allow_html=True)
    
    # Final progress
    progress_bar.progress(1.0)
    status_container.success(f"Processing complete! {st.session_state.stats['processed']} successful, {st.session_state.stats['errors']} errors")

# Results section
if st.session_state.results:
    st.markdown("## 📋 Processed Résumés")
    
    for result in st.session_state.results:
        with st.expander(f"👤 {result['name']} - {result['filename']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Raw Text Preview:**")
                st.markdown(f'<div class="text-preview">{result["raw"]}</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Summary:**")
                st.markdown(f'<div class="text-preview">{result["summary"]}</div>', unsafe_allow_html=True)

# Actions
if st.session_state.results:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process More Files"):
            # Keep results but allow new uploads
            pass
    with col2:
        if st.button("🗑️ Clear All Results"):
            st.session_state.results = []
            st.session_state.stats = {'processed': 0, 'errors': 0, 'total': 0}
            st.rerun()