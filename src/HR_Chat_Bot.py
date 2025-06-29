import re
import streamlit as st
from datetime import datetime
from streamlit.components.v1 import html
from utils import collection, openai

# --- Page Configuration ---
st.set_page_config(
    page_title="💬 HireScope Chat",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for ChatGPT-like UI ---
st.markdown("""
<style>
:root {
    --primary-bg: #181818;
    --secondary-bg: #242424;
    --user-message-bg: #242424;
    --assistant-message-bg: #e2e2e1;
    --assistant-message-color: #181818;
    --user-message-color: #e2e2e1;
    --border-color: #717576;
    --sidebar-bg: #242424;
    --sidebar-color: #e2e2e1;
    --primary-color: #717576;
    --shadow: 0 4px 20px 0 rgba(0,0,0,.15);
}
body {
    background: var(--primary-bg) !important;
}
section[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    color: var(--sidebar-color) !important;
    min-width:260px !important;
    max-width:320px !important;
    border-right: 1px solid var(--border-color);
}
.st-emotion-cache-1avcm0n {
    background: var(--primary-bg) !important;
}
#MainMenu, header, footer {visibility: hidden;}
/* Chat container styles */
.chatgpt-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 1.5rem 0 0 0;
}
.chatgpt-header {
    font-size: 2rem;
    font-weight: 700;
    color: var(--assistant-message-bg);
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    letter-spacing: -1px;
}
.chatgpt-message-row {
    display: flex;
    gap: 1.2rem;
    margin-bottom: 1.5rem;
}
.chatgpt-message-row.user {
    flex-direction: row-reverse;
}
.chatgpt-avatar {
    width: 44px;
    height: 44px;
    border-radius: 8px;
    background: #232323;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.7rem;
    color: #fff;
    border: 2px solid var(--border-color);
}
.chatgpt-message {
    padding: 1.1rem 1.35rem;
    border-radius: 0.9rem;
    font-size: 1.1rem;
    line-height: 1.6;
    max-width: 82%;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
    white-space: pre-wrap;
    word-break: break-word;
}
.chatgpt-message.user {
    background: var(--user-message-bg);
    color: var(--user-message-color);
    border-bottom-right-radius: 0.25rem;
}
.chatgpt-message.assistant {
    background: var(--assistant-message-bg);
    color: var(--assistant-message-color);
    border-bottom-left-radius: 0.25rem;
}
.chatgpt-timestamp {
    font-size: 0.76rem;
    color: #999;
    margin-top: 0.2em;
    margin-left: 2.6em;
}
.chatgpt-empty {
    text-align:center;
    color:#bdbdbd;
    margin-top:3rem;
    font-size:1.1rem;
    opacity:0.7;
}
.chatgpt-sidebar-title {
    font-size: 1.23rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 1.3rem;
    color: var(--sidebar-color);
    text-align: left;
}
.chatgpt-sidebar-btn, .chatgpt-sidebar-btn-active {
    background: none;
    border: none;
    color: inherit;
    padding: 0.6rem 1rem;
    text-align: left;
    width: 100%;
    font-size: 1rem;
    border-radius: 8px;
    margin-bottom: 0.2rem;
    cursor: pointer;
    transition: background 0.18s;
}
.chatgpt-sidebar-btn:hover {
    background: #292929;
}
.chatgpt-sidebar-btn-active {
    background: #313133;
    color: #e2e2e1;
    font-weight: 700;
}
.chatgpt-sidebar-btn-delete {
    background: #ff7272;
    color: #fff;
    border: none;
    width: 100%;
    border-radius: 8px;
    padding: 0.55rem 1rem;
    font-size: 1rem;
    margin-top: 1rem;
    cursor: pointer;
    transition: background 0.16s;
}
.chatgpt-sidebar-btn-delete:hover {
    background: #e62e2e;
}
.stChatInputContainer input {
    font-size: 1.1rem !important;
    border-radius: 10px !important;
    background: var(--secondary-bg) !important;
    color: var(--user-message-color) !important;
    border: 1.5px solid var(--border-color) !important;
}
.stChatInputContainer button {
    background: var(--primary-color) !important;
    color: var(--assistant-message-bg) !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    font-size: 1.1rem !important;
    border: none !important;
}
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.8rem 1.2rem;
    background: #212121;
    color: #e2e2e1;
    border-radius: 15px;
    width: fit-content;
    margin-left: 0.5rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 2px 8px #0002;
    font-size: 1.02rem;
}
.typing-dots {
    display: flex;
    gap: 0.35rem;
}
.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #717576;
    animation: typingAnimation 1.4s infinite ease-in-out;
}
.typing-dot:nth-child(1) { animation-delay: 0s; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingAnimation {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
    30% { transform: translateY(-7px); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# --- System Prompt ---
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
    new_title = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    st.session_state.active_chat = new_title
    st.session_state.all_chats[new_title] = [SYSTEM_PROMPT]
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# --- Helper Functions ---
def should_rename(chat_key):
    # Auto-rename if first non-greet user message is present and chat is default
    if not chat_key.startswith("New Chat"):
        return False
    chat = st.session_state.all_chats[chat_key]
    user_msgs = [m for m in chat if m["role"] == "user"]
    if not user_msgs:
        return False
    first = user_msgs[0]["content"].strip()
    return len(first) > 10 and not re.match(r"^(hi|hello|hey|thanks)", first, re.I)

def rename_chat(chat_key):
    user_msgs = [m for m in st.session_state.all_chats[chat_key] if m["role"] == "user"]
    if user_msgs:
        first = user_msgs[0]["content"].strip().split("\n")[0]
        new_title = re.sub(r"[^\w\s]", "", first)[:40].strip().title()
        if new_title and len(new_title) > 3:
            st.session_state.chat_titles[chat_key] = new_title

def is_greeting(text):
    return bool(re.fullmatch(r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", text.strip(), re.I))

def show_typing_indicator():
    st.markdown("""
    <div class="typing-indicator">
        <span style="color: #717576; font-weight: 600;">🤖 AI is typing</span>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def truncate_title(title, max_length=32):
    return title if len(title) <= max_length else title[:max_length-3] + "..."

# --- Sidebar: ChatGPT-like Chat List ---
with st.sidebar:
    st.markdown('<div class="chatgpt-sidebar-title">💬 Conversations</div>', unsafe_allow_html=True)
    # New Chat Button
    if st.button("➕ New Chat", key="new_chat", use_container_width=True):
        new_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new_name] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.session_state.is_generating = False
        st.rerun()
    # List chats
    if st.session_state.all_chats:
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        for name in sorted_chats:
            title = st.session_state.chat_titles.get(name, name)
            display_title = truncate_title(title)
            is_active = name == st.session_state.active_chat
            btn_class = "chatgpt-sidebar-btn-active" if is_active else "chatgpt-sidebar-btn"
            if st.button(
                display_title,
                key=f"select_{name}",
                use_container_width=True,
                help=title
            ):
                st.session_state.active_chat = name
                st.session_state.is_generating = False
                st.rerun()
    # Delete Chat Button
    if len(st.session_state.all_chats) > 1:
        if st.button("🗑️ Delete Current Chat", key="delete_chat", use_container_width=True):
            if st.session_state.active_chat in st.session_state.all_chats:
                del st.session_state.chat_titles[st.session_state.active_chat]
                del st.session_state.all_chats[st.session_state.active_chat]
                st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
                st.session_state.is_generating = False
                st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)

