import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

# --- Page Configuration ---
st.set_page_config(
    page_title="HireScope Chat",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
if 'sidebar_open' not in st.session_state:
    st.session_state.sidebar_open = True

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

# --- SVG Icons ---
ICONS = {
    "plus": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4'/></svg>""",
    "robot": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5'/><path d='M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135'/><path d='M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5'/></svg>""",
    "person": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z'/></svg>""",
    "chevron_right": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708'/></svg>""",
    "menu": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5'/></svg>"""
}

# --- Modern CSS with Dark/Light Mode Support ---
st.markdown("""
<style>
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* CSS Variables for theme support */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #10b981;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --border-color: #e5e7eb;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    :root {
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --bg-primary: #111827;
        --bg-secondary: #1f2937;
        --border-color: #374151;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
    }
}

/* Global styles */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background-color: var(--bg-primary);
}

/* Hide Streamlit branding */
.stDeployButton {
    display: none !important;
}

footer {
    visibility: hidden;
}

.stMainBlockContainer {
    padding-top: 2rem;
    max-width: 1200px;
}

/* Typography */
h1 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Sidebar styling */
.stSidebar {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
}

.stSidebar .stButton > button {
    width: 100%;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-weight: 500;
    transition: all 0.2s ease;
}

.stSidebar .stButton > button:hover {
    background: var(--bg-secondary);
    transform: translateY(-1px);
    box-shadow: var(--shadow);
}

.stSidebar .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border: none;
    color: white;
}

.stSidebar .stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Message styling */
.message {
    padding: 1.5rem;
    margin: 1rem 0;
    border-radius: 12px;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    box-shadow: var(--shadow);
}

.message.user {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05));
    border-left: 4px solid var(--primary-color);
}

.message.assistant {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
    border-left: 4px solid var(--success-color);
}

.message-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: var(--shadow);
}

.message.user .message-icon {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
}

.message.assistant .message-icon {
    background: linear-gradient(135deg, var(--success-color), #059669);
    color: white;
}

.message-content {
    flex: 1;
    color: var(--text-primary);
    line-height: 1.6;
}

.message-content strong {
    color: var(--text-primary);
    font-weight: 600;
}

/* Chat input */
.stChatInput > div {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    background: var(--bg-primary) !important;
    box-shadow: var(--shadow) !important;
}

.stChatInput input {
    color: var(--text-primary) !important;
    background: transparent !important;
    font-size: 1rem !important;
    padding: 1rem !important;
}

/* Loading animation */
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
    background: var(--success-color);
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

.loading-container {
    padding: 1.5rem;
    margin: 1rem 0;
    border-radius: 12px;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
    border-left: 4px solid var(--success-color);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow);
}

/* Responsive design */
@media (max-width: 768px) {
    .stMainBlockContainer {
        padding: 1rem;
    }
    
    .message {
        padding: 1rem;
        gap: 0.75rem;
    }
    
    .message-icon {
        width: 2rem;
        height: 2rem;
    }
    
    h1 {
        font-size: 2rem !important;
    }
}

/* Toggle button for sidebar */
.sidebar-toggle {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 1000;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.75rem;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    transition: all 0.2s ease;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 44px;
    min-height: 44px;
}

.sidebar-toggle:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.main-with-toggle {
    margin-left: 80px;
}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def generate_chat_title(content):
    """Generate a short title from the first message"""
    words = content.split()[:4]
    return " ".join(words) + ("..." if len(content.split()) > 4 else "")

# --- Sidebar Toggle Logic ---
if not st.session_state.sidebar_open:
    # Show toggle button when sidebar is closed
    st.markdown("""
    <button class="sidebar-toggle" onclick="window.parent.document.querySelector('[data-testid=\\"collapsedControl\\"]').click()">
        """ + ICONS['menu'] + """
    </button>
    <div class="main-with-toggle">
    """, unsafe_allow_html=True)

# --- Sidebar ---
if st.session_state.sidebar_open:
    with st.sidebar:
        # Header with collapse button
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown("### 💼 HireScope")
        with col2:
            if st.button(">>", key="collapse_sidebar", help="Collapse sidebar"):
                st.session_state.sidebar_open = False
                st.rerun()
        
        st.markdown("---")
        
        # New Chat Button
        if st.button("➕ New Chat", key="new_chat", help="Start a new conversation", use_container_width=True, type="primary"):
            title = "New Chat"
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
                    col1, col2 = st.columns([0.85, 0.15])
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
st.markdown("# HireScope Chat")
st.markdown("*AI-Powered Recruitment Assistant*")

# Get active chat
active_key = st.session_state.active
if active_key not in st.session_state.chats:
    # Fallback if active chat was deleted
    active_key = next(iter(st.session_state.chats))
    st.session_state.active = active_key

chat = st.session_state.chats[active_key]

# Display chat messages
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

# Show loading animation when generating response
if st.session_state.is_generating:
    st.markdown(f"""
    <div class="loading-container">
        <div class="message-icon" style="background: linear-gradient(135deg, var(--success-color), #059669); color: white; width: 2.5rem; height: 2.5rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: var(--shadow);">
            {ICONS['robot']}
        </div>
        <div style="flex: 1; color: var(--text-primary); line-height: 1.6;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <strong>HireScope Assistant</strong>
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
            </div>
            <div style="color: var(--text-secondary);">Thinking...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Chat input
prompt = st.chat_input("Ask about candidates, resumes, or hiring...")

if prompt:
    # Add user message
    chat.append({"role": "user", "content": prompt})
    
    # Set generating state to show loading
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
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.875rem; padding: 1rem 0;">
    Built with ❤️ using Streamlit • HireScope Chat v2.0
</div>
""", unsafe_allow_html=True)