# HireScope Chat App with SVG Icons and Functional Sidebar
import re
import streamlit as st
from datetime import datetime
from utils import collection, openai  # You must provide your own collection and openai setup

# --- SVG Icons (Bootstrap from icons.getbootstrap.com) ---
ROBOT_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='currentColor' class='bi bi-robot' viewBox='0 0 16 16'><path d='M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5'/><path d='M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135'/><path d='M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5'/></svg>"""

# --- Streamlit Config ---
st.set_page_config("HireScope Chat", layout="wide")

# --- Session State Init ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
    new_key = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    st.session_state.chats[new_key] = [{"role": "system", "content": "You are a recruiter assistant."}]
    st.session_state.active = new_key

# --- Sidebar with SVG Icons ---
with st.sidebar:
    st.markdown("## 💬 Chats")
    if st.button("➕ New Chat"):
        title = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.chats[title] = [st.session_state.chats[st.session_state.active][0].copy()]
        st.session_state.active = title
        st.rerun()

    for key in sorted(st.session_state.chats.keys(), reverse=True):
        active_class = "font-weight: bold;" if key == st.session_state.active else ""
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            if st.button(f"{key}", key=f"select_{key}"):
                st.session_state.active = key
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{key}"):
                del st.session_state.chats[key]
                st.session_state.active = next(iter(st.session_state.chats))
                st.rerun()

# --- Main Chat Area ---
st.title("HireScope Chat")
active_key = st.session_state.active
chat = st.session_state.chats[active_key]

for msg in chat[1:]:
    icon = "🧑" if msg['role'] == 'user' else "🤖"
    st.markdown(f"**{icon} {msg['role'].capitalize()}:** {msg['content']}")

prompt = st.chat_input("Ask about candidates...")
if prompt:
    chat.append({"role": "user", "content": prompt})
    try:
        total = collection.count()
        if total == 0:
            reply = "⚠️ No resume data available."
        else:
            hits = collection.query(query_texts=[prompt], n_results=3)
            context = "\n---\n".join(hits.get("documents", [[]])[0])
            chat[0]["content"] = f"Answer ONLY from these résumé snippets:\n\n{context}"
            result = openai.chat.completions.create(
                model="gpt-4o",
                messages=chat,
                temperature=0.3,
                max_tokens=1000
            )
            reply = result.choices[0].message.content
    except Exception as e:
        reply = f"⚠️ Error: {e}"
    chat.append({"role": "assistant", "content": reply})
    st.rerun()
