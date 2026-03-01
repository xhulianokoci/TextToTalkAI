# ============================================================
# retrieval.py — Semantic Similarity Search
# ============================================================
# Responsibilities:
#   - Embed the user's question
#   - Query Pinecone for the most similar document chunks
#   - Return ranked results with metadata for citations
# ============================================================

from src.embeddings import embed_texts, get_pinecone_index

# --- Constants ---
TOP_K = 5                  # Number of chunks to retrieve per query
MIN_SCORE = 0.30           # Minimum similarity score to include a result
                           # Cosine similarity: 1.0 = identical, 0.0 = unrelated
                           # 0.30 is a reasonable floor for semantic relevance


def retrieve_relevant_chunks(query: str, filter_sources: list[str] = None) -> list[dict]:
    """
    Given a user question, find the TOP_K most semantically
    similar chunks stored in Pinecone.

    Args:
        query: The user's natural language question
        filter_sources: Optional list of filenames to restrict search to.
                        If None, searches across all uploaded documents.

    Returns:
        List of result dicts, each containing:
          - text: the raw chunk text (used in the LLM prompt)
          - source: filename
          - page_number: page in the original document
          - chunk_index: position within the page
          - score: cosine similarity score (0.0 to 1.0)
    """
    # Step 1: Embed the query using the same model used for documents
    query_embedding = embed_texts([query])[0]

    # Step 2: Build optional metadata filter
    query_filter = None
    if filter_sources:
        query_filter = {"source": {"$in": filter_sources}}

    # Step 3: Query Pinecone
    index = get_pinecone_index()
    results = index.query(
        vector=query_embedding,
        top_k=TOP_K,
        include_metadata=True,
        filter=query_filter
    )

    # Step 4: Filter by minimum score and format output
    chunks = []
    for match in results.matches:
        if match.score >= MIN_SCORE:
            chunks.append({
                "text": match.metadata.get("text", ""),
                "source": match.metadata.get("source", "Unknown"),
                "page_number": match.metadata.get("page_number", "?"),
                "chunk_index": match.metadata.get("chunk_index", 0),
                "score": round(match.score, 4)
            })

    return chunks


def format_context_for_prompt(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a structured context block
    to be injected into the Claude prompt.

    Each chunk is labeled with its source and page so Claude
    can reference them in citations.
    """
    if not chunks:
        return "No relevant context found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[SOURCE {i}] File: {chunk['source']} | Page: {chunk['page_number']}\n"
            f"{chunk['text']}"
        )

    return "\n\n---\n\n".join(context_parts)
