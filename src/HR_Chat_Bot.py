import streamlit as st
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="HireScope Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Scoped CSS ---
SCOPED_CSS = """
<link href='https://css.gg/css' rel='stylesheet'>
<style>
.hirescope-wrapper {
    --primary-bg: #ffffff;
    --secondary-bg: #f5f7fa;
    --text-color: #1a1a1a;
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --message-user-bg: #e1f5fe;
    --message-assistant-bg: #f1f8e9;
    --border-color: #e1e4e8;
    --shadow-color: rgba(0,0,0,0.1);
}

.hirescope-wrapper {
    background-color: var(--primary-bg);
    color: var(--text-color);
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.hirescope-wrapper section[data-testid="stSidebar"] {
    background-color: var(--secondary-bg);
    border-right: 1px solid var(--border-color);
}

.hirescope-wrapper .chat-header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    padding: 1.25rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px var(--shadow-color);
    color: white;
}

.hirescope-wrapper .chat-header h2 {
    margin: 0;
    font-weight: 600;
    font-size: 1.35rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.hirescope-wrapper .chat-message {
    padding: 0.75rem 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    max-width: 85%;
    position: relative;
    transition: all 0.2s ease;
}

.hirescope-wrapper .user-message {
    background-color: var(--message-user-bg);
    margin-left: auto;
    border-top-right-radius: 4px;
}

.hirescope-wrapper .assistant-message {
    background-color: var(--message-assistant-bg);
    margin-right: auto;
    border-top-left-radius: 4px;
}

.hirescope-wrapper .message-timestamp {
    font-size: 0.65rem;
    opacity: 0.7;
    margin-top: 0.25rem;
    text-align: right;
}

.hirescope-wrapper .typing-indicator {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--secondary-bg);
    border-radius: 18px;
    width: fit-content;
    margin-left: 0.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px var(--shadow-color);
    font-size: 0.85rem;
}

.hirescope-wrapper .typing-dots {
    display: flex;
    gap: 0.35rem;
}

.hirescope-wrapper .typing-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--primary-color);
    animation: typingAnimation 1.4s infinite ease-in-out;
}

.hirescope-wrapper .typing-dot:nth-child(1) { animation-delay: 0s; }
.hirescope-wrapper .typing-dot:nth-child(2) { animation-delay: 0.2s; }
.hirescope-wrapper .typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingAnimation {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
    30% { transform: translateY(-4px); opacity: 1; }
}

/* Buttons */
.hirescope-wrapper .stButton > button {
    width: 100%;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    background: var(--primary-color);
    color: white;
    border: none;
    transition: all 0.25s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.hirescope-wrapper .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px var(--shadow-color);
}

.hirescope-wrapper .delete-btn > button {
    background: #ff4b4b !important;
}

/* Chat List */
.hirescope-wrapper .chat-item {
    padding: 0.5rem;
    border-radius: 8px;
    margin-bottom: 0.35rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.hirescope-wrapper .chat-item:hover {
    background: rgba(102, 126, 234, 0.1);
}

.hirescope-wrapper .chat-item.active {
    background: rgba(102, 126, 234, 0.2);
}

/* Empty State */
.hirescope-wrapper .empty-state {
    text-align: center;
    padding: 2rem;
    color: var(--text-color);
    opacity: 0.7;
    font-style: italic;
}

/* Utility Classes */
.hirescope-wrapper .flex {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.hirescope-wrapper .badge {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    background: var(--secondary-bg);
    color: var(--text-color);
}
</style>
"""

# Inject scoped CSS
st.markdown(SCOPED_CSS, unsafe_allow_html=True)

# --- Session State Management ---
class SessionState:
    @staticmethod
    def initialize():
        if "all_chats" not in st.session_state:
            st.session_state.all_chats = {}
        if "active_chat" not in st.session_state:
            SessionState.new_chat()
        if "chat_titles" not in st.session_state:
            st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}
        if "is_generating" not in st.session_state:
            st.session_state.is_generating = False
        if "editing_title" not in st.session_state:
            st.session_state.editing_title = None
        if "show_delete_confirm" not in st.session_state:
            st.session_state.show_delete_confirm = False
    
    @staticmethod
    def new_chat():
        new_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        st.session_state.all_chats[new_title] = [{
            "role": "system",
            "content": (
                "You are a recruiting assistant. Answer ONLY from résumé snippets provided in context. "
                "If the query is unrelated to résumés, say you can only answer resume-related questions."
            )
        }]
        st.session_state.active_chat = new_title

SessionState.initialize()

# --- Helper Functions ---
def show_typing_indicator():
    return """
    <div class="typing-indicator">
        <span>HireScope AI is thinking</span>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """

def format_timestamp():
    return f'<div class="message-timestamp">{datetime.now().strftime("%H:%M")}</div>'

def generate_chat_title(messages):
    try:
        user_msgs = [m["content"] for m in messages if m["role"] == "user"][:3]
        if not user_msgs:
            return f"Chat - {datetime.now().strftime('%Y-%m-%d')}"
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Create a 3-5 word title about: {' '.join(user_msgs)}"
            }],
            temperature=0.3,
            max_tokens=20
        )
        title = response.choices[0].message.content.strip('"\'').strip()
        return title[:40]
    except:
        return f"Chat - {datetime.now().strftime('%Y-%m-%d')}"

