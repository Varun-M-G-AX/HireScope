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

def matches(meta, doc):
    return (
        (name_filter.lower() in meta.get('name', '').lower() if name_filter else True) and
        (id_filter.lower() in meta.get('candidate_id', '').lower() if id_filter else True) and
        (by_hr.lower() in meta.get('uploaded_by', '').lower() if by_hr else True) and
        (keywords.lower() in doc.lower() if keywords else True)
    )

st.markdown("---")
st.subheader("Candidate List")

# Change 2 to 3 for 3-column grid
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

    col = cols[idx % len(cols)]
    with col:
        with st.container(border=True):
            # Header
            st.markdown(f"**{name}**")
            st.caption(f"ID: {candidate_id}")
            st.caption(f"Uploaded by: **{uploaded_by}** · {upload_date}")

            # Contact info
            if email:
                st.markdown(f'📧 [{email}](mailto:{email})')
            if phone:
                st.markdown(f'📞 {phone}')
            if linkedin:
                st.markdown(f'🔗 [LinkedIn]({linkedin})')

            # Buttons row
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                view_summary = st.button("📄 View Summary", key=f"view_{idx}")
            with bcol2:
                delete_candidate = st.button("🗑️ Delete", key=f"delete_{idx}")

            # Summary modal
            if view_summary:
                with st.expander(f"Summary for {name}", expanded=True):
                    st.write("")  # space
                    if summary_json:
                        # Use a fixed height box for JSON
                        st.json(summary_json, expanded=False)
                    else:
                        st.text_area("Summary", value=doc, height=220, disabled=True)

            # Delete confirmation
            if delete_candidate:
                with st.expander(f"Confirm delete {name}?", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Confirm", key=f"confirm_{idx}"):
                            collection.delete(ids=[meta['candidate_id']])
                            if hasattr(chroma_client, "persist"):
                                chroma_client.persist()
                            st.success(f"Deleted {name}.")
                            st.rerun()
                    with c2:
                        st.button("❌ Cancel", key=f"cancel_{idx}")