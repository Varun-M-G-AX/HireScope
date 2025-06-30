import re
import streamlit as st
from datetime import datetime
from utils import collection, openai  # You must provide your own collection and openai setup

# Initialize sidebar state first
if 'sidebar_open' not in st.session_state:
    st.session_state.sidebar_open = True

# --- Bootstrap SVG Icons ---
ICONS = {
    "chat": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M2.678 11.894a1 1 0 0 1 .287.801 11 11 0 0 1-.398 2c1.395-.323 2.247-.697 2.634-.893a1 1 0 0 1 .71-.074A8 8 0 0 0 8 14c3.996 0 7-2.807 7-6s-3.004-6-7-6-7 2.808-7 6c0 1.468.617 2.83 1.678 3.894m-.493 3.905a22 22 0 0 1-.713.129c-.2.032-.352-.176-.273-.362a10 10 0 0 0 .244-.637l.003-.01c.248-.72.45-1.548.524-2.319C.743 11.37 0 9.76 0 8c0-3.866 3.582-7 8-7s8 3.134 8 7-3.582 7-8 7a9 9 0 0 1-2.347-.306c-.52.263-1.639.742-3.468 1.105'/></svg>""",
    "plus": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4'/></svg>""",
    "three_dots": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M3 9.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3'/></svg>""",
    "trash": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z'/><path d='M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z'/></svg>""",
    "pencil": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L10.5 8.207l-3-3zm1.414 1.414-2.293 2.293L12.793 5.5zm-11.207 9.793L1 14l2.5-1.5 1.414-1.414L2.707 8.879z'/><path d='M10.5 1.5a.5.5 0 0 0-.5.5v.5h3a.5.5 0 0 1 .5.5v1A1.5 1.5 0 0 1 12 5.5H9.5a.5.5 0 0 1-.5-.5V4a.5.5 0 0 0-1 0v1.5A1.5 1.5 0 0 0 9.5 7h2.793l-3.793 3.793a.5.5 0 0 0-.146.353v.708c0 .193.084.377.229.518l1.25 1.25a.73.73 0 0 0 1.033 0l5.25-5.25a.5.5 0 0 0 0-.708L13.207 4.5H15.5a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-3V2a.5.5 0 0 0-.5-.5z'/></svg>""",
    "check": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z'/></svg>""",
    "x": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708'/></svg>""",
    "robot": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5'/><path d='M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135'/><path d='M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5'/></svg>""",
    "person": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z'/></svg>""",
    "menu": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5'/></svg>""",
    "chevron_right": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708'/></svg>""",
    "chevron_left": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0'/></svg>"""
}

# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
/* Hide default Streamlit elements but keep system settings */
.stDeployButton {display: none;}
#MainMenu {visibility: visible !important;}
footer {visibility: visible;}
header[data-testid="stHeader"] {visibility: visible;}
.stMainBlockContainer {padding-top: 1rem;}
/* Fixed Sidebar Toggle Button - Only visible when sidebar is closed */
.sidebar-toggle-fixed {
    position: fixed !important;
    top: 1rem !important;
    left: 1rem !important;
    z-index: 9999 !important;
    background: #1c83e1 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    cursor: pointer !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.2s ease !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
    min-width: 44px !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.sidebar-toggle-fixed:hover {
    background: #0d6efd !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2) !important;
}
/* Main content adjustment when sidebar is closed */
.main-content-adjusted {
    margin-left: 0 !important;
    padding-left: 80px !important;
}
/* Skeleton loading animation */
@keyframes skeleton-loading {
    0% {
        background-position: -200px 0;
    }
    100% {
        background-position: calc(200px + 100%) 0;
    }
}
.skeleton {
    display: inline-block;
    height: 1em;
    position: relative;
    overflow: hidden;
    background: linear-gradient(90deg, 
        rgba(255, 255, 255, 0.1) 25%, 
        rgba(255, 255, 255, 0.2) 50%, 
        rgba(255, 255, 255, 0.1) 75%);
    background-size: 200px 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 0.25rem;
}
.skeleton-container {
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0.75rem;
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    background: rgba(40, 167, 69, 0.1);
    border-left: 3px solid #28a745;
}
.skeleton-icon {
    flex-shrink: 0;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: #28a745;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
}
.skeleton-content {
    flex: 1;
    line-height: 1.6;
}
.skeleton-line {
    margin: 0.5rem 0;
}
.skeleton-line:nth-child(1) { width: 90%; }
.skeleton-line:nth-child(2) { width: 85%; }
.skeleton-line:nth-child(3) { width: 70%; }
.skeleton-line:nth-child(4) { width: 95%; }
/* Thinking dots animation */
.thinking-dots {
    display: inline-flex;
    gap: 0.25rem;
    align-items: center;
    margin-left: 0.5rem;
}
.thinking-dot {
    width: 0.375rem;
    height: 0.375rem;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.4;
    animation: thinking 1.4s infinite ease-in-out;
}
.thinking-dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-dot:nth-child(2) { animation-delay: -0.16s; }
.thinking-dot:nth-child(3) { animation-delay: 0; }
@keyframes thinking {
    0%, 80%, 100% {
        opacity: 0.4;
        transform: scale(1);
    }
    40% {
        opacity: 1;
        transform: scale(1.2);
    }
}
/* Sidebar styling */
.stSidebar > div {
    padding-top: 1rem;
}
/* Chat item styling */
.chat-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem;
    margin: 0.25rem 0;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: background-color 0.2s ease;
    position: relative;
}
.chat-item:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
.chat-item.active {
    background-color: rgba(255, 255, 255, 0.15);
}
.chat-title {
    flex: 1;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    font-size: 0.9rem;
    margin-right: 0.5rem;
}
.chat-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}
.chat-item:hover .chat-actions {
    opacity: 1;
}
.icon-button {
    background: none;
    border: none;
    padding: 0.25rem;
    border-radius: 0.25rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
}
.icon-button:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
/* New chat button */
.new-chat-btn {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    color: inherit;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
}
.new-chat-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
}
/* Message styling */
.message {
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0.75rem;
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
}
.message.user {
    background: rgba(0, 123, 255, 0.1);
    border-left: 3px solid #007bff;
}
.message.assistant {
    background: rgba(40, 167, 69, 0.1);
    border-left: 3px solid #28a745;
}
.message-icon {
    flex-shrink: 0;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}
.message.user .message-icon {
    background: #007bff;
    color: white;
}
.message.assistant .message-icon {
    background: #28a745;
    color: white;
}
.message-content {
    flex: 1;
    line-height: 1.6;
}
/* Rename input styling */
.rename-input {
    width: 100%;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.25rem;
    padding: 0.25rem 0.5rem;
    color: inherit;
    font-size: 0.9rem;
}
.rename-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
}
/* Responsive design */
@media (max-width: 768px) {
    .message {
        padding: 0.75rem;
        margin: 0.75rem 0;
    }
    
    .chat-title {
        font-size: 0.8rem;
    }
    
    .main-content-adjusted {
        padding-left: 60px !important;
    }
}
/* Sidebar toggle button styling */
.sidebar-toggle-btn {
    background: #1c83e1 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
    cursor: pointer !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.2s ease !important;
    font-weight: bold !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}
