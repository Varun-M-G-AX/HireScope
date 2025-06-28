import re
import streamlit as st
from datetime import datetime
from streamlit.components.v1 import html
from utils import collection, openai

st.set_page_config(
    page_title="💬 HireScope Chat",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    new_title = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    st.session_state.active_chat = new_title
    st.session_state.all_chats[new_title] = [SYSTEM_PROMPT]
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}

# --- Helpers ---
def should_rename(chat_key):
    if not chat_key.startswith("New Chat"):
        return False
    if len(st.session_state.all_chats) < 3:
        return False
    chat = st.session_state.all_chats[chat_key]
    user_msgs = [m for m in chat if m["role"] == "user"]
    if len(user_msgs) < 2:
        return False
    first = user_msgs[0]["content"].strip()
    return len(first) > 12 and not re.match(r"^(hi|hello|hey|thanks)", first, re.I)

def rename_chat(chat_key):
    user_msgs = [m for m in st.session_state.all_chats[chat_key] if m["role"] == "user"]
    if user_msgs:
        first = user_msgs[0]["content"].strip().split("\n")[0]
        new_title = re.sub(r"[^\w\s]", "", first)[:32].strip().title()
        if new_title:
            st.session_state.chat_titles[chat_key] = new_title

def is_greeting(text):
    return bool(re.fullmatch(r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", text.strip(), re.I))

def is_recruitment_query(query):
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
    except:
        return False

def show_typing_loader():
    html("""
    <style>
    .dots {
        font-size: 20px;
        letter-spacing: 3px;
        display: inline-block;
        animation: blink 1.5s infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 0.2; }
        50% { opacity: 1; }
    }
    </style>
    <div class="dots">🤖 Typing<span>.</span><span>.</span><span>.</span></div>
    """, height=40)

# --- Sidebar: Chat List ---
with st.sidebar:
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
            overflow-y: auto;
            max-height: 90vh;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("## 💬 Chats")
    if st.button("➕ Start New Chat"):
        new_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new_name] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.rerun()

    for name in list(st.session_state.all_chats):
        title = st.session_state.chat_titles.get(name, name)
        if st.button(title, key=f"select_{name}"):
            st.session_state.active_chat = name
            st.rerun()

    if len(st.session_state.all_chats) > 1:
        if st.button("🗑️ Delete This Chat"):
            del st.session_state.chat_titles[st.session_state.active_chat]
            del st.session_state.all_chats[st.session_state.active_chat]
            st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
            st.rerun()

# --- Main Chat Area ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats[chat_key]
title = st.session_state.chat_titles.get(chat_key, chat_key)

with st.container():
    st.markdown(f"""
        <div style='padding: 1rem; background: linear-gradient(to right, #4e54c8, #8f94fb); border-radius: 12px; margin-bottom: 1rem;'>
            <h2 style='color: white; margin: 0;'>{title}</h2>
        </div>
    """, unsafe_allow_html=True)

    for msg in chat[1:]:
        st.chat_message(msg["role"]).markdown(msg["content"])

    query = st.chat_input("Ask a question about candidates…")

# --- Handle Query ---
if query:
    chat.append({"role": "user", "content": query})

    if should_rename(chat_key):
        rename_chat(chat_key)

    with st.chat_message("assistant"):
        show_typing_loader()

    if is_greeting(query):
        reply = "You're welcome! How can I assist you with candidate information?"
    else:
        total = collection.count()
        relevant = is_recruitment_query(query)
        hits = collection.query(query_texts=[query], n_results=max(1, min(5, total)))
        docs = hits.get("documents", [[]])[0]

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
    st.rerun()