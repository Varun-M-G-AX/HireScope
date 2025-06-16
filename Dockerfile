# ───────────────────────────────────────────────────────────
#  HireScope – Streamlit + ChromaDB + OCR
#  Built for Hugging Face Spaces (Docker SDK)
# ───────────────────────────────────────────────────────────
FROM python:3.9-slim

# ── 1. Create working directory ────────────────────────────
WORKDIR /app

# ── 2. System dependencies (build, OCR, poppler for pdf2image)
RUN apt-get update && apt-get install -y \
      build-essential \
      git curl \
      tesseract-ocr \
      poppler-utils \
  && rm -rf /var/lib/apt/lists/*

# ── 3. Python dependencies ─────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 4. Copy application source ─────────────────────────────
COPY src/ ./src/

# ── 5. Environment variables ───────────────────────────────
# Persist ChromaDB vectors in HF Space volume
ENV CHROMA_DB_DIR=/data/chroma_store
# Streamlit config directory
ENV HOME=/app

# ── 6. Streamlit writable config dir ───────────────────────
RUN mkdir -p /app/.streamlit && chmod -R 777 /app/.streamlit

# ── 7. Expose port & healthcheck ───────────────────────────
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ── 8. Run Streamlit app ───────────────────────────────────
ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
