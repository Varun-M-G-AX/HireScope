import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

# --- SVG Avatars & Icons (Bootstrap) ---
ROBOT_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor"
class="bi bi-robot" viewBox="0 0 16 16"><path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135"/><path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5"/></svg>
"""
EDIT_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
  <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
  <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5z"/>
</svg>
"""
SAVE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
  <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
</svg>
"""
CANCEL_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293z"/>
</svg>
"""
DELETE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash-fill" viewBox="0 0 16 16">
  <path d="M2.5 1a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1H3v9a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V4h.5a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H10a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1zm3 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5M8 5a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7A.5.5 0 0 1 8 5m3 .5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 1 0"/>
</svg>
"""

# --- Sidebar CSS for hover/rename ---
st.markdown("""
<style>
.sidebar-chat-row {
    display: flex; align-items: center; gap: 0.4rem;
    margin-bottom: 0.3rem; padding: 0.2rem 0.1rem 0.2rem 0.2rem;
    border-radius: 7px;
    transition: background .18s;
    position: relative;
}
.sidebar-chat-row.active {
    background: rgba(113,117,118,0.09);
}
.sidebar-chat-avatar {
    min-width: 22px; min-height: 22px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    background: var(--secondary-background-color, #e2e2e1);
}
.sidebar-chat-avatar svg { width: 19px; height: 19px; color: var(--text-color, #181818);}
.sidebar-chat-title {
    flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-size: 1rem; cursor: pointer;
}
.sidebar-chat-title-active { font-weight: 700; color: var(--primary-color, #242424);}
.sidebar-rename-btn {
    display: none;
    background: none;
    border: none;
    padding: 0 3px;
    margin: 0 2px 0 0;
    cursor: pointer;
    vertical-align: middle;
}
.sidebar-chat-row:hover .sidebar-rename-btn {
    display: inline-block;
}
.sidebar-rename-input {
    width: 70%; border-radius: 6px; padding: 2px 8px;
    border: 1.2px solid var(--primary-color, #242424);
    font-size: 1rem; margin-right: 0.3rem;
}
.sidebar-save-btn, .sidebar-cancel-btn {
    background: none; border: none; padding: 0 1px; margin: 0 1px;
    cursor: pointer; vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

# --- Session Initialization ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "active_chat" not in st.session_state:
    new_title = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    st.session_state.active_chat = new_title
    st.session_state.all_chats[new_title] = [{
        "role": "system",
        "content": (
            "You are a recruiting assistant. "
            "Answer ONLY from résumé snippets provided in context. "
            "If the query is unrelated to candidates or résumés, say: "
            "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
        )
    }]
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "editing_title" not in st.session_state:
    st.session_state.editing_title = None

def truncate_title(title, max_length=24):
    return title if len(title) <= max_length else title[:max_length-3] + "..."

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

# --- Sidebar: Chat List with Hover Rename Option ---
with st.sidebar:
    st.markdown('### 💬 Chats')
    if st.button("➕ New Chat", key="new_chat", use_container_width=True):
        new_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new_name] = [st.session_state.all_chats[list(st.session_state.all_chats.keys())[0]][0].copy()]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.session_state.is_generating = False
        st.session_state.editing_title = None
        st.rerun()

    if st.session_state.all_chats:
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        for name in sorted_chats:
            is_active = name == st.session_state.active_chat
            display_title = st.session_state.chat_titles.get(name, name)
            row_class = "sidebar-chat-row active" if is_active else "sidebar-chat-row"
            with st.container():
                st.markdown(f"""<div class="{row_class}">""", unsafe_allow_html=True)
                st.markdown(
                    f"""<div class="sidebar-chat-avatar">{ROBOT_SVG}</div>""",
                    unsafe_allow_html=True
                )
                # Rename UI
                if st.session_state.editing_title == name:
                    new_title_val = st.text_input(
                        "", value=display_title, key=f"rename_{name}",
                        label_visibility="collapsed",
                        max_chars=40,
                        placeholder="Edit chat title"
                    )
                    colsave, colcancel = st.columns([1,1])
                    with colsave:
                        if st.button(SAVE_SVG, key=f"save_{name}", help="Save", use_container_width=True):
                            st.session_state.chat_titles[name] = new_title_val
                            st.session_state.editing_title = None
                            st.rerun()
                    with colcancel:
                        if st.button(CANCEL_SVG, key=f"cancel_{name}", help="Cancel", use_container_width=True):
                            st.session_state.editing_title = None
                            st.rerun()
                else:
                    # Title label with hover/click to rename
                    if st.button(truncate_title(display_title), key=f"select_{name}", use_container_width=True):
                        st.session_state.active_chat = name
                        st.session_state.is_generating = False
                        st.session_state.editing_title = None
                        st.rerun()
                    # Edit icon shown only on hover (CSS)
                    rename_btn_key = f"edit_{name}"
                    if st.button(EDIT_SVG, key=rename_btn_key, help="Rename chat", use_container_width=False):
                        st.session_state.editing_title = name
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    if len(st.session_state.all_chats) > 1:
        coldel, colbtn = st.columns([0.15,0.85])
        with coldel:
            st.markdown(f'<span class="sidebar-chat-avatar">{DELETE_SVG}</span>', unsafe_allow_html=True)
        with colbtn:
            if st.button("Delete Current Chat", key="delete_chat", use_container_width=True):
                if st.session_state.active_chat in st.session_state.all_chats:
                    del st.session_state.chat_titles[st.session_state.active_chat]
                    del st.session_state.all_chats[st.session_state.active_chat]
                    st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
                    st.session_state.is_generating = False
                    st.session_state.editing_title = None
                    st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)

# ----------- MAIN UI (chat bubbles not repeated here for brevity, use your prior code) -----------
# ... (rest of the chat UI, unchanged)