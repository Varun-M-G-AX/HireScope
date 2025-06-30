import streamlit as st
import json
from datetime import datetime
from utils import collection, chroma_client

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for modern UI
st.markdown("""
<style>
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* CSS Variables for theme support */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --text-tertiary: #9ca3af;
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --bg-tertiary: #f3f4f6;
    --border-color: #e5e7eb;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    :root {
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --text-tertiary: #9ca3af;
        --bg-primary: #111827;
        --bg-secondary: #1f2937;
        --bg-tertiary: #374151;
        --border-color: #374151;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
}

/* Global styles */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background-color: var(--bg-primary);
}

/* Hide Streamlit branding */
.stDeployButton {
    display: none !important;
}

/* Typography */
h1 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

h2, h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* Enhanced candidate card styling for Streamlit containers */
div[data-testid="stContainer"] {
    background: var(--bg-primary);
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.25rem !important;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

div[data-testid="stContainer"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--primary-color) !important;
}

div[data-testid="stContainer"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
}

/* Better spacing for card content */
div[data-testid="stContainer"] > div {
    margin-bottom: 0.75rem !important;
}

div[data-testid="stContainer"] > div:last-child {
    margin-bottom: 0 !important;
}

/* Avatar styling - updated for compact layout */
.avatar-circle {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 600;
    border: 2px solid var(--bg-primary);
    box-shadow: var(--shadow-sm);
    margin: 0;
}

/* Streamlit image styling within containers - compact version */
div[data-testid="stContainer"] img {
    border-radius: 50%;
    border: 2px solid var(--bg-primary);
    box-shadow: var(--shadow-sm);
    object-fit: cover;
}

/* Typography improvements for card content */
div[data-testid="stContainer"] h1, 
div[data-testid="stContainer"] h2, 
div[data-testid="stContainer"] h3,
div[data-testid="stContainer"] h4 {
    color: var(--text-primary) !important;
    margin-bottom: 0.5rem !important;
    margin-top: 0 !important;
}

div[data-testid="stContainer"] h3 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
}

div[data-testid="stContainer"] p {
    color: var(--text-secondary) !important;
    margin-bottom: 0.25rem !important;
    font-size: 0.9rem !important;
    line-height: 1.4 !important;
}

/* Code styling for candidate ID */
div[data-testid="stContainer"] code {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    padding: 0.2rem 0.4rem !important;
    border-radius: 4px !important;
    font-size: 0.85rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Divider styling within cards */
div[data-testid="stContainer"] hr {
    border: none !important;
    border-top: 1px solid var(--border-color) !important;
    margin: 0.75rem 0 !important;
    opacity: 0.7 !important;
}

/* Contact links styling */
div[data-testid="stContainer"] a {
    color: var(--primary-color) !important;
    text-decoration: none !important;
    font-weight: 500 !important;
}

div[data-testid="stContainer"] a:hover {
    text-decoration: underline !important;
    color: var(--secondary-color) !important;
}

/* Button styling - keeping for reference but using Streamlit native styling above */
.btn-primary {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background: var(--bg-tertiary);
    transform: translateY(-1px);
}

.btn-danger {
    background: var(--danger-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-danger:hover {
    background: #dc2626;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

/* Streamlit button styling within bordered containers */
div[data-testid="stContainer"] .stButton > button {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.625rem 1rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    margin-bottom: 0 !important;
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stContainer"] .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    background: linear-gradient(135deg, #5a67d8, #6b46c1) !important;
}

div[data-testid="stContainer"] .stButton > button[kind="secondary"] {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
}

div[data-testid="stContainer"] .stButton > button[kind="secondary"]:hover {
    background: var(--danger-color) !important;
    color: white !important;
    border-color: var(--danger-color) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
}

/* Remove button container margins and improve spacing */
div[data-testid="stContainer"] .stButton {
    margin-bottom: 0 !important;
}

div[data-testid="stContainer"] .element-container {
    margin-bottom: 0.4rem !important;
}

/* Improve spacing between button columns */
div[data-testid="stContainer"] .stColumns {
    gap: 0.75rem !important;
}

div[data-testid="stContainer"] .stColumns > div {
    padding-left: 0.375rem !important;
    padding-right: 0.375rem !important;
}

/* Summary modal */
.summary-modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-top: 1rem;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: var(--shadow-md);
}

.summary-content {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--text-secondary);
    white-space: pre-wrap;
    background: var(--bg-primary);
    padding: 1rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
}

/* Filter section */
.filter-section {
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
}

/* Stats cards */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
}

.stat-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-weight: 500;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    border: 2px dashed var(--border-color);
    margin: 2rem 0;
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.empty-state-text {
    color: var(--text-secondary);
    font-size: 1rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .candidate-card {
        padding: 1rem;
    }
    
    .action-buttons {
        flex-direction: column;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    h1 {
        font-size: 2rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📇 Candidate Profiles")
st.markdown("*Browse and manage all résumés processed by HireScope AI*")

# Fetching data
try:
    res = collection.get(include=["metadatas", "documents"])
    metas, docs = res["metadatas"], res["documents"]
except Exception as e:
    st.error(f"🚨 Failed to load candidate data: {e}")
    metas, docs = [], []

# Stats section
if metas:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(metas)}</div>
            <div class="stat-label">Total Candidates</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        uploaders = set(meta.get('uploaded_by', 'Unknown') for meta in metas)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(uploaders)}</div>
            <div class="stat-label">HR Users</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Count profiles with contact info
        with_contact = sum(1 for meta, doc in zip(metas, docs) 
                          if any(field in doc.lower() for field in ['email', 'phone', 'linkedin']))
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{with_contact}</div>
            <div class="stat-label">With Contact Info</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Recent uploads (last 7 days - simplified)
        recent = len([m for m in metas if 'upload_timestamp' in m])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{recent}</div>
            <div class="stat-label">Recent Uploads</div>
        </div>
        """, unsafe_allow_html=True)

