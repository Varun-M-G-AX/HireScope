import streamlit as st
import json
from utils import collection, chroma_client

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for card and summary scroll area
st.markdown("""
    <style>
    .candidate-card {
        background: #23272f;
        color: #f0f6fc;
        border-radius: 18px;
        box-shadow: 0 2px 12px #0003;
        padding: 1.5rem;
        margin-bottom: 30px;
        min-width: 320px;
        max-width: 470px;
        display: flex;
        flex-direction: column;
        gap: 0.7rem;
    }
    .candidate-header {
        display: flex;
        gap: 1.1rem;
        align-items: flex-start;
        margin-bottom: 0.4rem;
    }
    .candidate-avatar {
        width: 54px;
        height: 54px;
        border-radius: 50%;
        background: #363b45;
        color: #7ed6df;
        font-size: 2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .candidate-title {
        font-weight: 700;
        font-size: 1.13rem;
        margin-bottom: 2px;
    }
    .candidate-meta {
        font-size: 0.98rem;
        color: #a1a7bb;
        margin-bottom: 2px;
    }
    .candidate-contact {
        font-size: 1rem;
        margin-top: 0.3rem;
        margin-bottom: 0.3rem;
        line-height: 1.6;
    }
    .candidate-actions {
        display: flex;
        gap: 12px;
        margin-top: 1rem;
        margin-bottom: 0;
        justify-content: flex-start;
        width: 100%;
    }
    .summary-scroll {
        max-height: 260px;
        overflow-y: auto;
        background: #181c25;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .stButton button, .stButton > button {
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 20px !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        background: #3346d3 !important;
        color: #fff !important;
        transition: background 0.18s;
        margin-right: 2px;
    }
    .stButton button:hover, .stButton > button:hover {
        background: #23336c !important;
        color: #fff !important;
    }
    .stButton.delete-btn button {
        background: #e84118 !important;
    }
    .stButton.delete-btn button:hover {
        background: #c23616 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📇 Stored Candidate Résumés")
st.markdown("Browse and manage all résumés processed by HireScope AI.")

# Fetching data
try:
    res = collection.get(include=["metadatas", "documents"])
    metas, docs = res["metadatas"], res["documents"]
except Exception as e:
    st.error(f"🚨 Failed to load candidate data: {e}")
    metas, docs = [], []

if not metas:
    st.info("No résumés found. Please upload some using the 'Upload Résumés' page.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Candidates")
name_filter = st.sidebar.text_input("Candidate Name")
id_filter = st.sidebar.text_input("Candidate ID")
by_hr = st.sidebar.text_input("Uploaded By")
keywords = st.sidebar.text_input("Keywords in Summary")

def matches(meta, doc):
    return (
        (name_filter.lower() in meta.get('name', '').lower() if name_filter else True) and
        (id_filter.lower() in meta.get('candidate_id', '').lower() if id_filter else True) and
        (by_hr.lower() in meta.get('uploaded_by', '').lower() if by_hr else True) and
        (keywords.lower() in doc.lower() if keywords else True)
    )

st.markdown("---")
st.subheader("Candidate List")

cols = st.columns(2)

for idx, (meta, doc) in enumerate(zip(metas, docs)):
    if not matches(meta, doc):
        continue

    name = meta.get('name', 'Unknown')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    candidate_id = meta.get('candidate_id', '')
    initials = "".join([w[0] for w in name.split() if w and w[0].isalpha()]).upper()[:2] if name and name != "Unknown" else "👤"

    email = phone = linkedin = None
    summary_json = None
    try:
        summary_json = json.loads(doc)
        email = summary_json.get("email")
        phone = summary_json.get("phone")
        linkedin = summary_json.get("linkedin")
    except Exception:
        summary_json = None

    col = cols[idx % 2]
    with col:
        with st.container(border=False):
            st.markdown('<div class="candidate-card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="candidate-header">
                    <span class="candidate-avatar">{initials}</span>
                    <div>
                        <div class="candidate-title">{name}</div>
                        <div class="candidate-meta">ID: {candidate_id}</div>
                        <div class="candidate-meta">Uploaded by <b>{uploaded_by}</b> · {upload_date}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True,
            )
            st.markdown('<div class="candidate-contact">', unsafe_allow_html=True)
            if email:
                st.markdown(f'📧 <a href="mailto:{email}">{email}</a>', unsafe_allow_html=True)
            if phone:
                st.markdown(f'<br>📞 <span style="color:#e1b12c;">{phone}</span>', unsafe_allow_html=True)
            if linkedin:
                st.markdown(f'<br>🔗 <a href="{linkedin}" target="_blank" style="color:#0097e6;">LinkedIn</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Actions and summary - all INSIDE the card
            bcol1, bcol2 = st.columns([1, 1])
            with bcol1:
                view_summary = st.button("📄 View Summary", key=f"view_{idx}")
            with bcol2:
                delete_candidate = st.button("🗑️ Delete", key=f"delete_{idx}")

            if view_summary:
                with st.expander(f"Summary for {name}", expanded=True):
                    st.markdown('<div class="summary-scroll">', unsafe_allow_html=True)
                    if summary_json:
                        st.json(summary_json)
                    else:
                        st.text_area("Summary", doc, height=220, disabled=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            if delete_candidate:
                with st.expander(f"Confirm delete {name}?", expanded=True):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        if st.button("✅ Confirm", key=f"confirm_{idx}"):
                            collection.delete(ids=[meta['candidate_id']])
                            if hasattr(chroma_client, "persist"):
                                chroma_client.persist()
                            st.success(f"Deleted {name}.")
                            st.rerun()
                    with c2:
                        st.button("❌ Cancel", key=f"cancel_{idx}")

            st.markdown('</div>', unsafe_allow_html=True)