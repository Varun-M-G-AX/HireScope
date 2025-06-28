import re
import streamlit as st
from datetime import datetime
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
def auto_rename_chat(chat_key):
    if chat_key.startswith("New Chat") and len(st.session_state.all_chats) >= 3:
        chat = st.session_state.all_chats[chat_key]
        for msg in chat:
            if msg["role"] == "user":
                content = msg["content"].strip()
                if len(content) > 12 and not re.match(r"^(hi|hello|hey|thanks)", content, re.I):
                    new_title = re.sub(r"[^\w\s]", "", content.split("\n")[0])[:32]
                    if new_title:
                        st.session_state.chat_titles[chat_key] = new_title.strip()
                    break


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

# --- Sidebar: Chat List ---
with st.sidebar:
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
    auto_rename_chat(chat_key)

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
    auto_rename_chat(chat_key)
    st.rerun()