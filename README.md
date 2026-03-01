# 📄 TalkToTextAI - Talk to Documents

A Retrieval-Augmented Generation (RAG) application that lets you upload PDF or text documents and ask questions about them in natural language. Answers are grounded strictly in your documents, with source citations for every response.

---

## What It Does

- Upload one or more PDF or TXT files
- Ask questions in plain English
- Get accurate, cited answers drawn only from your documents
- Follow up with natural conversation — the app remembers context
- View exactly which document chunk each answer came from

---

## Setup Instructions

### Step 1 — Prerequisites

Make sure you have:
- Python 3.10 or higher (`python --version` to check)
- pip installed
- Git installed (optional, for version control)

### Step 2 — Clone or Download the Project

```bash
git clone https://github.com/your-username/TalkToTextAI.git
cd TalkToTextAI
```

Or download and unzip the project folder manually.

### Step 3 — Create a Virtual Environment

A virtual environment keeps this project's dependencies isolated from your system Python.

```bash
python -m venv venv
```

Activate it:

- **Mac/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

You'll see `(venv)` in your terminal when it's active.

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required libraries. It may take 1–2 minutes.

### Step 5 — Add Your API Keys

Open the `.env` file in the project root. It looks like this:

```
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_INDEX_NAME=talk-to-text
```

Replace each placeholder with your real key. Save the file.

Where to get each key:
- **Anthropic:** https://console.anthropic.com → API Keys
- **OpenAI:** https://platform.openai.com → API Keys
- **Pinecone:** https://app.pinecone.io → API Keys (free tier is sufficient)

### Step 6 — Create Your Pinecone Index

Log in to https://app.pinecone.io and create a new index with these settings:
- **Name:** `talk-to-text` (must match PINECONE_INDEX_NAME in your .env)
- **Dimensions:** `1536`
- **Metric:** `cosine`
- **Type:** Serverless

The app will also attempt to create this automatically on first run, but creating it manually ensures it's ready.

### Step 7 — Run the App

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

---

## Deploying to Streamlit Cloud

1. Push your project to a GitHub repository
   - Make sure `.env` is in `.gitignore` (it already is)
2. Go to https://share.streamlit.io and sign in with GitHub
3. Click "New app" → select your repository → set main file to `app.py`
4. Go to "Advanced settings" → "Secrets" and add your keys in TOML format:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
OPENAI_API_KEY = "sk-proj-..."
PINECONE_API_KEY = "pcsk_..."
PINECONE_INDEX_NAME = "talk-to-text"
```

5. Click Deploy. Your app will be live at a public URL in under 5 minutes.

---

## Project Structure

```
rag-assistant/
├── app.py                  # Streamlit UI — run this
├── .env                    # Your API keys (never commit)
├── .gitignore              # Keeps .env out of Git
├── requirements.txt        # All Python dependencies
├── /src
│   ├── __init__.py
│   ├── config.py           # Loads secrets from .env or Streamlit Cloud
│   ├── ingestion.py        # PDF/TXT parsing and chunking
│   ├── embeddings.py       # OpenAI embeddings + Pinecone upsert
│   ├── retrieval.py        # Similarity search
│   ├── llm.py              # Claude answer generation
│   ├── memory.py           # Conversation history
│   └── prompts.py          # All prompt templates
└── /docs
    ├── architecture.md     # System design documentation
    ├── prompts.md          # Prompt engineering documentation
    └── changelog.md        # Full change log
```

---

## How to Use

1. **Upload documents** using the left panel. Multiple files are supported.
2. **Wait for confirmation** — each file shows a green checkmark when indexed.
3. **Type your question** in the chat box at the bottom.
4. **Read the answer** — it streams in real time.
5. **Check sources** — click "View Sources" under any answer to see the exact document chunks used.
6. **Ask follow-ups** — the app remembers the last 3 exchanges.
7. **Clear conversation** using the button in the sidebar to start fresh.
8. **Remove a document** using the ✕ button next to its name in the sidebar.

---

## Limitations

- **Single user only.** Session state is per browser tab. Multiple users sharing one deployment will share the same Pinecone index.
- **Memory resets on refresh.** Conversation history is not persisted to a database.
- **Answers are only as good as the documents.** If the answer isn't in the document, the app will say so rather than guess.
- **Scanned PDFs with no text layer are not supported.** PyMuPDF reads text; it does not perform OCR on image-based PDFs.
- **Large files take longer.** A 200-page PDF may take 30–60 seconds to process on first upload.

---

## Documentation
- Architecture: `docs/architecture.md`
- Prompt engineering: `docs/prompts.md`
- Change log: `docs/changelog.md`
