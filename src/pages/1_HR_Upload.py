import io, re, json, streamlit as st, fitz, pdfplumber, PyPDF2
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
from utils import summarize_resume, make_candidate_id, chroma_client, collection

# ────── Page Configuration ──────
st.set_page_config(
    page_title="Resume AI", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ────── Clean Gemini-inspired CSS ──────
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@300;400;500;600&display=swap');

/* CSS Variables for theme switching */
:root {
    --primary-blue: #1a73e8;
    --primary-blue-hover: #1557b0;
    --background: #ffffff;
    --surface: #f8f9fa;
    --surface-variant: #e3f2fd;
    --on-surface: #202124;
    --on-surface-variant: #5f6368;
    --border: #dadce0;
    --success: #137333;
    --error: #d93025;
    --warning: #f9ab00;
}

/* Dark theme */
[data-theme="dark"] {
    --background: #0d1117;
    --surface: #161b22;
    --surface-variant: #21262d;
    --on-surface: #f0f6fc;
    --on-surface-variant: #8b949e;
    --border: #30363d;
    --success: #2ea043;
    --error: #f85149;
    --warning: #d29922;
}

/* Auto detect system theme */
@media (prefers-color-scheme: dark) {
    :root {
        --background: #0d1117;
        --surface: #161b22;
        --surface-variant: #21262d;
        --on-surface: #f0f6fc;
        --on-surface-variant: #8b949e;
        --border: #30363d;
        --success: #2ea043;
        --error: #f85149;
        --warning: #d29922;
    }
}

/* Base styles */
.stApp {
    font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--background);
    color: var(--on-surface);
}

/* Header */
.header {
    text-align: center;
    padding: 2rem 0;
    margin-bottom: 2rem;
}

