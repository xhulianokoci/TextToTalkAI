# ============================================================
# embeddings.py — Embedding Generation + Pinecone Storage
# ============================================================
# Responsibilities:
#   - Load environment config (local .env or Streamlit secrets)
#   - Initialize Pinecone index (create if not exists)
#   - Generate embeddings for text chunks via OpenAI
#   - Upsert vectors + metadata into Pinecone
# ============================================================

import os
import time
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import get_config

# --- Constants ---
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536   # Fixed output size for text-embedding-3-small
PINECONE_METRIC = "cosine"   # Cosine similarity is standard for semantic search
UPSERT_BATCH_SIZE = 100      # Pinecone recommends batches of 100 max


def get_pinecone_index():
    """
    Initialize Pinecone client and return the index.
    Creates the index if it doesn't exist yet.

    Why ServerlessSpec?
    Serverless Pinecone has no idle cost — perfect for a small-scale app.
    """
    config = get_config()
    pc = Pinecone(api_key=config["PINECONE_API_KEY"])
    index_name = config["PINECONE_INDEX_NAME"]

    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIMENSION,
            metric=PINECONE_METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Wait for index to be ready
        time.sleep(5)

    return pc.Index(index_name)


def get_openai_client():
    config = get_config()
    return OpenAI(api_key=config["OPENAI_API_KEY"])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Send a list of text strings to OpenAI and get back embeddings.
    Retries up to 3 times on failure with exponential backoff.

    Why retry?
    API calls can fail transiently. Retrying automatically prevents
    the user from having to re-upload their document.
    """
    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def upsert_chunks(chunks: list[dict]) -> int:
    """
    Embed a list of chunks and upsert them into Pinecone.

    Each Pinecone vector contains:
      - id: unique string identifier
      - values: the embedding vector (1536 floats)
      - metadata: source filename, page number, chunk index, and raw text
                  (raw text is stored so we can return it as a citation)

    Returns the total number of vectors upserted.
    """
    index = get_pinecone_index()
    total_upserted = 0

    # Process in batches to respect Pinecone limits
    for i in range(0, len(chunks), UPSERT_BATCH_SIZE):
        batch = chunks[i:i + UPSERT_BATCH_SIZE]
        texts = [chunk["text"] for chunk in batch]
        embeddings = embed_texts(texts)

        vectors = []
        for chunk, embedding in zip(batch, embeddings):
            vectors.append({
                "id": chunk["chunk_id"],
                "values": embedding,
                "metadata": {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"]
                }
            })

        index.upsert(vectors=vectors)
        total_upserted += len(vectors)

    return total_upserted


def delete_document_vectors(filename: str):
    """
    Delete all vectors associated with a specific document.
    Used when the user removes a document from the session.
    """
    index = get_pinecone_index()
    # Pinecone supports metadata filtering for deletion
    index.delete(filter={"source": {"$eq": filename}})
