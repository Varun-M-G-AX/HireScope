import re
import streamlit as st
from datetime import datetime
import time
from utils import collection, openai

# --- Page Configuration ---
st.set_page_config(
    page_title="💬 HireScope Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS.GG Icons Setup ---
GG_CSS = """
<link href='https://css.gg/css' rel='stylesheet'>
<style>
/* Dark/Light Mode Variables */
:root {
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

@media (prefers-color-scheme: dark) {
  :root {
    --primary-bg: #1e1e1e;
    --secondary-bg: #2d2d2d;
    --text-color: #f0f0f0;
    --primary-color: #7c93ff;
    --secondary-color: #9a6bff;
    --message-user-bg: #2a3a45;
    --message-assistant-bg: #2a3d35;
    --border-color: #3a3a3a;
    --shadow-color: rgba(0,0,0,0.3);
  }
}

/* Base Styles */
body {
  background-color: var(--primary-bg);
  color: var(--text-color);
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
  background-color: var(--secondary-bg);
}

/* Header Styling */
.chat-header {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  padding: 1.25rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 15px var(--shadow-color);
}

.chat-header h2 {
  margin: 0;
  font-weight: 600;
  font-size: 1.35rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Message Styling */
.chat-message {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  max-width: 85%;
  position: relative;
  transition: all 0.2s ease;
}

.user-message {
  background-color: var(--message-user-bg);
  margin-left: auto;
  border-top-right-radius: 4px;
}

.assistant-message {
  background-color: var(--message-assistant-bg);
  margin-right: auto;
  border-top-left-radius: 4px;
}

.message-timestamp {
  font-size: 0.65rem;
  opacity: 0.7;
  margin-top: 0.25rem;
  text-align: right;
}

/* Typing Indicator */
.typing-indicator-container {
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

.typing-animation {
  display: flex;
  gap: 0.35rem;
}

.typing-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--primary-color);
  animation: typingAnimation 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: 0s; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingAnimation {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* Button Styling */
.stButton > button {
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

.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px var(--shadow-color);
}

.secondary-btn > button {
  background: var(--secondary-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

.secondary-btn > button:hover {
  background: var(--secondary-bg);
  border-color: var(--primary-color);
}

.delete-btn > button {
  background: #ff4b4b !important;
}

/* Chat List Styling */
.chat-item {
  padding: 0.5rem;
  border-radius: 8px;
  margin-bottom: 0.35rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.chat-item.active {
  background: rgba(102, 126, 234, 0.2);
}

.chat-item .gg-trash {
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.chat-item:hover .gg-trash {
  opacity: 1;
}

.chat-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-grow: 1;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-color);
  opacity: 0.7;
  font-style: italic;
}

/* Footer */
.footer {
  text-align: center;
  color: var(--text-color);
  font-size: 0.85rem;
  padding: 1rem;
  opacity: 0.8;
}

/* General Utility Classes */
.flex {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mb-1 { margin-bottom: 1rem; }
.mt-1 { margin-top: 1rem; }
.badge {
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  background: var(--secondary-bg);
  color: var(--text-color);
}
</style>
"""

# Inject CSS into app
st.markdown(GG_CSS, unsafe_allow_html=True)

# --- Chat Context Prompt ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a recruiting assistant. "
        "Answer ONLY from résumé snippets provided in context. "
        "If the query is unrelated to candidates or résumés, say: "
        "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
    )
}

# --- Session Initialization ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "active_chat" not in st.session_state:
    new_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    st.session_state.active_chat = new_title
    st.session_state.all_chats[new_title] = [SYSTEM_PROMPT]
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "editing_title" not in st.session_state:
    st.session_state.editing_title = None

# --- Helper Functions ---
def show_typing_indicator():
    """Display enhanced typing indicator with smooth animation"""
    return """
    <div class="typing-indicator-container">
        <span>HireScope AI is thinking</span>
        <div class="typing-animation">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """

def format_message_timestamp():
    """Return formatted timestamp for messages"""
    return f'<div class="message-timestamp">{datetime.now().strftime("%H:%M")}</div>'

