# Updated Streamlit Sidebar Toggle Code Snippet
import streamlit as st

# --- State initialization ---
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

# --- SVG Icon for Toggle ---
ICON_MENU = """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5'/></svg>"""

# --- CSS Styling ---
st.markdown("""
<style>
.sidebar-toggle-btn {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 9999;
    background: rgba(28, 131, 225, 0.9);
    border: 1px solid rgba(28, 131, 225, 0.5);
    border-radius: 0.5rem;
    padding: 0.75rem;
    cursor: pointer;
    backdrop-filter: blur(10px);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    min-width: 44px;
    min-height: 44px;
}
.sidebar-toggle-btn:hover {
    background: rgba(28, 131, 225, 1);
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}
#sidebar-toggle-container {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 9999;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar Toggle Button (visible only when sidebar is closed) ---
if not st.session_state.sidebar_open:
    st.markdown(f"""
    <div id="sidebar-toggle-container">
        <button class="sidebar-toggle-btn" onclick="toggleSidebar()">
            {ICON_MENU}
        </button>
    </div>
    <script>
    function toggleSidebar() {{
        const elements = parent.document.querySelectorAll('button');
        const toggleBtn = Array.from(elements).find(btn => btn.innerText.includes('Open Sidebar'));
        if (toggleBtn) toggleBtn.click();
    }}
    </script>
    """, unsafe_allow_html=True)

    # This hidden Streamlit button is clicked programmatically
    if st.button("Open Sidebar", key="hidden_open_sidebar_btn"):
        st.session_state.sidebar_open = True
        st.rerun()

# --- Real Sidebar Logic ---
if st.session_state.sidebar_open:
    with st.sidebar:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown("### HireScope")
        with col2:
            if st.button("\u2715", key="close_sidebar"):
                st.session_state.sidebar_open = False
                st.rerun()

        st.write("This is your sidebar content.")

# --- Main Content ---
st.title("Main App Content")
st.write("This area remains visible even when sidebar is closed.")
