import streamlit as st
import json
from utils import collection, chroma_client

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Matching function
def matches(meta, doc):
    return (
        (name_filter.lower() in meta.get('name', '').lower() if name_filter else True) and
        (id_filter.lower() in meta.get('candidate_id', '').lower() if id_filter else True) and
        (by_hr.lower() in meta.get('uploaded_by', '').lower() if by_hr else True) and
        (keywords.lower() in doc.lower() if keywords else True)
    )

# Display cards
st.markdown("---")
st.subheader("Candidate List")
num_cols = 2
cols = st.columns(num_cols)

for idx, (meta, doc) in enumerate(zip(metas, docs)):
    if not matches(meta, doc):
        continue

    col = cols[idx % num_cols]
    with col:
        with st.container(border=True):
            st.markdown(f"### 👤 {meta.get('name', 'Unknown')}")
            st.caption(f"Uploaded by: **{meta.get('uploaded_by', 'N/A')}**")
            st.caption(f"📅 Uploaded: {meta.get('upload_timestamp', 'N/A')}")

            # Extract contacts from JSON summary if possible
            try:
                summary_json = json.loads(doc)
                email = summary_json.get("email")
                phone = summary_json.get("phone")
                linkedin = summary_json.get("linkedin")
            except:
                email = phone = linkedin = None

            if email:
                st.markdown(f"📧 Email: [{email}](mailto:{email})")
            if phone:
                st.markdown(f"📞 Phone: `{phone}`")
            if linkedin:
                st.markdown(f"🔗 [LinkedIn Profile]({linkedin})")

            # View Summary
            if st.button("📄 View Summary", key=f"view_{idx}"):
                with st.expander(f"Summary for {meta.get('name', 'Unknown')}", expanded=True):
                    st.markdown("""
                    <div style='max-height: 400px; overflow-y: auto; padding: 1rem; background-color: #0e1117; border: 1px solid #444; border-radius: 8px;'>
                    """, unsafe_allow_html=True)
                    try:
                        st.json(summary_json)
                    except:
                        st.text_area("Summary", doc, height=300, disabled=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            # Delete logic
            if st.button("🗑️ Delete", key=f"delete_{idx}"):
                with st.expander(f"Confirm delete {meta.get('name', 'Unknown')}?"):
                    confirm, cancel = st.columns([1, 1])
                    with confirm:
                        if st.button("✅ Confirm", key=f"confirm_{idx}"):
                            collection.delete(ids=[meta['candidate_id']])
                            if hasattr(chroma_client, "persist"):
                                chroma_client.persist()
                            st.success(f"Deleted {meta.get('name', 'Unknown')}.")
                            st.rerun()
                    with cancel:
                        st.button("❌ Cancel", key=f"cancel_{idx}")