def generate_chat_title(messages):
    """Generate a descriptive title for the chat using AI"""
    try:
        user_messages = [m["content"] for m in messages if m["role"] == "user"][:3]
        if not user_messages:
            return f"Chat - {datetime.now().strftime('%Y-%m-%d')}"
        
        prompt = (
            "Generate a concise title (3-5 words) for this conversation.\n"
            "Focus on the main topic being discussed.\n"
            "Examples:\n"
            "- Python Developer Candidates\n"
            "- Senior Marketing Roles\n"
            "- Technical Screening Questions\n\n"
            "Messages:\n" + "\n".join(f"- {msg}" for msg in user_messages)
        )
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=20
        )
        
        title = response.choices[0].message.content.strip()
        title = re.sub(r'^["\']|["\']$', "", title)
        return title[:40]
        
    except Exception as e:
        st.error(f"Error generating chat title: {e}")
        return f"Chat - {datetime.now().strftime('%Y-%m-%d')}"

def should_rename(chat_key):
    """Determine if a chat should be auto-renamed"""
    if not chat_key.startswith("New Chat"):
        return False
    chat = st.session_state.all_chats[chat_key]
    user_msgs = [m for m in chat if m["role"] == "user"]
    return len(user_msgs) >= 2

def truncate_title(title, max_length=28):
    """Truncate chat title for display"""
    return title if len(title) <= max_length else f"{title[:max_length-3]}..."

# --- Sidebar: Chat Management ---
with st.sidebar:
    st.markdown(f"""
    <div class="flex">
        <i class="gg-bot"></i>
        <h3>HireScope Chat</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # New Chat Button
    if st.button("New Chat", key="new_chat", help="Start a new conversation"):
        new_name = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        st.session_state.all_chats[new_name] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.session_state.is_generating = False
        st.session_state.editing_title = None
        st.rerun()
    
    st.markdown("---")
    
    # Chat List
    if st.session_state.all_chats:
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        
        for name in sorted_chats:
            title = st.session_state.chat_titles.get(name, name)
            display_title = truncate_title(title)
            
            active = name == st.session_state.active_chat
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                if st.button(
                    f"{display_title}", 
                    key=f"select_{name}",
                    help=f"Switch to '{title}'",
                    type="primary" if active else "secondary"
                ):
                    st.session_state.active_chat = name
                    st.session_state.is_generating = False
                    st.session_state.editing_title = None
                    st.rerun()
            
            with col2:
                if st.button(
                    "", 
                    key=f"delete_{name}",
                    help=f"Delete '{title}'"
                ):
                    if name in st.session_state.all_chats:
                        del st.session_state.chat_titles[name]
                        del st.session_state.all_chats[name]
                        if name == st.session_state.active_chat:
                            st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
                        st.session_state.is_generating = False
                        st.session_state.editing_title = None
                        st.rerun()
    
    st.markdown("---")
    
    # Statistics
    st.markdown(f"""
    <div class="flex">
        <i class="gg-push-up"></i>
        <span>Total Chats: <span class="badge">{len(st.session_state.all_chats)}</span></span>
    </div>
    """, unsafe_allow_html=True)
    
    current_chat = st.session_state.all_chats.get(st.session_state.active_chat, [])
    message_count = len([m for m in current_chat if m["role"] != "system"])
    st.markdown(f"""
    <div class="flex">
        <i class="gg-comment"></i>
        <span>Messages: <span class="badge">{message_count}</span></span>
    </div>
    """, unsafe_allow_html=True)

# --- Main Chat Interface ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats.get(chat_key, [SYSTEM_PROMPT])
title = st.session_state.chat_titles.get(chat_key, chat_key)

# Chat Header with Title Editing
col1, col2 = st.columns([1, 0.1])
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
    if st.button("", help="Rename chat"):
        st.session_state.editing_title = chat_key
        st.rerun()

# Title editing interface
if st.session_state.editing_title == chat_key:
    new_title = st.text_input(
        "Edit chat title:", 
        value=title,
        key="title_edit_input",
        label_visibility="collapsed"
    )
    
    if st.button("Save Changes"):
        st.session_state.chat_titles[chat_key] = new_title
        st.session_state.editing_title = None
        st.rerun()

# Display Chat Messages
message_container = st.container()
with message_container:
    if len(chat) <= 1:
        st.markdown("""
        <div class="empty-state">
            <h3><i class="gg-smile"></i> Welcome to HireScope Chat!</h3>
            <p>Ask me anything about the candidates in your database.</p>
            <p><em>Example: "Show me candidates with Python experience" or "Find senior developers with React skills"</em></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in chat[1:]:
            role_class = "user-message" if msg["role"] == "user" else "assistant-message"
            icon = "<i class='gg-user'></i>" if msg["role"] == "user" else "<i class='gg-bot'></i>"
            
            with st.container():
                st.markdown(
                    f'<div class="chat-message {role_class}">'
                    f'<div class="flex">'
                    f'{icon}'
                    f'<span style="font-weight:500;">{"You" if msg["role"] == "user" else "HireScope AI"}</span>'
                    f'</div>'
                    f'<div>{msg["content"]}</div>'
                    f'{format_message_timestamp()}'
                    f'</div>',
                    unsafe_allow_html=True
                )

# Show typing indicator if generating
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)