.header h1 {
    font-weight: 400;
    font-size: 2.75rem;
    color: var(--on-surface);
    margin: 0;
    background: linear-gradient(135deg, var(--primary-blue) 0%, #4285f4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header p {
    color: var(--on-surface-variant);
    font-size: 1.1rem;
    margin: 0.5rem 0 0 0;
    font-weight: 300;
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

.card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Upload area */
.upload-area {
    border: 2px dashed var(--border);
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    background: var(--surface-variant);
    transition: all 0.2s ease;
}

.upload-area:hover {
    border-color: var(--primary-blue);
    background: var(--surface);
}

/* Status messages */
.status {
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    font-weight: 400;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-success {
    background: rgba(19, 115, 51, 0.1);
    border: 1px solid var(--success);
    color: var(--success);
}

.status-error {
    background: rgba(217, 48, 37, 0.1);
    border: 1px solid var(--error);
    color: var(--error);
}

.status-warning {
    background: rgba(249, 171, 0, 0.1);
    border: 1px solid var(--warning);
    color: var(--warning);
}

/* Buttons */
.btn {
    background: var(--primary-blue);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: inherit;
}

.btn:hover {
    background: var(--primary-blue-hover);
}

.btn-secondary {
    background: var(--surface);
    color: var(--on-surface);
    border: 1px solid var(--border);
}

.btn-secondary:hover {
    background: var(--surface-variant);
}

/* Text preview */
.text-preview {
    background: var(--surface-variant);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'SF Mono', monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    color: var(--on-surface-variant);
}

/* Stats */
.stats {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin: 1rem 0;
}

.stat {
    text-align: center;
    padding: 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    min-width: 100px;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--primary-blue);
}

.stat-label {
    font-size: 0.875rem;
    color: var(--on-surface-variant);
    margin-top: 0.25rem;
}

/* Responsive */
@media (max-width: 768px) {
    .header h1 { font-size: 2rem; }
    .stats { flex-direction: column; }
    .card { padding: 1rem; }
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

</style>
""", unsafe_allow_html=True)

# ────── Initialize State ──────
if "results" not in st.session_state:
    st.session_state.results = []
if "stats" not in st.session_state:
    st.session_state.stats = {"processed": 0, "errors": 0}

# ────── Header ──────
st.markdown("""
<div class="header">
    <h1>🤖 Resume AI</h1>
    <p>Upload and analyze resumes with AI-powered insights</p>
</div>
""", unsafe_allow_html=True)

# ────── Stats Display ──────
st.markdown(f"""
<div class="stats">
    <div class="stat">
        <div class="stat-value">{st.session_state.stats['processed']}</div>
        <div class="stat-label">Processed</div>
    </div>
    <div class="stat">
        <div class="stat-value">{st.session_state.stats['errors']}</div>
        <div class="stat-label">Errors</div>
    </div>
    <div class="stat">
        <div class="stat-value">{len(st.session_state.results)}</div>
        <div class="stat-label">Results</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ────── Upload Section ──────
st.markdown('<div class="card">', unsafe_allow_html=True)

hr_name = st.text_input(
    "Your Name", 
    placeholder="Enter your name",
    help="This will be recorded with uploaded resumes"
)

if not hr_name:
    st.markdown('<div class="status status-warning">⚠️ Please enter your name to continue</div>', unsafe_allow_html=True)
    st.stop()

st.markdown('<div class="upload-area">', unsafe_allow_html=True)
files = st.file_uploader(
    "Choose PDF files", 
    type="pdf", 
    accept_multiple_files=True,
    help="Select up to 10 PDF resume files"
)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if files and len(files) > 10:
    st.markdown('<div class="status status-error">❌ Maximum 10 files allowed</div>', unsafe_allow_html=True)
    st.stop()

# ────── Text Extraction ──────
def extract_text(pdf_bytes: bytes) -> str:
    extractors = [
        lambda: "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf")),
        lambda: extract_text(io.BytesIO(pdf_bytes)),
        lambda: "\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(pdf_bytes)).pages),
    ]
    
    for extractor in extractors:
        try:
            result = extractor().strip()
            if result:
                return result
        except:
            continue
    return ""

def get_candidate_name(summary: str, filename: str) -> str:
    try:
        data = json.loads(summary)
        if "name" in data:
            return data["name"].strip()
    except:
        pass
    
    # Simple name extraction from filename
    return re.sub(r'[_\-]', ' ', filename).rsplit('.', 1)[0]

# ────── Process Files ──────
if files:
    progress = st.progress(0)
    
    for idx, file in enumerate(files):
        st.markdown(f'<div class="status">🔄 Processing {file.name}...</div>', unsafe_allow_html=True)
        
        try:
            pdf_bytes = file.getvalue()
            raw_text = extract_text(pdf_bytes)
            
            if not raw_text:
                raise Exception("Could not extract text")
            
            with st.spinner("Analyzing with AI..."):
                summary = summarize_resume(raw_text)
            
            name = get_candidate_name(summary, file.name)
            candidate_id = make_candidate_id(name)
            
            # Check existing
            existing = collection.get(where={"name": name})
            if existing["ids"]:
                if not st.checkbox(f"Overwrite {name}?", key=f"overwrite_{idx}"):
                    st.markdown(f'<div class="status status-warning">⏭️ Skipped {name}</div>', unsafe_allow_html=True)
                    continue
                collection.delete(where={"name": name})
            
            # Store in database
            collection.add(
                documents=[summary],
                metadatas=[{"candidate_id": candidate_id, "name": name, "uploaded_by": hr_name}],
                ids=[candidate_id]
            )
            
            if hasattr(chroma_client, "persist"):
                chroma_client.persist()
            
            st.session_state.results.append({
                "name": name,
                "id": candidate_id,
                "filename": file.name,
                "summary": summary
            })
            
            st.session_state.stats["processed"] += 1
            st.markdown(f'<div class="status status-success">✅ Processed {name}</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.session_state.stats["errors"] += 1
            st.markdown(f'<div class="status status-error">❌ Error with {file.name}: {str(e)}</div>', unsafe_allow_html=True)
        
        progress.progress((idx + 1) / len(files))
    
    progress.empty()

# ────── Results ──────
if st.session_state.results:
    st.markdown("## Results")
    
    for result in st.session_state.results:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### 👤 {result['name']}")
        st.markdown(f"**File:** {result['filename']}")
        
        with st.expander("View Summary"):
            st.markdown(f'<div class="text-preview">{result["summary"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process More", type="primary"):
            st.rerun()
    with col2:
        if st.button("🗑️ Clear Results"):
            st.session_state.results.clear()
            st.session_state.stats = {"processed": 0, "errors": 0}
            st.rerun()