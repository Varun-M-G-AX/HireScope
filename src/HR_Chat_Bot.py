import re
import streamlit as st
from datetime import datetime
from utils import collection, openai

st.set_page_config(page_title="💬 HireScope Chat", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

# -------------------
# Session Initialization & State
# -------------------
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
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}

# -------------------
# Helper Functions
# -------------------
def auto_rename_chat(chat_key, chat_history):
    # Only rename if it's still a generic name and the first user message is meaningful
    old_title = st.session_state.chat_titles.get(chat_key, chat_key)
    if old_title.startswith("New Chat"):
        for msg in chat_history:
            if msg["role"] == "user":
                first_line = msg["content"].strip().split("\n")[0]
                if len(first_line) > 7 and not re.match(r"^(hi|hello|hey|thanks)", first_line, re.I):
                    # Cut to 32 chars max, end on word
                    title = first_line[:32]
                    if len(first_line) > 32:
                        title = re.sub(r"\s+\S+$", "", title).strip() + "..."
                    st.session_state.chat_titles[chat_key] = title
                break

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

# -------------------
# SIDEBAR
# -------------------
with st.sidebar:
    st.title("HireScope 💼")
    st.markdown("### Actions")
    if st.button("📝 New chat"):
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
    # st.button("🔍 Search chats", disabled=True)  # Placeholder for future
    
    st.markdown("### Chats")
    chat_names = list(st.session_state.all_chats.keys())
    for cname in chat_names:
        title = st.session_state.chat_titles.get(cname, cname)
        if st.button(title, key=f"sidebar_{cname}"):
            st.session_state.active_chat = cname
            st.experimental_rerun()
    # Delete chat button (not for last chat)
    if len(chat_names) > 1:
        if st.button("🗑️ Delete current chat", key="deletechatbtn"):
            del st.session_state.all_chats[st.session_state.active_chat]
            del st.session_state.chat_titles[st.session_state.active_chat]
            st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
            st.experimental_rerun()

# -------------------
# MAIN CHAT PANEL
# -------------------
active_title = st.session_state.chat_titles.get(st.session_state.active_chat, st.session_state.active_chat)
st.header(active_title)

chat = st.session_state.all_chats[st.session_state.active_chat]

with st.container():
    for msg in chat[1:]:
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**🤖 Assistant:** {msg['content']}")

query = st.chat_input("💬 Ask about candidates…")

# -------------------
# CHAT INPUT & PROCESSING
# -------------------
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