# Chat Input
query = st.chat_input("Ask about candidates...", disabled=st.session_state.is_generating)

# --- Handle User Query ---
if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    
    # Add user message
    chat.append({"role": "user", "content": query})
    
    # Show user message immediately
    with st.container():
        st.markdown(
            f'<div class="chat-message user-message">'
            f'<div class="flex">'
            f'<i class="gg-user"></i>'
            f'<span style="font-weight:500;">You</span>'
            f'</div>'
            f'<div>{query}</div>'
            f'{format_message_timestamp()}'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Show typing indicator
    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)
    
    # Process query
    try:
        if is_greeting(query):
            reply = "Hello! I'm here to help you find information about candidates. How can I assist you today?"
        else:
            # Check database connection
            try:
                total = collection.count()
            except Exception as e:
                st.error(f"Database connection error: {e}")
                total = 0
            
            if total == 0:
                reply = "I don't have any résumé data available right now. Please make sure the candidate database is properly loaded."
            else:
                # Search for relevant documents
                try:
                    hits = collection.query(
                        query_texts=[query], 
                        n_results=max(1, min(5, total))
                    )
                    docs = hits.get("documents", [[]])[0]
                except Exception as e:
                    st.error(f"Search error: {e}")
                    docs = []
                
                if not docs or all(not d.strip() for d in docs):
                    reply = "I couldn't find any matching résumé information. Try rephrasing your question."
                else:
                    context = "\n\n---\n\n".join(docs)
                    chat[0]["content"] = f"Answer ONLY from these résumé snippets:\n\n{context}"
                    
                    try:
                        resp = openai.chat.completions.create(
                            model="gpt-4o",
                            messages=chat,
                            temperature=0.3,
                            max_tokens=1000
                        )
                        reply = resp.choices[0].message.content.strip()
                    except Exception as e:
                        reply = f"⚠️ Error generating response: {str(e)}"
        
        # Add assistant response
        chat.append({"role": "assistant", "content": reply})
        
        # Auto-rename chat if needed
        if should_rename(chat_key):
            new_title = generate_chat_title(chat)
            st.session_state.chat_titles[chat_key] = new_title
        
        # Show response
        typing_placeholder.empty()
        with st.container():
            st.markdown(
                f'<div class="chat-message assistant-message">'
                f'<div class="flex">'
                f'<i class="gg-bot"></i>'
                f'<span style="font-weight:500;">HireScope AI</span>'
                f'</div>'
                f'<div>{reply}</div>'
                f'{format_message_timestamp()}'
                f'</div>',
                unsafe_allow_html=True
            )
        
    except Exception as e:
        typing_placeholder.empty()
        error_msg = f"An error occurred: {str(e)}"
        chat.append({"role": "assistant", "content": error_msg})
        st.error(error_msg)
    
    finally:
        st.session_state.is_generating = False
        st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("""
<div class="footer">
    <div class="flex" style="justify-content: center; gap: 0.75rem;">
        <i class="gg-terminal"></i>
        <span>HireScope AI - Candidate Search Assistant</span>
    </div>
</div>
""", unsafe_allow_html=True)