import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

st.set_page_config(page_title="💬 HireScope Chat", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

# --- CSS inspired by modern chat apps; not a copy, but clean and minimalist
st.markdown("""
<style>
/* Sidebar */
.block-container { padding-top: 0.5rem !important; }
#MainMenu, .stDeployButton {display:none;}
.sidebar-section {
    margin-bottom: 1.7em;
}
.sidebar-title {
    color: #b7b7bd;
    font-weight: 700;
    font-size: 1.05em;
    margin-top: 1.2em;
    margin-bottom: 0.7em;
    letter-spacing: 0.04em;
}
.sidebar-action-btn {
    display: flex;
    align-items: center;
    padding: 0.6em 0.9em;
    border-radius: 0.6em;
    border: none;
    background: transparent;
    color: #e7e7ea;
    font-size: 1.08em;
    margin-bottom: 0.22em;
    width: 100%;
    transition: background 0.12s;
    cursor: pointer;
    gap: 0.7em;
}
.sidebar-action-btn:hover {
    background: #24252b;
    color: #d0d0e0;
}
.sidebar-chat-list {
    margin: 0; padding: 0; list-style: none;
}
.sidebar-chat-item {
    display: flex;
    align-items: center;
    padding: 0.58em 1em;
    border-radius: 0.6em;
    margin-bottom: 0.12em;
    cursor: pointer;
    font-size: 1.05em;
    color: #e7e7ea;
    background: transparent;
    border: none;
    width: 100%;
    text-align: left;
    gap: 0.7em;
    transition: background 0.12s;
    position: relative;
}
.sidebar-chat-item.selected,
.sidebar-chat-item:active {
    background: #3346d3;
    color: #fff;
}
.sidebar-chat-item .dot {
    width: 0.7em;
    height: 0.7em;
    border-radius: 50%;
    background: #3aaed8;
    margin-left: auto;
}
.sidebar-chat-item .delete-btn {
    margin-left: 0.7em;
    color: #e84118;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.1em;
    display: none;
}
.sidebar-chat-item:hover .delete-btn {
    display: inline;
}
.sidebar-chat-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 170px;
    display: inline-block;
    vertical-align: middle;
}
hr.sidebar-divider { border: none; border-top: 1px solid #282b33; margin: 1.1em 0; }
/* Chat Area */
.chat-main-panel {
    display: flex;
    flex-direction: column;
    height: 95vh;
    min-height: 500px;
    max-width: 870px;
    margin: auto;
}
.chat-header {
    font-size: 1.7em;
    font-weight: 700;
    color: #3346d3;
    margin-bottom: 0.7em;
    margin-top: 1.1em;
    letter-spacing: 0.01em;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex-grow: 1;
    max-height: 63vh;
    overflow-y: auto;
    background: #191a1e;
    border-radius: 1.1em;
    padding: 1.3em 1em 1em 1em;
    margin-bottom: 1em;
    box-shadow: 0 2px 12px #0001;
}
.chat-bubble-user {
    background: #3346d3;
    color: #fff;
    padding: 0.78rem 1.1rem;
    border-radius: 1rem 1rem 0 1rem;
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
    align-self: flex-start;
    max-width: 82%;
    font-size: 1.08em;
    box-shadow: 0 2px 12px #0001;
}
.bubble-role {
    display: inline-block;
    vertical-align: top;
    margin-right: 0.65em;
    font-size: 1.15em;
}
.stChatInputContainer { margin-bottom: 0px !important; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
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
    st.session_state.chat_titles = {default_name: "New Chat"}

if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}

# --- AUTO-RENAME LOGIC ---
def auto_rename_chat(chat_key, chat_history):
    # Only rename if it's still a generic name and the first user message is meaningful
    old_title = st.session_state.chat_titles.get(chat_key, chat_key)
    if old_title.startswith("New Chat"):
        for msg in chat_history:
            if msg["role"] == "user":
                first_line = msg["content"].strip().split("\n")[0]
                # Clean: remove greetings, short words, etc.
                if len(first_line) > 7 and not re.match(r"^(hi|hello|hey|thanks)", first_line, re.I):
                    # Cut to 32 chars max, no break in middle of word
                    title = first_line[:32]
                    if len(first_line) > 32:
                        title = re.sub(r"\s+\S+$", "", title).strip() + "..."
                    st.session_state.chat_titles[chat_key] = title
                break

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("![logo](https://em-content.zobj.net/source/microsoft/378/briefcase_1f4bc.png) &nbsp; **HireScope**", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Main actions
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    if st.button("📝  New chat", key="newchatbtn", use_container_width=True):
        name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
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
        st.session_state.chat_titles[name] = "New Chat"
        st.experimental_rerun()
    st.button("🔍  Search chats", use_container_width=True, disabled=True)
    st.button("📚  Library", use_container_width=True, disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Divider
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Chat sessions
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Chats</div>', unsafe_allow_html=True)
    for cname in list(st.session_state.all_chats.keys()):
        title = st.session_state.chat_titles.get(cname, cname)
        selected = "selected" if cname == st.session_state.active_chat else ""
        chat_btn = st.button(
            f"💬  {title}",
            key=f"sidebar_{cname}",
            use_container_width=True,
            help=cname if title != cname else None
        )
        if chat_btn:
            st.session_state.active_chat = cname
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN CHAT PANEL ---
col1, col2, col3 = st.columns([0.13, 1, 0.13])
with col2:
    st.markdown('<div class="chat-main-panel">', unsafe_allow_html=True)

    # Header (always on top)
    active_title = st.session_state.chat_titles.get(st.session_state.active_chat, st.session_state.active_chat)
    st.markdown(f'<div class="chat-header">{active_title}</div>', unsafe_allow_html=True)

    # Chat area (scrollable, doesn't move header)
    chat = st.session_state.all_chats[st.session_state.active_chat]
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in chat[1:]:
        is_user = msg["role"] == "user"
        bubble_class = "chat-bubble-user" if is_user else "chat-bubble-assistant"
        icon = "🧑" if is_user else "🤖"
        st.markdown(
            f'<div class="{bubble_class}"><span class="bubble-role">{icon}</span>{msg["content"]}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input (always at bottom)
    query = st.chat_input("💬 Ask about candidates…")
    st.markdown('</div>', unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
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

# --- CHAT INPUT & PROCESSING ---
total = collection.count()

if query:
    chat.append({"role": "user", "content": query})
    auto_rename_chat(st.session_state.active_chat, chat[1:])  # skip system prompt

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

    chat.append({"role": "assistant", "content": reply})
    auto_rename_chat(st.session_state.active_chat, chat[1:])
    st.experimental_rerun()