# Sidebar filters
with st.sidebar:
    st.markdown("## 🔍 Filter Candidates")
    
    name_filter = st.text_input("👤 Candidate Name", placeholder="Enter name...")
    id_filter = st.text_input("🆔 Candidate ID", placeholder="Enter ID...")
    by_hr = st.text_input("👨‍💼 Uploaded By", placeholder="HR user...")
    keywords = st.text_input("🔍 Keywords", placeholder="Skills, keywords...")
    
    # Advanced filters
    with st.expander("🎯 Advanced Filters"):
        has_email = st.checkbox("Has Email")
        has_phone = st.checkbox("Has Phone")
        has_linkedin = st.checkbox("Has LinkedIn")
    
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.rerun()

def matches(meta, doc):
    basic_match = (
        (name_filter.lower() in meta.get('name', '').lower() if name_filter else True) and
        (id_filter.lower() in meta.get('candidate_id', '').lower() if id_filter else True) and
        (by_hr.lower() in meta.get('uploaded_by', '').lower() if by_hr else True) and
        (keywords.lower() in doc.lower() if keywords else True)
    )
    
    if not basic_match:
        return False
    
    # Advanced filters
    if has_email and 'email' not in doc.lower():
        return False
    if has_phone and 'phone' not in doc.lower():
        return False
    if has_linkedin and 'linkedin' not in doc.lower():
        return False
    
    return True

# Filter and display candidates
filtered_candidates = [(meta, doc) for meta, doc in zip(metas, docs) if matches(meta, doc)]

if not metas:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📂</div>
        <div class="empty-state-title">No Candidates Found</div>
        <div class="empty-state-text">
            Start by uploading some résumés using the 'Upload Résumés' page.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not filtered_candidates:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-title">No Matches Found</div>
        <div class="empty-state-text">
            Try adjusting your search criteria or clearing the filters.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Display results
st.markdown(f"## 📋 Results ({len(filtered_candidates)} candidates)")

