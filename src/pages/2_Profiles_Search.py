import streamlit as st
import json
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

/* Enhanced candidate card */
.candidate-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.candidate-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--primary-color);
}

.candidate-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
}

/* Avatar styling */
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
    box-shadow: var(--shadow-md);
    margin-bottom: 1rem;
}

.candidate-name {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.candidate-id {
    font-size: 0.875rem;
    color: var(--text-tertiary);
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg-tertiary);
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    display: inline-block;
    margin-bottom: 0.5rem;
}

.candidate-meta {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
}

/* Contact info styling */
.contact-info {
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    padding: 1rem;
    margin: 1rem 0;
    border: 1px solid var(--border-color);
}

.contact-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.contact-item:last-child {
    margin-bottom: 0;
}

.contact-icon {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
}

/* Button styling */
.action-buttons {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.5rem;
}

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
    box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
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
    box-shadow: var(--shadow-sm);
}

.btn-danger:hover {
    background: #dc2626;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
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
        # Create enhanced candidate card
        with st.container():
            st.markdown(f"""
            <div class="candidate-card">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div>
                        {f'<img src="{avatar_url}" style="width: 64px; height: 64px; border-radius: 50%; object-fit: cover; border: 3px solid var(--bg-primary); box-shadow: var(--shadow-md);">' if avatar_url else f'<div class="avatar-circle">{initials}</div>'}
                    </div>
                    <div style="flex: 1;">
                        <div class="candidate-name">{name}</div>
                        <div class="candidate-id">ID: {candidate_id}</div>
                        <div class="candidate-meta">
                            👨‍💼 Uploaded by <strong>{uploaded_by}</strong><br>
                            📅 {upload_date}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Contact information
            if email or phone or linkedin:
                contact_items = []
                if email:
                    contact_items.append(f'<div class="contact-item">📧 <a href="mailto:{email}" style="color: var(--primary-color); text-decoration: none;">{email}</a></div>')
                if phone:
                    contact_items.append(f'<div class="contact-item">📞 {phone}</div>')
                if linkedin:
                    contact_items.append(f'<div class="contact-item">🔗 <a href="{linkedin}" target="_blank" style="color: var(--primary-color); text-decoration: none;">LinkedIn</a></div>')
                
                st.markdown(f"""
                <div class="contact-info">
                    {''.join(contact_items)}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Action buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                view_summary = st.button("📄 View Summary", key=f"view_{idx}", use_container_width=True)
            with col2:
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