.sidebar-toggle-btn:hover {
    background: #0d6efd !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# --- Streamlit Config ---
st.set_page_config(
    page_title="HireScope Chat", 
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.sidebar_open else "collapsed"
)

# --- Helper Functions ---
def generate_chat_title(content):
    """Generate a short title from the first message"""
    words = content.split()[:4]
    return " ".join(words) + ("..." if len(content.split()) > 4 else "")

def create_icon_button(icon_key, button_key, tooltip=""):
    """Create an icon button with proper styling"""
    return f"""
    <button class="icon-button" onclick="document.getElementById('{button_key}').click()" title="{tooltip}">
        {ICONS[icon_key]}
    </button>
    """

# --- Session State Init ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
    initial_title = "New Chat"
    st.session_state.chats[initial_title] = [{"role": "system", "content": "You are a recruiter assistant."}]
    st.session_state.active = initial_title

if "editing_chat" not in st.session_state:
    st.session_state.editing_chat = None

if "dropdown_open" not in st.session_state:
    st.session_state.dropdown_open = {}

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# --- Sidebar Toggle Button in Main Content (when sidebar is closed) ---
if not st.session_state.sidebar_open:
    # Create a container at the top for the toggle button
    toggle_container = st.container()
    with toggle_container:
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.button("☰", key="open_sidebar_btn", help="Open Sidebar", type="primary"):
                st.session_state.sidebar_open = True
                st.rerun()
    
    # Add CSS to make the main content area have proper spacing
    st.markdown('<div class="main-content-adjusted">', unsafe_allow_html=True)

# --- Sidebar ---
if st.session_state.sidebar_open:
    with st.sidebar:
        # New Chat Button
        st.markdown("**Create New Chat**")
        if st.button("➕ New Chat", key="new_chat", help="Start a new conversation", use_container_width=True):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            title = f"New Chat"
            counter = 1
            while title in st.session_state.chats:
                title = f"New Chat {counter}"
                counter += 1
            
            st.session_state.chats[title] = [{"role": "system", "content": "You are a recruiter assistant."}]
            st.session_state.active = title
            st.session_state.editing_chat = None
            st.rerun()
        
        st.markdown("---")
        
        # Chat History
        if st.session_state.chats:
            st.markdown("**Recent Chats**")
            
            for chat_key in sorted(st.session_state.chats.keys(), reverse=True):
                is_active = chat_key == st.session_state.active
                is_editing = st.session_state.editing_chat == chat_key
                
                if is_editing:
                    # Rename mode
                    col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
                    with col1:
                        new_name = st.text_input(
                            "", 
                            value=chat_key, 
                            key=f"rename_{chat_key}",
                            label_visibility="collapsed"
                        )
                    with col2:
                        if st.button("✓", key=f"confirm_{chat_key}", help="Confirm rename"):
                            if new_name and new_name != chat_key and new_name not in st.session_state.chats:
                                st.session_state.chats[new_name] = st.session_state.chats.pop(chat_key)
                                if st.session_state.active == chat_key:
                                    st.session_state.active = new_name
                            st.session_state.editing_chat = None
                            st.rerun()
                    with col3:
                        if st.button("✕", key=f"cancel_{chat_key}", help="Cancel rename"):
                            st.session_state.editing_chat = None
                            st.rerun()
                else:
                    # Normal mode
                    col1, col2 = st.columns([0.85, 0.15])
                    
                    with col1:
                        # Chat selection button
                        button_type = "primary" if is_active else "secondary"
                        if st.button(
                            chat_key, 
                            key=f"select_{chat_key}",
                            help=f"Switch to {chat_key}",
                            use_container_width=True,
                            type=button_type
                        ):
                            st.session_state.active = chat_key
                            st.session_state.editing_chat = None
                            st.rerun()
                    
                    with col2:
                        # Three dots menu
                        if st.button("⋮", key=f"menu_{chat_key}", help="Chat options"):
                            st.session_state.dropdown_open[chat_key] = not st.session_state.dropdown_open.get(chat_key, False)
                            st.rerun()
                    
                    # Dropdown menu
                    if st.session_state.dropdown_open.get(chat_key, False):
                        with st.container():
                            subcol1, subcol2 = st.columns(2)
                            with subcol1:
                                if st.button("✏️", key=f"edit_{chat_key}", help="Rename chat"):
                                    st.session_state.editing_chat = chat_key
                                    st.session_state.dropdown_open[chat_key] = False
                                    st.rerun()
                            with subcol2:
                                if st.button("🗑️", key=f"delete_{chat_key}", help="Delete chat"):
                                    if len(st.session_state.chats) > 1:
                                        del st.session_state.chats[chat_key]
                                        if st.session_state.active == chat_key:
                                            st.session_state.active = next(iter(st.session_state.chats))
                                        st.session_state.dropdown_open.pop(chat_key, None)
                                        if st.session_state.editing_chat == chat_key:
                                            st.session_state.editing_chat = None
                                        st.rerun()

# --- Main Chat Area ---
st.title("💼 HireScope Chat")
st.markdown("""
<div style="
    margin: 1rem 0 2rem 0;
    padding: 0;
">
    <h1 style="
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.05em;
        margin: 0;
        padding: 0;
        text-align: left;
        line-height: 1.1;
    ">💼 HireScope Chat</h1>
    <p style="
        color: var(--text-tertiary);
        font-size: 1.1rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        letter-spacing: 0.01em;
    ">AI-Powered Recruitment Assistant</p>
</div>
""", unsafe_allow_html=True)

# Get active chat
active_key = st.session_state.active
if active_key not in st.session_state.chats:
    # Fallback if active chat was deleted
    active_key = next(iter(st.session_state.chats))
    st.session_state.active = active_key

chat = st.session_state.chats[active_key]

# Display chat messages
chat_container = st.container()
with chat_container:
    for msg in chat[1:]:  # Skip system message
        role = msg['role']
        content = msg['content']
        
        if role == "user":
            st.markdown(f"""
            <div class="message user">
                <div class="message-icon">
                    {ICONS['person']}
                </div>
                <div class="message-content">
                    <strong>You</strong><br>
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message assistant">
                <div class="message-icon">
                    {ICONS['robot']}
                </div>
                <div class="message-content">
                    <strong>HireScope Assistant</strong><br>
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Show skeleton loading animation when generating response
    if st.session_state.is_generating:
        st.markdown(f"""
        <div class="skeleton-container">
            <div class="skeleton-icon">
                {ICONS['robot']}
            </div>
            <div class="skeleton-content">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <strong>HireScope Assistant</strong>
                    <div class="thinking-dots">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Chat input
prompt = st.chat_input("Ask about candidates, resumes, or hiring...")

if prompt:
    # Add user message
    chat.append({"role": "user", "content": prompt})
    
    # Set generating state to show skeleton
    st.session_state.is_generating = True
    st.rerun()

# Process response if we're in generating state
if st.session_state.is_generating:
    # Generate response
    try:
        total = collection.count()
        if total == 0:
            reply = "⚠️ No resume data available. Please upload some resumes to get started."
        else:
            # Query the vector database
            hits = collection.query(query_texts=[chat[-1]["content"]], n_results=3)
            context = "\n---\n".join(hits.get("documents", [[]])[0])
            
            # Update system message with context
            chat[0]["content"] = f"""You are a recruiter assistant. Answer ONLY from these résumé snippets:
{context}
Be helpful, professional, and provide specific information from the resumes when available."""
            
            # Get AI response
            result = openai.chat.completions.create(
                model="gpt-4o",
                messages=chat,
                temperature=0.3,
                max_tokens=1000
            )
            reply = result.choices[0].message.content
            
    except Exception as e:
        reply = f"⚠️ Error processing your request: {str(e)}"
    
    # Add assistant response
    chat.append({"role": "assistant", "content": reply})
    
    # Update chat title if it's still default
    if active_key.startswith("New Chat") and len(chat) == 3:  # System + User + Assistant
        new_title = generate_chat_title(chat[-2]["content"])  # Use user message for title
        if new_title != active_key:
            st.session_state.chats[new_title] = st.session_state.chats.pop(active_key)
            st.session_state.active = new_title
    
    # Reset generating state
    st.session_state.is_generating = False
    st.rerun()

# Close the main content div if sidebar is closed
if not st.session_state.sidebar_open:
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8rem;'>"
    "HireScope Chat - AI-Powered Recruitment Assistant"
    "</div>", 
    unsafe_allow_html=True
)
