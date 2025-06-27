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

cols = st.columns(2)

for idx, (meta, doc) in enumerate(zip(metas, docs)):
    if not matches(meta, doc):
        continue

    name = meta.get('name', 'Unknown')
    uploaded_by = meta.get('uploaded_by', 'N/A')
    upload_date = meta.get('upload_timestamp', 'N/A')
    candidate_id = meta.get('candidate_id', '')

    # Avatar logic: use avatar_url if present, else initials
    avatar_url = meta.get('avatar_url')
    initials = "".join([w[0] for w in name.split() if w and w[0].isalpha()]).upper()[:2] or "👤"

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
            avatar_col, info_col = st.columns([1, 5])
            with avatar_col:
                if avatar_url:
                    st.image(avatar_url, width=56)
                else:
                    # Render colored circle with initials using st.write and markdown
                    st.markdown(
                        f'<div style="width:56px;height:56px;border-radius:50%;background:#5a5e6b;color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.7rem;border:2px solid #3b3e47;">{initials}</div>',
                        unsafe_allow_html=True
                    )
            with info_col:
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
            bcol1, bcol2 = st.columns([1, 1])
            with bcol1:
                view_summary = st.button("📄 View Summary", key=f"view_{idx}")
            with bcol2:
                delete_candidate = st.button("🗑️ Delete", key=f"delete_{idx}")

            # Summary modal - fixed height, scrollable box inside the card
            if view_summary:
                st.markdown("**Summary**")
                # The st.json widget will always expand, so instead, use st.code in a scrollable st.container
                if summary_json:
                    summary_str = json.dumps(summary_json, indent=2, ensure_ascii=False)
                else:
                    summary_str = doc
                # Scrollable code/text area
                st.markdown(
                    f"<div style='max-height:300px;overflow:auto;background:#1e222d;padding:10px;border-radius:7px;border:1px solid #444;'>"
                    f"<pre style='font-size: 0.93rem; color: #eee;'>{summary_str}</pre></div>",
                    unsafe_allow_html=True
                )

            # Delete confirmation
            if delete_candidate:
                st.warning(f"Delete {name}? This cannot be undone.")
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