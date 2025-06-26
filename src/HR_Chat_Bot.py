import re, streamlit as st
from datetime import datetime
from utils import collection, openai

st.set_page_config(page_title="Chat with Résumés", page_icon="💬")

st.title("💬 HireScope Chat Space")

# ──────────────────────────────────────────────────────────────
# Chat session management
# ──────────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────────
# Sidebar for chat session selection + rename
# ──────────────────────────────────────────────────────────────

st.sidebar.subheader("💬 Chat Sessions")

# Rename current chat
new_name = st.sidebar.text_input("📝 Rename this chat", value=st.session_state.active_chat)
if new_name != st.session_state.active_chat:
    st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(st.session_state.active_chat)
    st.session_state.active_chat = new_name

# Select existing chat
selected = st.sidebar.selectbox("📂 Select Chat", list(st.session_state.all_chats.keys()), index=list(st.session_state.all_chats.keys()).index(st.session_state.active_chat))
if selected != st.session_state.active_chat:
    st.session_state.active_chat = selected

# Create new chat
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

# ──────────────────────────────────────────────────────────────
# Display chat history
# ──────────────────────────────────────────────────────────────

for msg in chat[1:]:  # skip system message
    st.chat_message(msg["role"]).markdown(msg["content"])

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def is_greeting(text: str) -> bool:
    return bool(re.fullmatch(r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", text.strip(), re.I))

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

# ──────────────────────────────────────────────────────────────
# Input prompt
# ──────────────────────────────────────────────────────────────

total = collection.count()
query = st.chat_input("Ask anything about candidates…")
if query:
    st.chat_message("user").markdown(query)
    chat.append({"role": "user", "content": query})

    if is_greeting(query):
        reply = "You're welcome! How can I assist you with candidate information?"
    else:
        relevant = is_recruitment_query(query)
        hits = collection.query(query_texts=[query], n_results=min(5, total))
        docs = hits["documents"][0]

        if docs and any(d.strip() for d in docs):
            relevant = True

        if not relevant:
            reply = "Sorry, I can only answer questions about candidates based on the résumé snippets provided."
        elif not docs or all(not d.strip() for d in docs):
            reply = "I’m sorry, I don’t have résumé data that answers that."
        else:
            context = "\n\n---\n\n".join(docs)
            chat[0]["content"] = (
                "Answer ONLY from these résumé snippets:\n\n" + context
            )
            resp = openai.chat.completions.create(
                model="gpt-4o",
                messages=chat
            )
            reply = resp.choices[0].message.content.strip()

    st.chat_message("assistant").markdown(reply)
    chat.append({"role": "assistant", "content": reply})
