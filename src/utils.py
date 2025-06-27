# utils.py – shared helpers for HireScope

import os, re
from datetime import datetime
import streamlit as st
import openai, chromadb
from chromadb.utils import embedding_functions

# ─────────────────────────────────────────────────────────────────────
# 1. Load OpenAI API key from environment
# ─────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY missing. Add it in Space ➜ Settings ➜ Secrets.")
    st.stop()
openai.api_key = OPENAI_API_KEY

# ─────────────────────────────────────────────────────────────────────
# 2. Determine ChromaDB persistence path
# ─────────────────────────────────────────────────────────────────────
DEFAULT_LOCAL_DIR = "./chroma_store"
HF_DATA_DIR       = "/data/chroma_store"

USE_HF_DIR  = bool(os.getenv("SPACE_ID") or os.getenv("HF_SPACE_ID"))
PERSIST_DIR = os.getenv("CHROMA_DB_DIR", HF_DATA_DIR if USE_HF_DIR else DEFAULT_LOCAL_DIR)

@st.cache_resource
def get_chroma_client():
    try:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        st.info(f"📂 Using persistent Chroma directory: {PERSIST_DIR}")
        return chromadb.PersistentClient(path=PERSIST_DIR)
    except PermissionError:
        st.warning(f"⚠️ No write access to {PERSIST_DIR}. Using in-memory ChromaDB (non-persistent).")
        return chromadb.Client()

chroma_client = get_chroma_client()

def get_collection():
    return chroma_client.get_or_create_collection(
        name="resumes",
        embedding_function=embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name="text-embedding-3-large"
        )
    )

collection = get_collection()

# ─────────────────────────────────────────────────────────────────────
# 3. Load summarization prompt from external Markdown file
# ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_prompt_template(path="src/prompt_2.md"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"⚠️ Could not read prompt_2.md: {e}")
        return (
            "You are a résumé parser. Extract fields: name, email, phone, location, "
            "skills, education, experience, and summary. Format in readable plain text."
        )

PROMPT_TEMPLATE = load_prompt_template()

# ─────────────────────────────────────────────────────────────────────
# 4. GPT‑4o résumé summariser using loaded prompt
# ─────────────────────────────────────────────────────────────────────
def summarize_resume(raw: str) -> str:
    prompt = f"{PROMPT_TEMPLATE}\n\nRésumé:\n\"\"\"\n{raw[:3000]}\n\"\"\""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ OpenAI API error: {e}")
        return ""

# ─────────────────────────────────────────────────────────────────────
# 5. Candidate ID generator
# ─────────────────────────────────────────────────────────────────────
def make_candidate_id(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]", "", name.lower())
    if not clean:
        clean = "anonymous"
    return f"{clean}_{datetime.now():%Y%m%d%H%M%S}"
