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
    padding: 1.5rem !important;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

div[data-testid="stContainer"]:hover {
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    transform: translateY(-4px);
    border-color: var(--primary-color) !important;
}

div[data-testid="stContainer"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
}

/* Better spacing for card content */
div[data-testid="stContainer"] > div {
    margin-bottom: 1rem !important;
}

div[data-testid="stContainer"] > div:last-child {
    margin-bottom: 0 !important;
}

/* Avatar styling - updated for better layout */
.avatar-circle {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 600;
    border: 3px solid var(--bg-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    margin: 0;
}

/* Streamlit image styling within containers */
div[data-testid="stContainer"] img {
    border-radius: 50%;
    border: 3px solid var(--bg-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
    # Get all data without specifying include parameters first
    all_data = collection.get()
    metas = all_data.get("metadatas", [])
    docs = all_data.get("documents", [])
    all_ids = all_data.get("ids", [])
    
    # Debug info
    st.sidebar.write(f"Debug: Found {len(metas)} candidates, {len(all_ids)} IDs")
    if metas:
        st.sidebar.write(f"Sample metadata keys: {list(metas[0].keys()) if metas[0] else 'None'}")
        st.sidebar.write(f"Sample upload timestamp: {metas[0].get('upload_timestamp', 'None') if metas else 'None'}")
    
except Exception as e:
    st.error(f"🚨 Failed to load candidate data: {e}")
    metas, docs, all_ids = [], [], []

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
        # Recent uploads - count profiles uploaded in the last 7 days
        from datetime import datetime, timedelta
        recent_count = 0
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for meta in metas:
            upload_date = meta.get('upload_timestamp')
            if upload_date:
                try:
                    parsed_date = None
                    if isinstance(upload_date, str):
                        # Try different date formats
                        date_formats = [
                            "%Y-%m-%d %H:%M:%S.%f",  # With microseconds
                            "%Y-%m-%d %H:%M:%S", 
                            "%Y-%m-%d", 
                            "%d/%m/%Y %H:%M:%S",
                            "%d/%m/%Y", 
                            "%m/%d/%Y %H:%M:%S",
                            "%m/%d/%Y",
                            "%Y-%m-%d %H:%M",
                            "%d-%m-%Y %H:%M:%S",
                            "%d-%m-%Y"
                        ]
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(upload_date, fmt)
                                break
                            except ValueError:
                                continue
                    elif hasattr(upload_date, 'year'):  # datetime object
                        parsed_date = upload_date
                    
                    if parsed_date and parsed_date >= cutoff_date:
                        recent_count += 1
                        
                except Exception as e:
                    # For debugging - remove this in production
                    # st.sidebar.write(f"Date parse error for {upload_date}: {e}")
                    continue
        
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{recent_count}</div>
            <div class="stat-label">Recent Uploads (7 days)</div>
        </div>
        """, unsafe_allow_html=True)

# Sidebar filters
with st.sidebar:
    st.markdown("## 🔍 Filter Candidates")
    
    # Reset button at the top
    if st.button("🔄 Reset All Filters", use_container_width=True):
        # Clear all filter session state
        st.session_state.clear()
        st.rerun()
    
    # Use session state to persist filter values
    if 'filters_reset' not in st.session_state:
        st.session_state.filters_reset = False
    
    name_filter = st.text_input("👤 Candidate Name", placeholder="Enter name...", value="")
    id_filter = st.text_input("🆔 Candidate ID", placeholder="Enter ID...", value="")
    by_hr = st.text_input("👨‍💼 Uploaded By", placeholder="HR user...", value="")
    keywords = st.text_input("🔍 Keywords", placeholder="Skills, keywords...", value="")
    
    # Advanced filters
    with st.expander("🎯 Advanced Filters"):
        has_email = st.checkbox("Has Email", value=False)
        has_phone = st.checkbox("Has Phone", value=False)
        has_linkedin = st.checkbox("Has LinkedIn", value=False)
    
    # Show current filter values for debugging
    if name_filter or id_filter or by_hr or keywords or has_email or has_phone or has_linkedin:
        st.write("🔍 Active Filters:")
        if name_filter: st.write(f"Name: {name_filter}")
        if id_filter: st.write(f"ID: {id_filter}")
        if by_hr: st.write(f"HR: {by_hr}")
        if keywords: st.write(f"Keywords: {keywords}")
        if has_email: st.write("Has Email: ✓")
        if has_phone: st.write("Has Phone: ✓")
        if has_linkedin: st.write("Has LinkedIn: ✓")

def matches(meta, doc):
    # Debug what we're working with
    doc_str = str(doc).lower() if doc else ""
    
    # Basic text filters - be more explicit
    if name_filter and name_filter.strip():
        if name_filter.lower() not in meta.get('name', '').lower():
            return False
    
    if id_filter and id_filter.strip():
        if id_filter.lower() not in meta.get('candidate_id', '').lower():
            return False
    
    if by_hr and by_hr.strip():
        if by_hr.lower() not in meta.get('uploaded_by', '').lower():
            return False
    
    if keywords and keywords.strip():
        if keywords.lower() not in doc_str:
            return False
    
    # Advanced filters - more thorough checking
    if has_email:
        email_found = (
            'email' in doc_str or 
            '@' in doc_str or
            any(str(v).lower().find('email') != -1 for v in meta.values() if v) or
            any('@' in str(v) for v in meta.values() if v)
        )
        if not email_found:
            return False
    
    if has_phone:
        import re
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
            r'\b\d{10}\b',  # 10 digits
            r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # International
        ]
        phone_found = (
            'phone' in doc_str or 
            'mobile' in doc_str or
            'tel' in doc_str or
            any(re.search(pattern, doc_str) for pattern in phone_patterns) or
            any('phone' in str(v).lower() for v in meta.values() if v)
        )
        if not phone_found:
            return False
    
    if has_linkedin:
        linkedin_found = (
            'linkedin' in doc_str or 
            'linkedin.com' in doc_str or
            '/in/' in doc_str or
            any('linkedin' in str(v).lower() for v in meta.values() if v)
        )
        if not linkedin_found:
            return False
    
    return True

# Filter and display candidates
filtered_candidates = []
candidate_ids = []  # Keep track of IDs for deletion

if metas and docs:
    for i, (meta, doc) in enumerate(zip(metas, docs)):
        if matches(meta, doc):
            filtered_candidates.append((meta, doc, i))  # Include original index
            # Try to get the actual ID from the collection
            try:
                candidate_ids.append(all_ids[i] if i < len(all_ids) else meta.get('candidate_id', f'idx_{i}'))
            except:
                candidate_ids.append(meta.get('candidate_id', f'idx_{i}'))

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

for idx, (meta, doc, original_idx) in enumerate(filtered_candidates):
    name = meta.get('name', 'Unknown')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    candidate_id = meta.get('candidate_id', '')
    
    # Get the actual ID for deletion
    actual_id = candidate_ids[idx] if idx < len(candidate_ids) else candidate_id

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
                                display_date = parsed_date.strftime("%B %d, %Y at %I:%M %p")
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format matches, use the original string
                            display_date = upload_date
                    else:
                        # If it's already a datetime object
                        display_date = upload_date.strftime("%B %d, %Y at %I:%M %p")
                except:
                    # Fallback to original value if parsing fails
                    display_date = str(upload_date)
            else:
                # Use current date and time as fallback
                current_time = datetime.now()
                display_date = current_time.strftime("%B %d, %Y at %I:%M %p")
                # Only show warning if needed - you can uncomment this line for debugging
                # st.caption("⚠️ Using current time as upload timestamp was not available")
            
            # Main card header with avatar and name
            avatar_col, info_col = st.columns([1, 4])
            
            with avatar_col:
                if avatar_url:
                    st.image(avatar_url, width=64)
                else:
                    st.markdown(f"""
                    <div class="avatar-circle" style="width: 64px; height: 64px; font-size: 1.5rem;">{initials}</div>
                    """, unsafe_allow_html=True)
            
            with info_col:
                st.markdown(f"### {name}")
                st.markdown(f"**ID:** `{candidate_id}`")
                st.markdown(f"**Uploaded by:** {uploaded_by}")
                st.markdown(f"**Date:** {display_date}")
            
            # Compact contact information in a clean layout
            if email or phone or linkedin:
                st.markdown("---")
                st.markdown("**Contact Information:**")
                
                # Contact info in clean layout
                contact_items = []
                if email:
                    contact_items.append(f"📧 [{email}](mailto:{email})")
                if phone:
                    contact_items.append(f"📞 {phone}")
                if linkedin:
                    contact_items.append(f"🔗 [LinkedIn]({linkedin})")
                
                # Display contact info
                for item in contact_items:
                    st.markdown(f"- {item}")
            
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
                            success = False
                            error_messages = []
                            
                            # Method 1: Delete by ChromaDB ID
                            if actual_id and len(actual_id) > 0:
                                try:
                                    collection.delete(ids=[str(actual_id)])
                                    success = True
                                    st.write(f"✅ Deleted using ChromaDB ID: {actual_id}")
                                except Exception as e1:
                                    error_messages.append(f"ChromaDB ID method: {str(e1)}")
                            
                            # Method 2: Delete by candidate_id
                            if not success and candidate_id:
                                try:
                                    collection.delete(ids=[str(candidate_id)])
                                    success = True
                                    st.write(f"✅ Deleted using candidate ID: {candidate_id}")
                                except Exception as e2:
                                    error_messages.append(f"Candidate ID method: {str(e2)}")
                            
                            # Method 3: Delete by metadata where clause
                            if not success and candidate_id:
                                try:
                                    collection.delete(where={"candidate_id": {"$eq": candidate_id}})
                                    success = True
                                    st.write(f"✅ Deleted using metadata where clause")
                                except Exception as e3:
                                    error_messages.append(f"Metadata where method: {str(e3)}")
                            
                            # Method 4: Delete by name (dangerous but last resort)
                            if not success and name != "Unknown":
                                try:
                                    collection.delete(where={"name": {"$eq": name}})
                                    success = True
                                    st.write(f"✅ Deleted using name: {name}")
                                except Exception as e4:
                                    error_messages.append(f"Name method: {str(e4)}")
                            
                            if success:
                                # Try to persist
                                try:
                                    collection.persist()
                                except:
                                    try:
                                        chroma_client.persist()
                                    except:
                                        pass
                                
                                st.success(f"✅ Successfully deleted {name}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete candidate")
                                with st.expander("🔍 Error Details"):
                                    for i, msg in enumerate(error_messages, 1):
                                        st.write(f"Method {i}: {msg}")
                                    st.write(f"Actual ID: {actual_id}")
                                    st.write(f"Candidate ID: {candidate_id}")
                                    st.write(f"Name: {name}")
                                        
                        except Exception as e:
                            st.error(f"❌ Unexpected error: {str(e)}")
                            st.write("Full error details:", e)
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