# --- Main ChatGPT-like Chat Interface ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats.get(chat_key, [SYSTEM_PROMPT])
title = st.session_state.chat_titles.get(chat_key, chat_key)

st.markdown(f'<div class="chatgpt-header">HireScope Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="chatgpt-container">', unsafe_allow_html=True)

# Display Chat Messages
if len(chat) <= 1:
    st.markdown('<div class="chatgpt-empty">👋 Start a conversation about candidates or résumés.<br><br><em>Example: "Show me Python developers" or "Who has 5+ years of project management?"</em></div>', unsafe_allow_html=True)
else:
    for idx, msg in enumerate(chat[1:]):  # skip system prompt
        role = msg["role"]
        avatar = "🧑" if role == "user" else "🤖"
        msg_class = f"chatgpt-message {role}"
        row_class = f"chatgpt-message-row {role}"
        st.markdown(f"""
        <div class="{row_class}">
            <div class="chatgpt-avatar">{avatar}</div>
            <div>
                <div class="{msg_class}">{msg["content"]}</div>
                <div class="chatgpt-timestamp">{datetime.now().strftime('%H:%M')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Typing indicator
if st.session_state.is_generating:
    st.markdown('<div class="chatgpt-message-row assistant"><div class="chatgpt-avatar">🤖</div><div>', unsafe_allow_html=True)
    show_typing_indicator()
    st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Chat Input
query = st.chat_input("Type your message here and hit Enter...", disabled=st.session_state.is_generating)

# --- Handle User Query ---
if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    chat.append({"role": "user", "content": query})
    # Auto-rename chat if needed
    if should_rename(chat_key):
        rename_chat(chat_key)
    # Show user message immediately
    st.experimental_rerun()  # Show message + typing indicator instantly
    # Now process the query "in the background" (Streamlit rerun)
    # On next rerun, process the pending message and output
    # This ensures the UI is responsive

if st.session_state.is_generating and chat[-1]["role"] == "user":
    user_msg = chat[-1]["content"]
    try:
        if is_greeting(user_msg):
            reply = "Hello! 👋 I'm here to help you find information about candidates. How can I assist you today?"
        else:
            try:
                total = collection.count()
            except Exception as e:
                reply = f"⚠️ Database connection error: {e}"
                total = 0
            if total == 0:
                reply = "I don't have any résumé data available right now. Please make sure the candidate database is properly loaded."
            else:
                try:
                    hits = collection.query(
                        query_texts=[user_msg], 
                        n_results=max(1, min(5, total))
                    )
                    docs = hits.get("documents", [[]])[0]
                except Exception as e:
                    docs = []
                    reply = f"⚠️ Search error: {e}"
                if not docs or all(not d.strip() for d in docs):
                    reply = "I couldn't find any résumé information that matches your query. Try rephrasing your question or asking about different qualifications."
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
                        reply = f"⚠️ I'm having trouble generating a response right now. Please try again. Error: {str(e)}"
        chat.append({"role": "assistant", "content": reply})
    except Exception as e:
        error_msg = f"⚠️ An unexpected error occurred: {str(e)}"
        chat.append({"role": "assistant", "content": error_msg})
    finally:
        st.session_state.is_generating = False
        st.experimental_rerun()

# --- Footer ---
st.markdown("""
<div style="text-align: center; color: #bdbdbd; font-size: 0.98em; padding: 1.5rem 0 0 0;">
    <hr style="border-color: #313133;">
    <p>🤖 <b>HireScope Chat</b> — AI-powered candidate search and analysis</p>
    <p><em>Ask about candidates, skills, experience, and qualifications</em></p>
</div>
""", unsafe_allow_html=True)