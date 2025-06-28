import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

st.set_page_config(page_title="💬 HireScope Chat", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

# ────────────────────────────────
# CSS – ChatGPT-Like Sidebar and Chat
# ────────────────────────────────
st.markdown("""
<style>
/* Sidebar */
.css-1l02zno {width: 320px !important; min-width: 260px;}
.sidebar-chat-list {
    margin-top: 1.2rem;
    padding: 0;
    list-style: none;
}
.sidebar-chat-item {
    padding: 0.85em 1em;
    border-radius: 0.7em;
    margin-bottom: 0.4em;
    cursor: pointer;
    font-size: 1.06em;
    display: flex;
    align-items: center;
    background: #181c25;
    transition: background 0.12s;
    border: 1.2px solid transparent;
}
.sidebar-chat-item.selected, .sidebar-chat-item:hover {
    background: #212738;
    border-color: #7a8cff;
    color: #7a8cff;
}
.sidebar-chat-item .icon {
    margin-right: 0.7em;
    font-size: 1.2em;
}
.sidebar-footer {
    margin-top: 2.7em;
    text-align: center;
}
.sidebar-newchat-btn {
    width: 100%;
    font-weight: 500;
    padding: 0.6em 0;
    border-radius: 0.6em;
    background: #3346d3;
    color: #fff;
    border: none;
    font-size: 1.1em;
    margin-top: 0.5em;
    transition: background 0.14s;
}
.sidebar-newchat-btn:hover {
    background: #202b80;
    color: #fff;
}
/* Chat Bubbles */
.chat-bubble-user {
    background: #3346d3;
    color: #fff;
    padding: 0.78rem 1.1rem;
    border-radius: 1rem 1rem 0 1rem;
    margin-bottom: 0.5rem;
    align-self: flex-end;
    max-width: 82%;
    font-size: 1.08em;
    box-shadow: 0 2px 12px #0001;
}
.chat-bubble-assistant {
    background: #f1f3f5;
    color: #181c25;
    padding: 0.78rem 1.1rem;
    border-radius: 1rem 1rem 1rem 0;
    margin-bottom: 0.5rem;
    align-self: flex-start;
    max-width: 82%;
    font-size: 1.08em;
    box-shadow: 0 2px 12px #0001;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 1rem;
    min-height: 60vh;
}
.bubble-role {
    display: inline-block;
    vertical-align: top;
    margin-right: 0.65em;
    font-size: 1.15em;
}
.rename-box {
    margin-bottom: 1em;
    text-align: left;
}
.delete-chat-btn {
    padding: 0.18em 0.6em;
    border-radius: 0.5em;
    background: #e84118;
    color: #fff;
    font-size: 0.95em;
    border: none;
    margin-left: 0.5em;
    margin-top: -2px;
}
.delete-chat-btn:hover {
    background: #c23616;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────
# Session Initialization
# ────────────────────────────────
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if "active_chat" not in st.session_state:
    default_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    st.session_state.active_chat = default_name
    st.session_state.all_chats[default_name] = [{
        "role": "system",
        "content": (
            "You are a recruiting assistant. "
            "Answer ONLY from résumé snippets provided in context. "
            "If the query is unrelated to candidates or résumés, say: "
            "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
        )
    }]

# Utility to create unique chat names
def get_new_chat_name():
    base = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    n = 1
    name = base
    while name in st.session_state.all_chats:
        n += 1
        name = f"{base} ({n})"
    return name

# ────────────────────────────────
# Sidebar – ChatGPT-Style
# ────────────────────────────────
with st.sidebar:
    st.markdown("### 💼 Chats")

    chat_names = list(st.session_state.all_chats.keys())
    active = st.session_state.active_chat

    # Chat List
    for cname in chat_names:
        selected = ("selected" if cname == active else "")
        icon = "💬" if cname.startswith("New Chat") else "🗂️"
        if st.button(f"{icon}  {cname}", key=f"sidebar_{cname}", use_container_width=True):
            st.session_state.active_chat = cname

    # Rename and Delete current chat
    st.markdown('<div class="rename-box">', unsafe_allow_html=True)
    new_name = st.text_input("📝 Rename chat", value=active, key="renamebox")
    if new_name and new_name.strip() != active and new_name not in st.session_state.all_chats:
        st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(active)
        st.session_state.active_chat = new_name
        active = new_name
    if len(chat_names) > 1:
        if st.button("🗑️ Delete chat", key="deletechatbtn", help="Delete this chat session permanently"):
            del st.session_state.all_chats[active]
            st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
    st.markdown('</div>', unsafe_allow_html=True)

    # New Chat button at sidebar bottom
    st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
    if st.button("➕ New Chat", key="newchatbtn", help="Start a new chat session"):
        name = get_new_chat_name()
        st.session_state.active_chat = name
        st.session_state.all_chats[name] = [{
            "role": "system",
            "content": (
                "You are a recruiting assistant. "
                "Answer ONLY from résumé snippets provided in context. "
                "If the query is unrelated to candidates or résumés, say: "
                "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
            )
        }]
    st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────
# Main Chat Area
# ────────────────────────────────
st.title("💬 HireScope Chat Assistant")

chat = st.session_state.all_chats[st.session_state.active_chat]
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in chat[1:]:
        is_user = msg["role"] == "user"
        bubble_class = "chat-bubble-user" if is_user else "chat-bubble-assistant"
        icon = "🧑" if is_user else "🤖"
        st.markdown(f'<div class="{bubble_class}"><span class="bubble-role">{icon}</span>{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────
# Helper Functions
# ────────────────────────────────
def is_greeting(text: str) -> bool:
    return bool(re.fullmatch(
        r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*",
        text.strip(), re.I
    ))

def is_recruitment_query(query: str) -> bool:
    prompt = (
        "Respond ONLY with 'Yes' or 'No'. Does this query relate to candidates, "
        "resumes, recruiting, jobs or HR?\n"
        f"Query: \"{query}\""
    )
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return resp.choices[0].message.content.strip().lower().startswith("yes")
    except Exception:
        return False

# ────────────────────────────────
# Chat Input & Processing
# ────────────────────────────────
query = st.chat_input("💬 Ask about candidates…")
total = collection.count()

if query:
    st.chat_message("user").markdown(query)
    chat.append({"role": "user", "content": query})

    if is_greeting(query):
        reply = "You're welcome! How can I assist you with candidate information?"
    else:
        relevant = is_recruitment_query(query)
        hits = collection.query(query_texts=[query], n_results=max(1, min(5, total)))
        docs = hits["documents"][0] if hits["documents"] else []

        if docs and any(d.strip() for d in docs):
            relevant = True

        if not relevant:
            reply = "Sorry, I can only answer questions about candidates based on the résumé snippets provided."
        elif not docs or all(not d.strip() for d in docs):
            reply = "I’m sorry, I don’t have résumé data that answers that."
        else:
            context = "\n\n---\n\n".join(docs)
            chat[0]["content"] = f"Answer ONLY from these résumé snippets:\n\n{context}"
            try:
                resp = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=chat
                )
                reply = resp.choices[0].message.content.strip()
            except Exception as e:
                reply = f"⚠️ Error generating response: {e}"

    st.chat_message("assistant").markdown(reply)
    chat.append({"role": "assistant", "content": reply})