# --- UI Components ---
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="flex">
            <i class="gg-bot"></i>
            <h3>HireScope Chat</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ New Chat", key="new_chat", use_container_width=True):
            SessionState.new_chat()
            st.session_state.is_generating = False
            st.session_state.editing_title = None
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.all_chats:
            sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
            
            for name in sorted_chats:
                title = st.session_state.chat_titles.get(name, name)
                display = title[:25] + "..." if len(title) > 28 else title
                
                if name == st.session_state.active_chat:
                    st.markdown(f"**{display}**")
                else:
                    if st.button(
                        display,
                        key=f"select_{name}",
                        use_container_width=True
                    ):
                        st.session_state.active_chat = name
                        st.rerun()
        
        st.markdown("---")
        
        if len(st.session_state.all_chats) > 1:
            if st.button("🗑️ Delete Current Chat", key="delete_chat", use_container_width=True):
                st.session_state.show_delete_confirm = True
            
            if st.session_state.show_delete_confirm:
                st.warning("Confirm deletion?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes", use_container_width=True):
                        name = st.session_state.active_chat
                        del st.session_state.chat_titles[name]
                        del st.session_state.all_chats[name]
                        st.session_state.active_chat = next(iter(st.session_state.all_chats.keys()))
                        st.session_state.show_delete_confirm = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.show_delete_confirm = False
                        st.rerun()

def render_chat_interface():
    chat = st.session_state.all_chats.get(st.session_state.active_chat, [])
    title = st.session_state.chat_titles.get(st.session_state.active_chat, "New Chat")
    
    # Chat Header
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.markdown(f"""
        <div class="chat-header">
            <h2>
                <i class="gg-briefcase"></i>
                {title}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("✏️", help="Rename chat"):
            st.session_state.editing_title = st.session_state.active_chat
            st.rerun()
    
    # Title Editor
    if st.session_state.editing_title == st.session_state.active_chat:
        new_title = st.text_input(
            "Edit chat title:", 
            value=title,
            key="title_edit_input",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Save", use_container_width=True):
                st.session_state.chat_titles[st.session_state.active_chat] = new_title
                st.session_state.editing_title = None
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.editing_title = None
                st.rerun()
    
    # Messages
    if len(chat) <= 1:  # Only system message
        st.markdown("""
        <div class="empty-state">
            <h3><i class="gg-smile"></i> Welcome to HireScope!</h3>
            <p>Ask about candidates in your database.</p>
            <p><em>Example: "Find Python developers with 5+ years experience"</em></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in chat[1:]:  # Skip system message
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="flex">
                        <i class="gg-user"></i>
                        <span style="font-weight:500;">You</span>
                    </div>
                    <div>{msg["content"]}</div>
                    {format_timestamp()}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div class="flex">
                        <i class="gg-bot"></i>
                        <span style="font-weight:500;">Assistant</span>
                    </div>
                    <div>{msg["content"]}</div>
                    {format_timestamp()}
                </div>
                """, unsafe_allow_html=True)
    
    # Typing indicator
    if st.session_state.is_generating:
        with st.chat_message("assistant"):
            st.markdown(show_typing_indicator(), unsafe_allow_html=True)

# --- Main App ---
st.markdown("<div class='hirescope-wrapper'>", unsafe_allow_html=True)
render_sidebar()
render_chat_interface()

# Chat input
query = st.chat_input(
    "Ask about candidates...", 
    disabled=st.session_state.is_generating,
    key="chat_input"
)

if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    chat = st.session_state.all_chats[st.session_state.active_chat]
    
    # Add user message
    chat.append({"role": "user", "content": query})
    
    # Auto-rename chat if needed
    if st.session_state.active_chat.startswith("New Chat"):
        new_title = generate_chat_title(chat)
        st.session_state.chat_titles[st.session_state.active_chat] = new_title
    
    # Process response
    try:
        if any(word in query.lower() for word in ["hi", "hello", "hey"]):
            reply = "Hello! How can I help with your recruiting needs today?"
        else:
            # Check for resume data
            total = collection.count()
            if total == 0:
                reply = "No resume data available. Please load candidate data first."
            else:
                # Get relevant resumes
                docs = collection.query(
                    query_texts=[query], 
                    n_results=min(3, total)
                ).get("documents", [[]])[0]
                
                if not docs or all(not d.strip() for d in docs):
                    reply = "No matching resumes found. Try different search terms."
                else:
                    # Get AI response
                    context = "Context:\n" + "\n---\n".join(docs)
                    chat[0]["content"] = context
                    
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=chat,
                        temperature=0.3,
                        max_tokens=500
                    )
                    reply = response.choices[0].message.content
        
        chat.append({"role": "assistant", "content": reply})
    except Exception as e:
        chat.append({"role": "assistant", "content": f"Error: {str(e)}"})
    finally:
        st.session_state.is_generating = False
        st.rerun()

# Footer
st.markdown("""
<div class="footer">
    <div class="flex" style="justify-content: center;">
        <i class="gg-terminal"></i>
        <span>HireScope AI Recruiting Assistant</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # Close hirescope-wrapper
