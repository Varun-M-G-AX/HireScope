import streamlit as st
import json # Import json module for parsing summary
from utils import collection, chroma_client # Ensure these are correctly imported from your utils.py

st.set_page_config(
    page_title="HireScope - Candidate Profiles",
    page_icon="📇", # Changed to a more fitting icon for profiles
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📇 Stored Candidate Résumés")
st.markdown("Browse and manage all résumés processed by HireScope AI.")

# ───────── Fetch Data ─────────
# Fetch all documents (summaries) and their associated metadatas from ChromaDB
try:
    res = collection.get(include=["metadatas", "documents"])
    metas, docs = res["metadatas"], res["documents"]
except Exception as e:
    st.error(f"🚨 Failed to load candidate data from the database: {e}")
    st.info("Please ensure ChromaDB is running and accessible. You might need to upload résumés first.")
    metas, docs = [], [] # Initialize as empty to prevent further errors

if not metas:
    st.info("No résumés found in the database yet. Please upload some using the 'Upload Résumés' page.")
    st.stop()

# ───────── Filter Options (Sidebar) ─────────
st.sidebar.header("🔍 Filter Candidates")
st.sidebar.markdown("Use the fields below to narrow down the list of résumés.")

name_filter = st.sidebar.text_input("By Candidate Name", placeholder="e.g., John Doe")
id_filter   = st.sidebar.text_input("By Candidate ID", placeholder="e.g., john-doe-2023...")
by_hr       = st.sidebar.text_input("By Uploader Name (HR Rep)", placeholder="e.g., Jane Smith")
keywords    = st.sidebar.text_input("Contains Keyword in Summary", placeholder="e.g., Python, AWS, Project Manager")

# Function to check if a candidate matches the current filters
def matches(meta, doc):
    """
    Checks if a candidate's metadata and document content match the applied filters.
    """
    name_match = (name_filter.lower() in meta['name'].lower() if name_filter else True)
    id_match = (id_filter.lower() in meta['candidate_id'].lower() if id_filter else True)
    
    # Safely get 'uploaded_by' as it might be missing in older entries
    uploaded_by_value = meta.get('uploaded_by', '')
    hr_match = (by_hr.lower() in uploaded_by_value.lower() if by_hr else True)
    
    keyword_match = (keywords.lower() in doc.lower() if keywords else True)
    
    return name_match and id_match and hr_match and keyword_match

# ───────── Display Results ─────────
st.markdown("---") # Separator for visual clarity
st.subheader("Candidate Profiles")

matches_found = 0
# Use a container for the grid of cards to ensure consistent layout
card_container = st.container()

with card_container:
    # Create a list to hold candidates that match filters
    filtered_candidates = []
    for i, (meta, doc) in enumerate(zip(metas, docs)):
        if matches(meta, doc):
            filtered_candidates.append((meta, doc, i)) # Store meta, doc, and original index

    if not filtered_candidates:
        st.warning("No matching candidates found based on your filters.")
        st.info("Try adjusting your search criteria or upload new résumés.")
    else:
        # Arrange cards in columns for a grid-like layout
        # Changed num_cols from 3 to 2 to make cards wider
        num_cols = 2 
        cols = st.columns(num_cols)
        
        for idx, (meta, doc, original_index) in enumerate(filtered_candidates):
            with cols[idx % num_cols]: # Distribute cards evenly across columns
                # Use st.container(border=True) for a nice visual card-like container
                with st.container(border=True): 
                    st.markdown(f"### 👤 {meta.get('name', 'Unknown')}")
                    st.caption(f"ID: `{meta['candidate_id']}`")
                    st.caption(f"Uploaded by: {meta.get('uploaded_by', 'N/A')}")
                    st.markdown("---") # Separator

                    # View Details Button and Expander
                    # Use a unique key based on the original_index to avoid conflicts
                    view_expander_key = f"view_expander_{original_index}"
                    
                    # Initialize expander state in session_state if not present
                    if view_expander_key not in st.session_state:
                        st.session_state[view_expander_key] = False

                    # Button to toggle the expander
                    if st.button("👁️ View Details", key=f"view_btn_{original_index}", use_container_width=True):
                        st.session_state[view_expander_key] = not st.session_state[view_expander_key]
                        st.rerun() # Rerun to immediately reflect the expander state change

                    # The expander itself, conditionally displayed
                    if st.session_state.get(view_expander_key, False):
                        with st.expander("Résumé Details", expanded=True):
                            tab1, tab2 = st.tabs(["AI Summary", "Raw Text (Not Stored)"])
                            
                            with tab1:
                                st.write("**AI-Generated Summary:**")
                                # Attempt to pretty-print JSON if the summary is valid JSON
                                try:
                                    summary_json = json.loads(doc)
                                    st.json(summary_json)
                                except json.JSONDecodeError:
                                    st.text_area("AI-Generated Summary", doc, height=250, disabled=True, key=f"summary_display_{original_index}")
                            
                            with tab2:
                                st.write("**Raw Extracted Text:**")
                                st.info(
                                    "The full raw text of the résumé is not stored in the database for this view. "
                                    "It is processed for summarization and embeddings. "
                                    "For raw text review, please refer to the 'Upload Résumés' page after upload."
                                )
                                # You could display the summary here again as a placeholder if desired
                                # st.text_area("Raw Text Placeholder", doc, height=250, disabled=True, key=f"raw_text_placeholder_{original_index}")
                        
                    st.markdown("<br>", unsafe_allow_html=True) # Add some space below the expander

                    # Delete Logic
                    delete_confirmation_key = f"confirm_delete_{original_index}"
                    
                    # Initialize confirmation state if not present
                    if delete_confirmation_key not in st.session_state:
                        st.session_state[delete_confirmation_key] = False

                    if not st.session_state[delete_confirmation_key]:
                        # Show initial delete button
                        if st.button("🗑️ Delete Profile", key=f"delete_btn_{original_index}", use_container_width=True):
                            st.session_state[delete_confirmation_key] = True # Set confirmation flag
                            st.rerun() # Rerun to show confirmation buttons
                    else:
                        # Show confirmation buttons
                        st.warning(f"⚠️ Confirm deletion of **{meta.get('name', 'Unknown')}**?")
                        confirm_col, cancel_col = st.columns(2)
                        with confirm_col:
                            if st.button("✅ Confirm Delete", key=f"confirm_del_btn_{original_index}", use_container_width=True):
                                try:
                                    collection.delete(ids=[meta["candidate_id"]])
                                    if hasattr(chroma_client, "persist"):
                                        chroma_client.persist() # Persist changes to disk
                                    st.success(f"Deleted **{meta.get('name', 'Unknown')}** successfully.", icon="🗑️")
                                    st.toast(f"Profile for {meta.get('name', 'Unknown')} deleted!", icon="🗑️")
                                    st.session_state[delete_confirmation_key] = False # Reset confirmation
                                    st.rerun() # Rerun to update the list of candidates
                                except Exception as e:
                                    st.error(f"Error deleting profile: {e}")
                                    st.session_state[delete_confirmation_key] = False # Reset confirmation on error
                                    st.rerun() # Rerun to clear confirmation buttons
                        with cancel_col:
                            if st.button("❌ Cancel", key=f"cancel_del_btn_{original_index}", use_container_width=True):
                                st.session_state[delete_confirmation_key] = False # Reset confirmation
                                st.rerun() # Rerun to hide confirmation buttons