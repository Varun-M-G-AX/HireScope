import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

st.set_page_config(page_title="💬 HireScope Chat", page_icon="💼", layout="wide")

# ────────────────────────────────
# CSS – ChatGPT-Like Experience
# ────────────────────────────────
st.markdown("""
<style>
.chat-bubble-user {
    background: var(--primary-color);
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 1rem 1rem 0 1rem;
    margin-bottom: 0.5rem;
    align-self: flex-end;
    max-width: 80%;
}
.chat-bubble-assistant {
    background: #f1f3f5;
    color: black;
    padding: 0.75rem 1rem;
    border-radius: 1rem 1rem 1rem 0;
    margin-bottom: 0.5rem;
    align-self: flex-start;
    max-width: 80%;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 1rem;
}
.sidebar-title {
    font-weight: bold;
    font-size: 1.1rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────
# Title
# ────────────────────────────────
st.title("💬 HireScope Chat Assistant")

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

chat = st.session_state.all_chats[st.session_state.active_chat]

# ────────────────────────────────
# Sidebar – Chat Controls
# ────────────────────────────────
st.sidebar.markdown("## 💼 Chats")
current = st.session_state.active_chat
new_name = st.sidebar.text_input("📝 Rename chat", value=current)
if new_name and new_name.strip() != current and new_name not in st.session_state.all_chats:
    st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(current)
    st.session_state.active_chat = new_name

chat_names = list(st.session_state.all_chats.keys())
selected = st.sidebar.selectbox("📂 Switch Chat", options=chat_names, index=chat_names.index(st.session_state.active_chat))
if selected != st.session_state.active_chat:
    st.session_state.active_chat = selected

if st.sidebar.button("➕ New Chat"):
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

chat = st.session_state.all_chats[st.session_state.active_chat]

# ────────────────────────────────
# Chat Message Renderer
# ────────────────────────────────
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in chat[1:]:
        bubble_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-assistant"
        st.markdown(f'<div class="{bubble_class}">{msg["content"]}</div>', unsafe_allow_html=True)
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