import streamlit as st
import json
from datetime import datetime, timedelta
from utils import collection, chroma_client

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simplified CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

.candidate-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

.candidate-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateY(-2px);
}

.avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 1rem;
}

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: #667eea;
}

.stat-label {
    font-size: 0.9rem;
    color: #6b7280;
}

.stButton > button {
    width: 100%;
    border-radius: 6px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Header
st.title("📇 Candidate Profiles")
st.caption("Browse and manage all résumés processed by HireScope AI")

# Load data
@st.cache_data(ttl=60)
def load_data():
    try:
        data = collection.get()
        return data.get("metadatas", []), data.get("documents", []), data.get("ids", [])
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return [], [], []

metas, docs, all_ids = load_data()

# Stats
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
        uploaders = len(set(meta.get('uploaded_by', 'Unknown') for meta in metas))
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{uploaders}</div>
            <div class="stat-label">HR Users</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        with_contact = sum(1 for doc in docs if any(term in str(doc).lower() for term in ['@', 'phone', 'linkedin']))
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{with_contact}</div>
            <div class="stat-label">With Contact</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Recent uploads (last 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        recent = 0
        for meta in metas:
            date_str = meta.get('upload_timestamp', '')
            if date_str:
                try:
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            if date_obj >= cutoff:
                                recent += 1
                            break
                        except:
                            continue
                except:
                    pass
        
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{recent}</div>
            <div class="stat-label">Recent (7d)</div>
        </div>
        """, unsafe_allow_html=True)

# Filters
with st.sidebar:
    st.subheader("🔍 Filters")
    
    if st.button("🔄 Clear All", use_container_width=True):
        st.rerun()
    
    name_filter = st.text_input("Name", placeholder="Search by name...")
    keywords_filter = st.text_input("Keywords", placeholder="Skills, experience...")
    
    with st.expander("Advanced"):
        has_email = st.checkbox("Has Email")
        has_phone = st.checkbox("Has Phone") 
        has_linkedin = st.checkbox("Has LinkedIn")

# Filter function
def filter_candidates(meta, doc):
    doc_str = str(doc).lower()
    
    # Name filter
    if name_filter and name_filter.lower() not in meta.get('name', '').lower():
        return False
    
    # Keywords filter
    if keywords_filter and keywords_filter.lower() not in doc_str:
        return False
    
    # Contact filters
    if has_email and '@' not in doc_str:
        return False
    if has_phone and not any(term in doc_str for term in ['phone', 'mobile', 'tel']):
        return False
    if has_linkedin and 'linkedin' not in doc_str:
        return False
    
    return True

# Apply filters
filtered_data = []
for i, (meta, doc) in enumerate(zip(metas, docs)):
    if filter_candidates(meta, doc):
        filtered_data.append((meta, doc, all_ids[i] if i < len(all_ids) else f'id_{i}'))

# Display results
if not metas:
    st.info("No candidates found. Upload some résumés to get started.")
    st.stop()

if not filtered_data:
    st.warning("No matches found. Try adjusting your filters.")
    st.stop()

st.subheader(f"📋 Results ({len(filtered_data)} candidates)")

# Cards layout
for idx, (meta, doc, doc_id) in enumerate(filtered_data):
    name = meta.get('name', 'Unknown')
    candidate_id = meta.get('candidate_id', 'N/A')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    
    # Parse contact info
    try:
        doc_json = json.loads(doc)
        email = doc_json.get('email', 'N/A')
        phone = doc_json.get('phone', 'N/A')
        linkedin = doc_json.get('linkedin', 'N/A')
    except:
        email = phone = linkedin = 'N/A'
    
    # Avatar
    initials = ''.join([word[0] for word in name.split() if word])[:2].upper() or '??'
    
    with st.container():
        st.markdown(f"""
        <div class="candidate-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div class="avatar">{initials}</div>
                <div style="margin-left: 1rem;">
                    <h3 style="margin: 0; color: #1f2937;">{name}</h3>
                    <p style="margin: 0; color: #6b7280;">ID: {candidate_id}</p>
                    <p style="margin: 0; color: #6b7280;">By: {uploaded_by} • {upload_date}</p>
                </div>
            </div>
            
            <div style="margin-bottom: 1rem;">
                <strong>Contact:</strong><br>
                📧 {email}<br>
                📞 {phone}<br>
                🔗 {linkedin}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 View Summary", key=f"view_{idx}"):
                with st.expander("Summary", expanded=True):
                    st.text(doc)
        
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{idx}", type="secondary"):
                if st.button(f"⚠️ Confirm Delete {name}?", key=f"confirm_{idx}", type="primary"):
                    try:
                        # Try deletion methods
                        success = False
                        
                        # Method 1: By ID
                        try:
                            collection.delete(ids=[str(doc_id)])
                            success = True
                        except:
                            pass
                        
                        # Method 2: By candidate_id
                        if not success and candidate_id != 'N/A':
                            try:
                                collection.delete(where={"candidate_id": candidate_id})
                                success = True
                            except:
                                pass
                        
                        if success:
                            st.success(f"Deleted {name}")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
                    except Exception as e:
                        st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("*HireScope Candidate Management*")