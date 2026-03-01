# RAG Assistant — Change Log

All meaningful architectural, implementation, and design decisions are recorded here.

---

| Date | Area | Change | Reason | Impact |
|---|---|---|---|---|
| 2026-02-25 | Project | Initial project scaffold created | Starting Phase 1 of build plan | Sets folder structure and dependency baseline |
| 2026-02-25 | LLM | Selected Anthropic Claude (claude-sonnet-4-6) | Strong instruction-following, grounded responses, excellent for citation-based answers | All answer generation routed through Anthropic API |
| 2026-02-25 | Embeddings | Selected OpenAI text-embedding-3-small | Industry standard, low cost (~$0.00002/chunk), high quality for semantic search | All text chunks and queries embedded via OpenAI |
| 2026-02-25 | Vector DB | Selected Pinecone (cloud) | Persistent across sessions, no local disk management, supports both local dev and cloud deployment | Requires PINECONE_API_KEY; index must be created before first run |
| 2026-02-25 | PDF Parsing | Selected PyMuPDF (fitz) | More reliable than PyPDF2 on complex PDFs, faster, better text extraction accuracy | Handles both simple and complex PDF layouts |
| 2026-02-25 | Chunking | Set chunk size 800 tokens, overlap 100 tokens | 800 tokens balances context richness vs retrieval precision; 100-token overlap prevents meaning loss at chunk boundaries | Affects embedding cost and retrieval accuracy |
| 2026-02-25 | Memory | In-session list capped at 6 turns (3 user + 3 assistant) | Single-user app; session memory is sufficient; avoids bloating Claude's context window | Memory resets on page refresh or session clear |
| 2026-02-25 | Deployment | Target both local (.env) and Streamlit Cloud (st.secrets) | User requires both environments | Config loader must check both sources |
