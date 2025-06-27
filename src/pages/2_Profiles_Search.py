import streamlit as st
import json
from utils import collection, chroma_client

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇",
    layout="wide"
)

st.title("📇 Stored Candidate Résumés")

# ───────── Retrieve Data ─────────
try:
    res = collection.get(include=["metadatas", "documents"])
    metas, docs = res["metadatas"], res["documents"]
except Exception as e:
    st.error(f"🚨 Could not load data: {e}")
    st.stop()

if not metas:
    st.info("No résumés found in the database. Please upload some.")
    st.stop()

# ───────── Sidebar Filters ─────────
st.sidebar.header("🔍 Filter Candidates")
name_filter = st.sidebar.text_input("Name")
id_filter = st.sidebar.text_input("Candidate ID")
uploaded_by_filter = st.sidebar.text_input("Uploaded By")
keywords_filter = st.sidebar.text_input("Keyword in Summary")

def matches(meta, doc):
    return (
        (name_filter.lower() in meta['name'].lower() if name_filter else True) and
        (id_filter.lower() in meta['candidate_id'].lower() if id_filter else True) and
        (uploaded_by_filter.lower() in meta.get("uploaded_by", "").lower() if uploaded_by_filter else True) and
        (keywords_filter.lower() in doc.lower() if keywords_filter else True)
    )

# ───────── Candidate Cards ─────────
st.markdown("---")
st.markdown("### 👥 Candidate List")

columns = st.columns(3)  # 3 per row
card_index = 0
results_found = 0

for i, (meta, doc) in enumerate(zip(metas, docs)):
    if not matches(meta, doc):
        continue
    results_found += 1
    col = columns[card_index % 3]

    with col:
        with st.container(border=True):
            name = meta.get("name", "Unknown")
            cid = meta.get("candidate_id", "N/A")
            uploader = meta.get("uploaded_by", "N/A")
            summary = doc

            # Attempt to parse JSON summary
            try:
                parsed = json.loads(summary)
                email = parsed.get("email", "N/A")
                phone = parsed.get("phone", "N/A")
                linkedin = parsed.get("linkedin", None)
            except Exception:
                email = phone = "N/A"
                linkedin = None

            # Card content
            st.markdown(f"#### 👤 {name}")
            st.caption(f"🆔 `{cid}`")
            st.caption(f"🗂️ Uploaded by: {uploader}")
            st.markdown("---")

            if email != "N/A":
                st.markdown(f"📧 **Email**: [{email}](mailto:{email})")
            if phone != "N/A":
                st.markdown(f"📱 **Phone**: {phone}")
            if linkedin:
                st.markdown(f"🔗 **LinkedIn**: [View Profile]({linkedin})")

            st.markdown("---")

            # Expand Summary
            if st.button("📄 View Summary", key=f"view_{i}"):
                with st.expander(f"Summary for {name}", expanded=True):
                    try:
                        st.json(json.loads(doc))
                    except:
                        st.text_area("Résumé Summary", doc, height=300)

            # Delete Confirmation
            confirm_key = f"confirm_delete_{i}"
            if confirm_key not in st.session_state:
                st.session_state[confirm_key] = False

            if not st.session_state[confirm_key]:
                if st.button("🗑️ Delete", key=f"del_{i}"):
                    st.session_state[confirm_key] = True
                    st.experimental_rerun()
            else:
                st.warning(f"Confirm deletion of {name}?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Confirm", key=f"yes_del_{i}"):
                        collection.delete(ids=[cid])
                        if hasattr(chroma_client, "persist"):
                            chroma_client.persist()
                        st.success(f"Deleted {name}")
                        st.rerun()
                with c2:
                    if st.button("❌ Cancel", key=f"no_del_{i}"):
                        st.session_state[confirm_key] = False
                        st.rerun()

    card_index += 1

if results_found == 0:
    st.warning("No matching candidates found.")
