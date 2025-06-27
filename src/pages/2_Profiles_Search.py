import streamlit as st
import json
from utils import collection, chroma_client

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for nice cards
st.markdown("""
    <style>
    .card-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 32px;
        justify-content: flex-start;
    }
    .candidate-card {
        background: #181c25;
        color: #f0f6fc;
        box-shadow: 0 4px 32px #0002;
        border-radius: 18px;
        padding: 1.8rem 1.5rem 1.5rem 1.5rem;
        min-width: 320px;
        max-width: 400px;
        flex: 1 1 340px;
        transition: box-shadow 0.2s, transform 0.2s;
        position: relative;
        border: 1px solid #23272f;
    }
    .candidate-card:hover {
        box-shadow: 0 6px 40px #0004;
        transform: translateY(-2px) scale(1.03);
        border-color: #4b7bec;
    }
    .candidate-avatar {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #23272f;
        color: #7ed6df;
        font-size: 2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
        margin-right: 12px;
        float: left;
    }
    .candidate-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .candidate-actions {
        margin-top: 1.2rem;
        display: flex;
        gap: 8px;
    }
    .candidate-contact {
        margin: 0.2rem 0 0.2rem 0;
        font-size: 1rem;
    }
    .candidate-meta {
        font-size: 0.98rem;
        color: #7f8fa6;
    }
    .delete-expander > div {
        background: #23272f !important;
        border-radius: 9px !important;
        border: 1px solid #4b7bec !important;
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

# Render cards in a custom HTML grid for best effect
st.markdown('<div class="card-grid">', unsafe_allow_html=True)

for idx, (meta, doc) in enumerate(zip(metas, docs)):
    if not matches(meta, doc):
        continue

    # Prepare card info
    name = meta.get('name', 'Unknown')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    candidate_id = meta.get('candidate_id', '')
    initials = "".join([w[0] for w in name.split() if w]).upper()[:2] if name and name != "Unknown" else "👤"

    # Contact info
    email = phone = linkedin = None
    summary_json = None
    try:
        summary_json = json.loads(doc)
        email = summary_json.get("email")
        phone = summary_json.get("phone")
        linkedin = summary_json.get("linkedin")
    except:
        pass

    # Render card as HTML for style
    card_html = f"""
    <div class="candidate-card">
        <div class="candidate-header">
            <div class="candidate-avatar">{initials}</div>
            <div>
                <div style="font-size:1.22rem;font-weight:700;margin-bottom:2px;">{name}</div>
                <div class="candidate-meta">ID: <b>{candidate_id}</b></div>
                <div class="candidate-meta">Uploaded by <b>{uploaded_by}</b> · <span>{upload_date}</span></div>
            </div>
        </div>
        <div class="candidate-contact">
            {'📧 <a href="mailto:{}">{}</a>'.format(email, email) if email else ''}
            {'<br>📞 <span style="color:#e1b12c;">{}</span>'.format(phone) if phone else ''}
            {'<br>🔗 <a href="{}" target="_blank" style="color:#0097e6;">LinkedIn</a>'.format(linkedin) if linkedin else ''}
        </div>
        <div class="candidate-actions">
            <form action="" method="post">
                <button class="stButton" name="view_{idx}" style="background:#4b7bec;color:white;border:none;padding:7px 18px;border-radius:7px;cursor:pointer;" type="submit">📄 View Summary</button>
                <button class="stButton" name="delete_{idx}" style="background:#e84118;color:white;border:none;padding:7px 18px;border-radius:7px;cursor:pointer;" type="submit">🗑️ Delete</button>
            </form>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Streamlit controls for each card (separate from HTML, for actual logic)
    # Use unique keys to keep buttons independent
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📄 View Summary", key=f"view_{idx}"):
            with st.expander(f"Summary for {name}", expanded=True):
                st.markdown(
                    "<div style='max-height: 400px; overflow-y: auto; padding: 1rem; background-color: #181c25; border: 1px solid #4b7bec; border-radius: 9px;'>",
                    unsafe_allow_html=True)
                if summary_json:
                    st.json(summary_json)
                else:
                    st.text_area("Summary", doc, height=300, disabled=True)
                st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        if st.button("🗑️ Delete", key=f"delete_{idx}"):
            with st.expander(f"Confirm delete {name}?", expanded=True, class_="delete-expander"):
                confirm, cancel = st.columns([1, 1])
                with confirm:
                    if st.button("✅ Confirm", key=f"confirm_{idx}"):
                        collection.delete(ids=[meta['candidate_id']])
                        if hasattr(chroma_client, "persist"):
                            chroma_client.persist()
                        st.success(f"Deleted {name}.")
                        st.rerun()
                with cancel:
                    st.button("❌ Cancel", key=f"cancel_{idx}")

st.markdown('</div>', unsafe_allow_html=True)