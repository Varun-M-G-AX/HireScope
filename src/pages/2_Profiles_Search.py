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

# --- Modern theme-adaptive CSS ---
st.markdown("""
<style>
.stApp { background: var(--background-color); }
.candidate-card {
    background: var(--background-color);
    border: 1.5px solid var(--secondary-background-color);
    border-radius: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    padding: 1.7rem 1.25rem 1.05rem 1.25rem;
    margin-bottom: 1.35rem;
    transition: box-shadow .25s, border-color .18s;
    position: relative;
}
.candidate-card:hover {
    box-shadow: 0 8px 32px rgba(102,126,234,0.20);
    border-color: #667eea;
}
.avatar-circle {
    width: 58px; height: 58px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff; font-weight: 700; font-size: 1.45rem;
    display: flex; align-items: center; justify-content: center;
    border: 2.5px solid var(--background-color);
    margin-bottom: 0.3rem;
}
.candidate-name { font-size: 1.2rem; font-weight: 700; color: var(--text-color); }
.candidate-id { font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 0.22rem;}
.candidate-meta { font-size: 0.85rem; color: var(--text-secondary);}
.card-divider { border: none; border-top: 1px solid var(--secondary-background-color); margin: 0.7rem 0 0.6rem 0;}
.card-actions { display: flex; gap: 0.9rem; margin-top: 0.65rem;}
.card-actions button { flex: 1; }
.contact-item { font-size: 0.95rem; color: var(--text-color);}
@media (max-width: 800px) {
    .candidate-card { padding: 0.9rem 1rem; }
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("# 📇 Candidate Profiles")
st.markdown("*Browse and manage all résumés processed by HireScope AI*")

# --- Data ---
try:
    all_data = collection.get()
    metas = all_data.get("metadatas", [])
    docs = all_data.get("documents", [])
    all_ids = all_data.get("ids", [])
except Exception as e:
    st.error(f"🚨 Failed to load candidate data: {e}")
    st.stop()

# --- Filter Sidebar ---
with st.sidebar:
    st.markdown("## 🔍 Filter Candidates")
    if st.button("🔄 Reset All Filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    name_filter = st.text_input("👤 Name", value="")
    id_filter = st.text_input("🆔 Candidate ID", value="")
    by_hr = st.text_input("👨‍💼 Uploaded By", value="")
    keywords = st.text_input("🔍 Keywords", value="")
    with st.expander("🎯 Advanced Filters"):
        has_email = st.checkbox("Has Email", value=False)
        has_phone = st.checkbox("Has Phone", value=False)
        has_linkedin = st.checkbox("Has LinkedIn", value=False)

def matches(meta, doc, summary):
    doc_str = str(doc).lower() if doc else ""
    meta_str = str(meta).lower() if meta else ""
    if name_filter and name_filter.strip():
        if name_filter.lower() not in meta.get('name','').lower():
            return False
    if id_filter and id_filter.strip():
        if id_filter.lower() not in meta.get('candidate_id','').lower():
            return False
    if by_hr and by_hr.strip():
        if by_hr.lower() not in meta.get('uploaded_by','').lower():
            return False
    if keywords and keywords.strip():
        if keywords.lower() not in doc_str:
            return False
    if has_email:
        if summary and summary.get("email"):
            pass
        elif "email" in doc_str or '@' in doc_str:
            pass
        else:
            return False
    if has_phone:
        if summary and summary.get("phone"):
            pass
        elif "phone" in doc_str or "mobile" in doc_str:
            pass
        else:
            return False
    if has_linkedin:
        if summary and summary.get("linkedin"):
            pass
        elif "linkedin" in doc_str or "linkedin.com" in doc_str or "/in/" in doc_str:
            pass
        else:
            return False
    return True

# --- Filter candidates and pair with Chroma IDs ---
filtered_candidates = []
for i, (meta, doc) in enumerate(zip(metas, docs)):
    summary = None
    try:
        summary = json.loads(doc) if isinstance(doc, str) and doc.strip().startswith("{") else None
    except Exception:
        summary = None
    if matches(meta, doc, summary):
        filtered_candidates.append({"meta": meta, "doc": doc, "id": all_ids[i] if i < len(all_ids) else meta.get("candidate_id", f"idx_{i}"), "summary": summary})

# --- Display Empty States ---
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

# --- Responsive grid ---
cols = st.columns(2)

for idx, candidate in enumerate(filtered_candidates):
    meta, doc, chroma_id, summary = candidate["meta"], candidate["doc"], candidate["id"], candidate["summary"]
    name = meta.get('name', 'Unknown')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    candidate_id = meta.get('candidate_id', '')
    avatar_url = meta.get('avatar_url')
    initials = "".join([w[0] for w in name.split() if w and w[0].isalpha()]).upper()[:2] or "👤"

    # Parse date
    display_date = upload_date
    if upload_date and upload_date != "N/A":
        parsed_date = None
        for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                parsed_date = datetime.strptime(str(upload_date), fmt)
                break
            except: continue
        if parsed_date:
            display_date = parsed_date.strftime("%b %d, %Y")
    else:
        display_date = "Unknown"

    # Contact info
    email = summary.get("email") if summary else None
    phone = summary.get("phone") if summary else None
    linkedin = summary.get("linkedin") if summary else None

    col = cols[idx % len(cols)]
    with col:
        st.markdown('<div class="candidate-card">', unsafe_allow_html=True)
        avatar_html = f'<img src="{avatar_url}" width="58"/>' if avatar_url else f'<div class="avatar-circle">{initials}</div>'
        st.markdown(avatar_html, unsafe_allow_html=True)
        st.markdown(f'<div class="candidate-name">{name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="candidate-id">ID: <code>{candidate_id}</code></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="candidate-meta">Uploaded by: {uploaded_by} &nbsp;|&nbsp; Date: {display_date}</div>', unsafe_allow_html=True)
        st.markdown('<hr class="card-divider"/>', unsafe_allow_html=True)
        # Contact
        if email or phone or linkedin:
            st.markdown("**Contact:**")
            if email: st.markdown(f'<div class="contact-item">📧 <a href="mailto:{email}">{email}</a></div>', unsafe_allow_html=True)
            if phone: st.markdown(f'<div class="contact-item">📞 {phone}</div>', unsafe_allow_html=True)
            if linkedin: st.markdown(f'<div class="contact-item">🔗 <a href="{linkedin}" target="_blank">LinkedIn</a></div>', unsafe_allow_html=True)
        # Actions
        st.markdown('<div class="card-actions">', unsafe_allow_html=True)
        view_summary = st.button("📄 View Summary", key=f"view_{idx}")
        delete_candidate = st.button("🗑️ Delete", key=f"delete_{idx}", type="secondary")
        st.markdown('</div>', unsafe_allow_html=True)
        # View modal
        if view_summary:
            st.markdown(f"""
            <div class="summary-modal">
                <h4 style="color: var(--text-color); margin-bottom: 1rem;">📄 Candidate Summary</h4>
                <div class="summary-content">{json.dumps(summary, indent=2, ensure_ascii=False) if summary else doc}</div>
            </div>
            """, unsafe_allow_html=True)
        # Delete
        if delete_candidate:
            st.warning(f"⚠️ Delete **{name}**? This action cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Confirm Delete", key=f"confirm_{idx}"):
                    try:
                        collection.delete(ids=[str(chroma_id)])
                        try: collection.persist()
                        except: pass
                        st.success("✅ Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to delete: {e}")
            with c2:
                if st.button("❌ Cancel", key=f"cancel_{idx}"):
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.88rem; padding: 1rem 0;">
    HireScope Candidate Management • Built with ❤️ using Streamlit
</div>
""", unsafe_allow_html=True)