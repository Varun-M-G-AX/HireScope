import re
import streamlit as st
from datetime import datetime
import time
from typing import Dict, List, Any

# --- Optional: Replace with actual implementations ---
try:
    from openai import OpenAI
    from utils import collection  # Your database collection utility
except ImportError:
    class MockOpenAI:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return type('obj', (object,), {
                        'choices': [type('obj', (object,), {
                            'message': type('obj', (object,), {
                                'content': "Mock response - replace with OpenAI implementation"
                            })
                        })]
                    })
    openai = MockOpenAI()
    collection = type('obj', (object,), {
        'count': lambda: 5,
        'query': lambda **kwargs: {'documents': [["Resume snippet 1", "Resume snippet 2"]]}
    })

# --- Streamlit Config ---
st.set_page_config(
    page_title="HireScope Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS (CSS.GG icons included) ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Chat Context Prompt ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a recruiting assistant. Answer ONLY from résumé snippets provided in context. "
        "If the query is unrelated to candidates or résumés, say: "
        "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
    )
}

# --- Session Initialization ---
def init_state():
    ss = st.session_state
    if "all_chats" not in ss:
        ss.all_chats = {}
    if "active_chat" not in ss:
        now = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        ss.active_chat = now
        ss.all_chats[now] = [SYSTEM_PROMPT]
    if "chat_titles" not in ss:
        ss.chat_titles = {k: k for k in ss.all_chats}
    ss.setdefault("is_generating", False)
    ss.setdefault("editing_title", None)
    ss.setdefault("show_delete_confirm", False)

init_state()

# --- Helper Functions ---
def truncate(text, max_len=28):
    return text if len(text) <= max_len else text[:max_len-3] + "..."

def is_greeting(text):
    return bool(re.fullmatch(r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", text.strip(), re.I))

def is_recruitment_query(query):
    prompt = f"Respond ONLY with 'Yes' or 'No'. Is this about candidates, resumes, recruiting, jobs or HR?\nQuery: \"{query}\""
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        return resp.choices[0].message.content.strip().lower().startswith("yes")
    except:
        return False

def generate_title(chat):
    user_msgs = [m["content"] for m in chat if m["role"] == "user"][:3]
    if not user_msgs:
        return f"Chat - {datetime.now():%Y-%m-%d}"
    prompt = "Generate a concise title (3-5 words) for this conversation.\n" + "\n".join(user_msgs)
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=20
        )
        return response.choices[0].message.content.strip().strip('"\'')[:40]
    except:
        return "Chat - Title Error"

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 💬 HireScope Chat")
    if st.button("➕ New Chat"):
        new = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new] = new
        st.session_state.active_chat = new
        st.rerun()

    st.markdown("---")
    for name in sorted(st.session_state.all_chats.keys(), reverse=True):
        label = truncate(st.session_state.chat_titles.get(name, name))
        if st.button(label, key=f"sel_{name}"):
            st.session_state.active_chat = name
            st.rerun()

    st.markdown("---")
    if len(st.session_state.all_chats) > 1:
        if st.button("🗑️ Delete Current Chat"):
            del st.session_state.chat_titles[st.session_state.active_chat]
            del st.session_state.all_chats[st.session_state.active_chat]
            st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
            st.rerun()

# --- Main Interface ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats[chat_key]

st.markdown(f"## 💼 {st.session_state.chat_titles.get(chat_key, chat_key)}")

for msg in chat[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Ask about candidates...")

if query and not st.session_state.is_generating:
    chat.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if is_greeting(query):
                    reply = "Hello! How can I assist you with candidate queries today?"
                elif not is_recruitment_query(query):
                    reply = "Sorry, I only answer questions based on résumé snippets provided."
                else:
                    total = collection.count()
                    if total == 0:
                        reply = "No résumés available in the database."
                    else:
                        results = collection.query(query_texts=[query], n_results=min(5, total))
                        docs = results.get("documents", [[]])[0]
                        if not docs:
                            reply = "No relevant information found."
                        else:
                            context = "\n\n---\n\n".join(docs)
                            chat[0]["content"] = f"Answer ONLY from:\n\n{context}"
                            response = openai.chat.completions.create(
                                model="gpt-4",
                                messages=chat,
                                temperature=0.3,
                                max_tokens=1000
                            )
                            reply = response.choices[0].message.content.strip()
            except Exception as e:
                reply = f"An error occurred: {str(e)}"
            chat.append({"role": "assistant", "content": reply})
            st.markdown(reply)

    # Auto-rename if needed
    if chat_key.startswith("New Chat") and len([m for m in chat if m["role"] == "user"]) >= 2:
        new_title = generate_title(chat)
        st.session_state.chat_titles[chat_key] = new_title

# --- Footer ---
st.markdown("---")
st.markdown("""
<div class="footer">
    <span>🤖 HireScope AI &ndash; Candidate Search Assistant</span>
</div>
""", unsafe_allow_html=True)