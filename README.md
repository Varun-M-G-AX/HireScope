# HireScope 💼

**AI-Powered Résumé Assistant for Recruiters & HR Teams**

[![Streamlit](https://img.shields.io/badge/Streamlit-App-blue?logo=streamlit)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-yellow)](https://www.trychroma.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-4o-green)](Hello GPT-4o | OpenAI https://share.google/VLrOImpBBgO1fAsru)

---

## Overview

**HireScope** is an AI-driven platform designed to streamline the recruitment process by enabling HR teams to upload, parse, query, and search candidate résumés at scale. The app leverages Streamlit for the user interface, ChromaDB as the vector database, OCR for PDF extraction, and OpenAI's GPT models for advanced résumé summarization and Q&A.

---

## Features

- **Upload Résumés:** Supports PDF uploads, robust text extraction (multi-library with OCR fallback).
- **Résumé Parsing:** Extracts structured candidate data (contact info, skills, work history, education, etc.) into a unified schema using advanced AI prompts.
- **Semantic Search:** Instantly find top-matching candidates using ChromaDB vector search.
- **Chatbot Q&A:** Query candidate data in natural language with an interactive Streamlit chatbot powered by GPT-4o.
- **Modern UI:** Responsive, theme-aware design with enhanced UX and dark mode support.
- **Docker Support:** Easily deployable anywhere with a single Dockerfile.
- **Persistent Storage:** Stores resume embeddings and metadata for fast querying.

---

## Project Structure

```
HireScope/
│
├── Dockerfile                 # All-in-one deployment file
├── requirements.txt           # Python dependencies (root)
├── src/
│   ├── HR_Chat_Bot.py         # Main Streamlit app entrypoint
│   ├── app.py                 # Core logic for the chatbot
│   ├── pages/
│   │   ├── 1_HR_Upload.py     # Résumé uploading & extraction UI
│   │   └── 2_Profiles_Search.py # Candidate search & display UI
│   ├── utils.py               # Helpers (embedding, parsing, summarization)
│   ├── prompt_2.md            # AI prompt for structured résumé data extraction
│   └── requirements.txt       # (Optional) Additional dependencies for src/
└── README.md                  # You're here!
```

---

## How It Works

1. **Upload:** Drag and drop candidate résumés (PDFs).
2. **Extraction:** Multi-method text extraction (PyMuPDF, pdfminer, pdfplumber, PyPDF2, Tesseract OCR).
3. **Parsing & Embedding:** Summarize and structure resumes using GPT-4o, then embed using OpenAI embeddings into ChromaDB.
4. **Search & Chat:** Use the chatbot or search UI to query the database for relevant candidates, skills, or experience.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Varun-M-G-AX/HireScope.git
cd HireScope
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```
> For full OCR support, you may need system packages: `tesseract-ocr`, `poppler-utils`, and their dependencies.

### 3. Set Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key for embedding and chat.
- `CHROMA_DB_DIR` (optional): Custom path for persistent ChromaDB storage.

### 4. Run the App

```bash
streamlit run src/HR_Chat_Bot.py
```

Or use Docker:

```bash
docker build -t hirescope .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... hirescope
```

---

## Usage

- **Upload Résumés:** Use the upload page to add new candidates.
- **Search Candidates:** Use the profiles search page for semantic queries.
- **Chatbot:** Ask natural language questions about candidates (e.g., "Show me Python developers with 5+ years experience").

---

## AI Prompt Schema

Résumé parsing follows a strict [schema](src/prompt_2.md) where all candidate fields (name, email, skills, work history, etc.) are extracted and normalized for reliable search and analysis.

---

## Dependencies

- [Streamlit](https://streamlit.io/)
- [OpenAI](https://openai.com/)
- [ChromaDB](https://www.trychroma.com/)
- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [pdfminer.six](https://github.com/pdfminer/pdfminer.six)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [pytesseract](https://github.com/madmaze/pytesseract)
- [pdf2image](https://github.com/Belval/pdf2image)
- [fitz (PyMuPDF)](https://pymupdf.readthedocs.io/)

See [requirements.txt](requirements.txt) for the full list.

---

## Deployment

The included [Dockerfile](Dockerfile) supports Hugging Face Spaces or any generic containerized deployment.

---

## License

MIT License

---

## Author

[Varun-M-G-AX](https://github.com/Varun-M-G-AX)

---

## Acknowledgments

- Inspired by HR automation needs and modern AI capabilities.
- Powered by OpenAI, Streamlit, and the open Python data stack.

---

> **Note:** This README was generated based on the contents of the repository. For the latest updates and code, visit the [GitHub repository](https://github.com/Varun-M-G-AX/HireScope).
