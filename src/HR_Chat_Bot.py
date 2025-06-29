import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

# --- Page Configuration ---
st.set_page_config(
    page_title="💬 HireScope Chat",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SVG Avatars (Bootstrap Icons, theme aware) ---
ROBOT_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor"
class="bi bi-robot" viewBox="0 0 16 16">
  <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/>
  <path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/>
</svg>
"""
HUMAN_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor"
class="bi bi-person-square" viewBox="0 0 16 16">
  <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0"/>
  <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm12 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1v-1c0-1-1-4-6-4s-6 3-6 4v1a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/>
</svg>
"""

# --- CSS Styling: Theme-adaptive using Streamlit variables ---
st.markdown("""
<style>
body { background: var(--background-color) !important; }
.chatgpt-header {
    font-size: 2.1rem;
    font-weight: 800;
    text-align: center;
    opacity: 0.7;
    margin-top: 2rem;
    margin-bottom: 2.3rem;
    letter-spacing: -1px;
}
.chatgpt-container { max-width: 720px; margin: 0 auto; }
.message-row {
    display: flex; align-items: flex-end; margin-bottom: 1.5rem; width: 100%;
}
.message-row.user { flex-direction: row-reverse; }
.avatar {
    min-width: 44px; min-height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    margin-left: 12px; margin-right: 12px;
    background: var(--secondary-background-color, #e2e2e1);
    box-shadow: 0 2px 12px #0002;
}
.avatar.bot { background: var(--secondary-background-color, #717576); }
.avatar.user { background: var(--secondary-background-color, #e2e2e1); }
.avatar svg { display: block; margin: auto; }
.bubble {
    border-radius: 1.08rem; box-shadow: 0 2px 12px #0001;
    padding: 1.15rem 1.35rem; font-size: 1.11rem; line-height: 1.7;
    min-width: 90px; max-width: 80vw; width: 100%;
    border: 1.4px solid var(--secondary-background-color, #e2e2e1);
    background: var(--secondary-background-color, #e2e2e1);
    color: var(--text-color, #181818);
    word-break: break-word;
}
.bubble.user {
    background: var(--primary-color, #242424);
    color: var(--text-color, #e2e2e1);
    border-top-right-radius: 0.5rem;
    margin-left: auto; margin-right: 0;
}
.bubble.bot {
    background: var(--secondary-background-color, #e2e2e1);
    color: var(--text-color, #181818);
    border-top-left-radius: 0.5rem;
    margin-right: auto; margin-left: 0;
}
.timestamp {
    font-size: 0.8rem; color: #969696; margin: 0.2em 0.4em; text-align: right;
}
.typing-indicator {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.8rem 1.2rem; background: #ededed;
    color: #717576;
    border-radius: 15px; width: fit-content; margin-left: 0.5rem; margin-bottom: 1.1rem;
    box-shadow: 0 2px 8px #0002; font-size: 1.02rem;
}
.typing-dots { display: flex; gap: 0.35rem; }
.typing-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #717576; animation: typingAnimation 1.4s infinite ease-in-out;
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

def should_rename(chat_key):
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
        <span style="font-weight:600;">🤖 AI is typing</span>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def truncate_title(title, max_length=32):
    return title if len(title) <= max_length else title[:max_length-3] + "..."

# --- Sidebar: Chat List ---
with st.sidebar:
    st.markdown('### 💬 Chats')
    if st.button("➕ New Chat", key="new_chat", use_container_width=True):
        new_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new_name] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.session_state.is_generating = False
        st.rerun()
    if st.session_state.all_chats:
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        for name in sorted_chats:
            title = st.session_state.chat_titles.get(name, name)
            display_title = truncate_title(title)
            is_active = name == st.session_state.active_chat
            if st.button(
                display_title,
                key=f"select_{name}",
                use_container_width=True,
                help=title
            ):
                st.session_state.active_chat = name
                st.session_state.is_generating = False
                st.rerun()
    if len(st.session_state.all_chats) > 1:
        if st.button("🗑️ Delete Current Chat", key="delete_chat", use_container_width=True):
            if st.session_state.active_chat in st.session_state.all_chats:
                del st.session_state.chat_titles[st.session_state.active_chat]
                del st.session_state.all_chats[st.session_state.active_chat]
                st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
                st.session_state.is_generating = False
                st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)

# --- Main UI ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats.get(chat_key, [SYSTEM_PROMPT])
title = st.session_state.chat_titles.get(chat_key, chat_key)

st.markdown('<div class="chatgpt-header">HireScope Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="chatgpt-container">', unsafe_allow_html=True)

if len(chat) <= 1:
    st.markdown('<div class="chatgpt-empty">👋 Start a conversation about candidates or résumés.<br><br><em>Example: "Show me Python developers" or "Who has 5+ years of project management?"</em></div>', unsafe_allow_html=True)
else:
    for idx, msg in enumerate(chat[1:]):
        role = msg["role"]
        avatar = ROBOT_SVG if role == "assistant" else HUMAN_SVG
        msg_class = f"bubble {role}"
        row_class = f"message-row {role}"
        st.markdown(f"""
        <div class="{row_class}">
            <div class="avatar {role}">{avatar}</div>
            <div style="flex:1;">
                <div class="{msg_class}">{msg["content"]}</div>
                <div class="timestamp">{datetime.now().strftime('%H:%M')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if st.session_state.is_generating:
    st.markdown(f'<div class="message-row assistant"><div class="avatar assistant">{ROBOT_SVG}</div><div>', unsafe_allow_html=True)
    show_typing_indicator()
    st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

query = st.chat_input("Type your message here and hit Enter...", disabled=st.session_state.is_generating)

if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    chat.append({"role": "user", "content": query})
    if should_rename(chat_key):
        rename_chat(chat_key)
    st.rerun()

if st.session_state.is_generating and chat[-1]["role"] == "user":
    user_msg = chat[-1]["content"]
    try:
        if is_greeting(user_msg):
            reply = "Hello! How can I assist you today?"
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
        st.rerun()

st.markdown("""
<div style="text-align: center; color: #bdbdbd; font-size: 0.98em; padding: 1.5rem 0 0 0;">
    <hr style="border-color: #313133;">
    <p>🤖 <b>HireScope Chat</b> — AI-powered candidate search and analysis</p>
    <p><em>Ask about candidates, skills, experience, and qualifications</em></p>
</div>
""", unsafe_allow_html=True)