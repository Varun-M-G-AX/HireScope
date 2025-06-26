import streamlit as st
from utils import collection, chroma_client

st.set_page_config(page_title="Candidate Profiles", page_icon="📇")
st.title("📇 Stored Candidate Résumés")

res = collection.get(include=["metadatas", "documents"])
metas, docs = res["metadatas"], res["documents"]

if not metas:
    st.info("No résumés in the database yet.")
    st.stop()

# ───────── Filter options ─────────
st.sidebar.header("🔍 Filter Candidates")
name_filter = st.sidebar.text_input("By Name")
id_filter   = st.sidebar.text_input("By Candidate ID")
by_hr       = st.sidebar.text_input("By Uploaded By")
keywords    = st.sidebar.text_input("Contains (any keyword)")

def matches(meta, doc):
    return (
        (name_filter.lower() in meta['name'].lower() if name_filter else True) and
        (id_filter.lower() in meta['candidate_id'].lower() if id_filter else True) and
        (by_hr.lower() in meta.get('uploaded_by', '').lower() if by_hr else True) and
        (keywords.lower() in doc.lower() if keywords else True)
    )

# ───────── Display results ─────────
matches_found = 0
for i, (meta, doc) in enumerate(zip(metas, docs)):
    if not matches(meta, doc): continue
    matches_found += 1

    with st.container(border=True):
        st.markdown(f"### 👤 {meta.get('name', 'Unknown')}")
        st.caption(f"ID: `{meta['candidate_id']}` • Uploaded by: {meta.get('uploaded_by','N/A')}")
        
        col1, col2 = st.columns(2)

        with col1:
            if st.button("👁️ View", key=f"view_{i}"):
                st.text_area("Résumé Summary", doc, height=300)

        with col2:
            delete_key = f"confirm_delete_{i}"
            if delete_key not in st.session_state:
                st.session_state[delete_key] = False

            if not st.session_state[delete_key]:
                if st.button("🗑️ Delete", key=f"del_{i}"):
                    st.session_state[delete_key] = True
                    st.warning(f"⚠️ Are you sure you want to delete `{meta.get('name', 'Unknown')}`?")
                    st.button("✅ Confirm Delete", key=f"confirm_{i}")
            else:
                if st.button("✅ Confirm Delete", key=f"confirm_{i}"):
                    collection.delete(ids=[meta["candidate_id"]])
                    if hasattr(chroma_client, "persist"): chroma_client.persist()
                    st.success("Deleted successfully.")
                    st.rerun()
                st.button("❌ Cancel", key=f"cancel_{i}", on_click=lambda k=delete_key: st.session_state.update({k: False}))

if matches_found == 0:
    st.warning("No matching candidates found.")
