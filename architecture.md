# TalkToTextAI — Architecture Documentation

## Project Overview
Talk to Documents is a Retrieval-Augmented Generation (RAG) application that lets users upload PDF or text files and query them in natural language. Answers are grounded strictly in the uploaded documents, with source citations for every response.

---

## High-Level Architecture

```
User Browser (Streamlit)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                      app.py (UI Layer)                   │
│  - File upload widget                                    │
│  - Chat interface                                        │
│  - Session state management                              │
│  - Citation display                                      │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────────┐
        ▼               ▼                   ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────────┐
│ ingestion.py │ │ retrieval.py│ │    memory.py      │
│ PDF parsing  │ │ Similarity  │ │ Conversation      │
│ Chunking     │ │ search      │ │ history manager   │
└──────┬───────┘ └──────┬──────┘ └──────────────────┘
       │                │
       ▼                ▼
┌──────────────┐ ┌─────────────┐
│embeddings.py │ │   llm.py    │
│OpenAI embed  │ │ Claude API  │
│Pinecone store│ │ Answer gen  │
└──────┬───────┘ └──────┬──────┘
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────────┐
│  Pinecone   │  │  Anthropic API  │
│  (Cloud DB) │  │  (Claude model) │
└─────────────┘  └─────────────────┘
```

---

## Component Responsibilities

### app.py
The UI entry point and orchestrator. Manages Streamlit session state, handles file uploads, triggers ingestion, drives the chat loop, and displays citations. Contains no business logic — delegates entirely to src/ modules.

### src/ingestion.py
Parses uploaded files (PDF via PyMuPDF, TXT via standard decode). Splits raw text into token-counted chunks using tiktoken. Attaches metadata (source filename, page number, chunk index) to every chunk. Returns a flat list of chunk dicts.

### src/embeddings.py
Initializes the Pinecone index (creates it if missing). Calls OpenAI's text-embedding-3-small model to convert chunk text into 1536-dimension vectors. Upserts vectors with metadata into Pinecone in batches of 100.

### src/retrieval.py
Embeds the user's question using the same OpenAI model. Queries Pinecone for the top-5 most similar vectors using cosine similarity. Filters results below a 0.30 relevance threshold. Formats results into a structured context block for prompt injection.

### src/llm.py
Builds the final message payload (system prompt + retrieved context + conversation history + user question). Sends to Claude via the Anthropic Python SDK. Supports both streaming (real-time token display) and non-streaming modes.

### src/prompts.py
Single source of truth for all prompt templates. Contains the system prompt (with hallucination guardrails), the RAG prompt builder, and the no-documents fallback prompt.

### src/memory.py
Maintains a capped list of conversation turns (max 6). Provides add, get, clear, and display functions. Memory is stored in Streamlit session state — it resets when the browser tab is closed or refreshed.

### src/config.py
Unified secret loader. Checks Streamlit secrets first (cloud deployment), falls back to .env (local). Validates all required keys are present and raises a clear error if not.

---

## Data Flow

### Upload Flow
1. User selects a PDF or TXT file in the sidebar
2. app.py reads file bytes and calls ingestion.process_uploaded_file()
3. ingestion.py extracts text page by page, then splits into chunks
4. Each chunk receives metadata: source filename, page number, chunk index, unique ID
5. embeddings.upsert_chunks() embeds each chunk via OpenAI API
6. Vectors + metadata are stored in Pinecone
7. Filename is added to session state to track loaded documents

### Query Flow
1. User types a question in the chat input
2. retrieval.retrieve_relevant_chunks() embeds the query via OpenAI
3. Pinecone returns the top-5 most similar chunks (filtered to uploaded docs)
4. retrieval.format_context_for_prompt() formats chunks with [SOURCE N] labels
5. prompts.build_rag_prompt() assembles: system prompt + history + context + question
6. llm.stream_answer() sends the full payload to Claude
7. Claude's response streams back token by token
8. Citations (chunk source + page + score) are shown in an expander below the answer
9. The exchange is added to conversation memory

---

## Key Architectural Decisions

### Why Pinecone over ChromaDB?
Pinecone is cloud-hosted, meaning the vector index persists across restarts and works identically in local and deployed environments. ChromaDB stores data on disk locally, which creates sync problems when deploying to Streamlit Cloud. For a dual-environment target, Pinecone eliminates an entire class of deployment bugs.

### Why OpenAI embeddings with Anthropic LLM?
These are separate concerns. Embeddings are a mathematical transformation — they don't "know" anything. OpenAI's text-embedding-3-small is the highest quality/cost ratio embedding model available. Claude is used for reasoning and language generation, where it excels. Mixing providers at different layers is standard RAG practice.

### Why 800 token chunks with 100 token overlap?
800 tokens provides enough context for a chunk to be semantically meaningful (a paragraph or two). Shorter chunks lose context; longer chunks hurt retrieval precision because a single vector must represent too much content. The 100-token overlap prevents a sentence from being cut in half between two chunks, preserving meaning at boundaries.

### Why cap memory at 6 turns?
The RAG prompt already injects up to 5 document chunks per query. Together with the system prompt, that consumes significant context. Capping history at 6 turns keeps total prompt size manageable while still enabling natural follow-up conversations.

### Why stream the response?
Streaming (yielding tokens as they arrive) dramatically improves perceived performance. A response that takes 5 seconds to generate appears immediately and types itself out, vs. a 5-second blank wait. This is a significant UX improvement for no additional cost.

---

## Embedding Model Specs
| Property | Value |
|---|---|
| Model | text-embedding-3-small |
| Provider | OpenAI |
| Output dimensions | 1536 |
| Max input tokens | 8191 |
| Cost | ~$0.00002 per 1K tokens |

## Retrieval Specs
| Property | Value |
|---|---|
| Similarity metric | Cosine |
| Top-K results | 5 |
| Minimum score threshold | 0.30 |
| Metadata stored | text, source, page_number, chunk_index |

## LLM Specs
| Property | Value |
|---|---|
| Model | claude-sonnet-4-6 |
| Provider | Anthropic |
| Max response tokens | 1024 |
| Temperature | Default (not set — Claude's default is balanced) |
| Streaming | Yes |
