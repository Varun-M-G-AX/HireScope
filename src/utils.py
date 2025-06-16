"""
utils.py – shared helpers for HireScope

• Reads OPENAI_API_KEY from env (HF Secret)
• Uses persistent ChromaDB in /data/chroma_store on HF
• Falls back to ./chroma_store locally (or in‑memory if /data isn't writable)
• GPT‑4o résumé summariser
• Candidate‑ID generator
"""
import os, re
from datetime import datetime
import streamlit as st
import openai, chromadb
from chromadb.utils import embedding_functions

# ── 1. Secure API key ────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY missing. Add it in Space ➜ Settings ➜ Secrets.")
    st.stop()
openai.api_key = OPENAI_API_KEY

# ── 2. Choose persistent directory ───────────────────────────────────
DEFAULT_LOCAL_DIR = "./chroma_store"
HF_DATA_DIR       = "/data/chroma_store"          # Hugging Face Docker volume

USE_HF_DIR = bool(os.getenv("SPACE_ID") or os.getenv("HF_SPACE_ID"))
PERSIST_DIR = os.getenv("CHROMA_DB_DIR",
                        HF_DATA_DIR if USE_HF_DIR else DEFAULT_LOCAL_DIR)

# ── 3. Create (or gracefully skip) the directory ─────────────────────
@st.cache_resource
def get_chroma_client():
    try:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        st.info(f"📂 Using persistent Chroma directory: {PERSIST_DIR}")
        return chromadb.PersistentClient(path=PERSIST_DIR)
    except PermissionError:
        st.warning(f"⚠️ No write access to {PERSIST_DIR}. "
                   "Falling back to in‑memory ChromaDB (data will reset on restart).")
        return chromadb.Client()   # ephemeral

chroma_client = get_chroma_client()

def get_collection():
    return chroma_client.get_or_create_collection(
        name="resumes",
        embedding_function=embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name="text-embedding-3-large",
        )
    )
collection = get_collection()

# ── 4. GPT‑4o résumé summariser ──────────────────────────────────────
def summarize_resume(raw: str) -> str:
    prompt = f"""
Return the résumé as structured **plain text** (NOT JSON) like:

Name: ...
Email: ...
Phone: ...
Location: ...
Skills: python, sql, ...
Languages: english, ...
Certifications: ...
Education:
  • Degree at University
Work Experience:
  • Role at Company (dates) – short summary
Latest Role: ...

Résumé:
\"\"\"{raw[:3000]}\"\"\""""
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

# ── 5. Candidate‑ID helper ───────────────────────────────────────────
def make_candidate_id(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]", "", name.lower())
    return f"{clean}_{datetime.now():%Y%m%d%H%M%S}"
