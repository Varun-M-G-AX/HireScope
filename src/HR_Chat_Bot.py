import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

# --- Theme Setup ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "light"

with st.sidebar:
    st.markdown("### 🖼️ Appearance")
    theme_options = {"Light": "light", "Dark": "dark"}
    chosen = st.radio(
        "Choose theme", 
        list(theme_options.keys()), 
        horizontal=True, 
        index=0 if st.session_state.theme_mode == "light" else 1
    )
    st.session_state.theme_mode = theme_options[chosen]

THEME = st.session_state.theme_mode

# --- Custom CSS with toggleable dark/light mode ---
css_light = """
<link href='https://css.gg/icons/css/bot.css' rel='stylesheet'>
<link href='https://css.gg/icons/css/profile.css' rel='stylesheet'>
<style>
body { background: #f3f3f3 !important; }
.chatgpt-header {
    font-size: 2.2rem; font-weight: 800; color: #bdbdbd;
    text-align: center; margin-top:1.7rem; margin-bottom:3rem; letter-spacing:-1px;
}
.chatgpt-container { max-width: 760px; margin: 0 auto; }
.message-row {
    display: flex; align-items: flex-end; margin-bottom: 1.7rem; width: 100%;
}
.message-row.user { flex-direction: row-reverse; }
.avatar {
    width: 44px; height: 44px; border-radius: 10px; background: #e2e2e1; 
    display: flex; align-items: center; justify-content: center;
    font-size: 1.7rem; margin-left: 16px; margin-right: 16px; box-shadow: 0 2px 12px #0001;
}
.avatar.bot { background: #717576; color: #fff; }
.avatar.user { background: #e2e2e1; color: #242424; }
.bubble {
    border-radius: 1.1rem; box-shadow: 0 2px 12px #0001;
    padding: 1.2rem 1.35rem; font-size: 1.13rem; line-height: 1.7;
    min-width: 90px; max-width: 82vw; width: 100%; display: inline-block;
    border: 1.5px solid #ddd;
}
.bubble.user {
    background: #242424; color: #e2e2e1; border-top-right-radius: 0.5rem;
    margin-left: auto; margin-right: 0;
}
.bubble.bot {
    background: #e2e2e1; color: #181818; border-top-left-radius: 0.5rem;
    margin-right: auto; margin-left: 0;
}
.timestamp {
    font-size: 0.8rem; color: #969696; margin: 0.2em 0.4em;
    text-align: right;
}
.typing-indicator {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.8rem 1.2rem; background: #ededed; color: #717576;
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
"""

css_dark = """
<link href='https://css.gg/icons/css/bot.css' rel='stylesheet'>
<link href='https://css.gg/icons/css/profile.css' rel='stylesheet'>
<style>
body { background: #181818 !important; }
.chatgpt-header {
    font-size: 2.2rem; font-weight: 800; color: #717576;
    text-align: center; margin-top:1.7rem; margin-bottom:3rem; letter-spacing:-1px;
}
.chatgpt-container { max-width: 760px; margin: 0 auto; }
.message-row {
    display: flex; align-items: flex-end; margin-bottom: 1.7rem; width: 100%;
}
.message-row.user { flex-direction: row-reverse; }
.avatar {
    width: 44px; height: 44px; border-radius: 10px; background: #313133;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.7rem; margin-left: 16px; margin-right: 16px; box-shadow: 0 3px 18px #0006;
}
.avatar.bot { background: #717576; color: #fff; }
.avatar.user { background: #242424; color: #e2e2e1; }
.bubble {
    border-radius: 1.1rem; box-shadow: 0 3px 18px #0005;
    padding: 1.2rem 1.35rem; font-size: 1.13rem; line-height: 1.7;
    min-width: 90px; max-width: 82vw; width: 100%; display: inline-block;
    border: 1.5px solid #313133;
}
.bubble.user {
    background: #242424; color: #e2e2e1; border-top-right-radius: 0.5rem;
    margin-left: auto; margin-right: 0;
}
.bubble.bot {
    background: #e2e2e1; color: #181818; border-top-left-radius: 0.5rem;
    margin-right: auto; margin-left: 0;
}
.timestamp {
    font-size: 0.8rem; color: #717576; margin: 0.2em 0.4em;
    text-align: right;
}
.typing-indicator {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.8rem 1.2rem; background: #232323; color: #e2e2e1;
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
"""

st.markdown(css_light if THEME == "light" else css_dark, unsafe_allow_html=True)

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
            btn_style = "font-weight:700;" if is_active else ""
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
        # Use css.gg icons
        avatar = '<i class="gg-bot"></i>' if role == "assistant" else '<i class="gg-profile"></i>'
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
    st.markdown('<div class="message-row assistant"><div class="avatar assistant"><i class="gg-bot"></i></div><div>', unsafe_allow_html=True)
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
        st.rerun()

st.markdown("""
<div style="text-align: center; color: #bdbdbd; font-size: 0.98em; padding: 1.5rem 0 0 0;">
    <hr style="border-color: #313133;">
    <p>🤖 <b>HireScope Chat</b> — AI-powered candidate search and analysis</p>
    <p><em>Ask about candidates, skills, experience, and qualifications</em></p>
</div>
""", unsafe_allow_html=True)