# Grid layout for candidates
cols = st.columns(2)

for idx, (meta, doc) in enumerate(filtered_candidates):
    name = meta.get('name', 'Unknown')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    candidate_id = meta.get('candidate_id', '')

    # Avatar logic
    avatar_url = meta.get('avatar_url')
    initials = "".join([w[0] for w in name.split() if w and w[0].isalpha()]).upper()[:2] or "👤"

    # Parse contact info
    email = phone = linkedin = None
    summary_json = None
    try:
        summary_json = json.loads(doc)
        email = summary_json.get("email")
        phone = summary_json.get("phone")
        linkedin = summary_json.get("linkedin")
    except Exception:
        summary_json = None

    col = cols[idx % len(cols)]
    with col:
        # Create enhanced candidate card with professional layout
        with st.container(border=True):
            # Format upload date properly
            display_date = "Date not available"
            if upload_date and upload_date != "N/A":
                try:
                    # Try to parse different date formats
                    if isinstance(upload_date, str):
                        # Handle common date formats
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M"]:
                            try:
                                parsed_date = datetime.strptime(upload_date, fmt)
                                display_date = parsed_date.strftime("%B %d, %Y")
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format matches, use the original string
                            display_date = upload_date
                    else:
                        # If it's already a datetime object
                        display_date = upload_date.strftime("%B %d, %Y")
                except:
                    # Fallback to original value if parsing fails
                    display_date = str(upload_date)
            
            # Main card header with avatar and name
            avatar_col, info_col = st.columns([1, 5])
            
            with avatar_col:
                if avatar_url:
                    st.image(avatar_url, width=56)
                else:
                    st.markdown(f"""
                    <div class="avatar-circle" style="width: 56px; height: 56px; font-size: 1.2rem;">{initials}</div>
                    """, unsafe_allow_html=True)
            
            with info_col:
                st.markdown(f"### {name}")
                st.markdown(f"**ID:** `{candidate_id}`")
                st.markdown(f"**Uploaded by:** {uploaded_by} • {display_date}")
            
            # Compact contact information in a clean layout
            if email or phone or linkedin:
                st.markdown("---")
                
                # Contact info in horizontal layout
                contact_items = []
                if email:
                    contact_items.append(f"📧 [{email}](mailto:{email})")
                if phone:
                    contact_items.append(f"📞 {phone}")
                if linkedin:
                    contact_items.append(f"🔗 [LinkedIn]({linkedin})")
                
                # Display contact info in a single row or wrap naturally
                st.markdown(" • ".join(contact_items))
            
            # Clean action buttons at the bottom
            st.markdown("---")
            action_col1, action_col2 = st.columns([1, 1])
            with action_col1:
                view_summary = st.button("📄 View Summary", key=f"view_{idx}", use_container_width=True)
            with action_col2:
                delete_candidate = st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True, type="secondary")

            # Summary modal
            if view_summary:
                if summary_json:
                    summary_str = json.dumps(summary_json, indent=2, ensure_ascii=False)
                else:
                    summary_str = doc
                
                st.markdown(f"""
                <div class="summary-modal">
                    <h4 style="color: var(--text-primary); margin-bottom: 1rem;">📄 Candidate Summary</h4>
                    <div class="summary-content">{summary_str}</div>
                </div>
                """, unsafe_allow_html=True)

            # Delete confirmation
            if delete_candidate:
                st.warning(f"⚠️ Delete **{name}**? This action cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Confirm Delete", key=f"confirm_{idx}", type="primary"):
                        try:
                            collection.delete(ids=[candidate_id])
                            if hasattr(chroma_client, "persist"):
                                chroma_client.persist()
                            st.success(f"✅ Successfully deleted {name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting candidate: {e}")
                with c2:
                    if st.button("❌ Cancel", key=f"cancel_{idx}"):
                        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.875rem; padding: 1rem 0;">
    HireScope Candidate Management • Built with ❤️ using Streamlit
</div>
""", unsafe_allow_html=True)