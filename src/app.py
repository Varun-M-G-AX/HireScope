import re
import streamlit as st
st.set_page_config(page_title="HireScope Query Bot", page_icon="💼")
from utils import collection, openai


st.title("💼 HireScope Query Bot")

# ───────── résumé count ─────────
total = collection.count()
st.caption(f"Total résumés in database: **{total}**")

# ----- avoid slider crash when total is 0 or 1 -----
if total > 1:
    top_k = st.sidebar.slider(
        "Number of top matches to retrieve",
        min_value=1,
        max_value=total,
        value=min(5, total)
    )
else:
    top_k = 1

# ───────── chat memory ─────────
if "chat" not in st.session_state:
    st.session_state.chat = [
        {
            "role": "system",
            "content": (
                "You are a recruiting assistant. "
                "Answer ONLY from résumé snippets provided in context. "
                "If the query is unrelated to candidates or résumés, "
                "say: 'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
            ),
        }
    ]

# ───────── show chat history ─────────
for msg in st.session_state.chat[1:]:
    st.chat_message(msg["role"]).markdown(msg["content"])

# ───────── helpers ─────────
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
        return False  # fallback

# ───────── user prompt ─────────
query = st.chat_input("Ask anything about candidates…")
if query:
    st.chat_message("user").markdown(query)
    st.session_state.chat.append({"role": "user", "content": query})

    # Greeting / thanks shortcut
    if is_greeting(query):
        reply = "You're welcome! How can I assist you with candidate information?"
    else:
        relevant = is_recruitment_query(query)

        hits = collection.query(query_texts=[query], n_results=top_k)
        docs = hits["documents"][0]

        # If classifier said No but we found some matches, treat as relevant
        if docs and any(d.strip() for d in docs):
            relevant = True

        if not relevant:
            reply = (
                "Sorry, I can only answer questions about candidates based on "
                "the résumé snippets provided."
            )
        elif not docs or all(not d.strip() for d in docs):
            reply = "I’m sorry, I don’t have résumé data that answers that."
        else:
            context = "\n\n---\n\n".join(docs)
            st.session_state.chat[0]["content"] = (
                "Answer ONLY from these résumé snippets:\n\n" + context
            )
            resp = openai.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.chat
            )
            reply = resp.choices[0].message.content.strip()

    st.chat_message("assistant").markdown(reply)
    st.session_state.chat.append({"role": "assistant", "content": reply})

# ───────── if DB is empty ─────────
if total == 0:
    st.warning("⚠️ No résumés in the database. Upload some from the HR Uploader page.")
