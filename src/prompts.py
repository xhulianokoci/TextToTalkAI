# ============================================================
# prompts.py — All Prompt Templates
# ============================================================
# Centralizing prompts here means:
#   - Easy to audit and modify without touching logic files
#   - Change log entries can reference this file specifically
#   - No prompt logic scattered across multiple modules
# ============================================================


SYSTEM_PROMPT = """You are a precise document assistant. Your job is to answer questions \
based strictly on the document context provided to you.

Rules you must follow:
1. ONLY use information from the provided context to answer. Do not use any outside knowledge.
2. If the context does not contain enough information to answer, say exactly: \
"I could not find an answer to that in the uploaded documents."
3. Always cite your sources using the [SOURCE N] labels from the context.
4. Keep answers clear and concise. Use bullet points for lists when appropriate.
5. Do not speculate, infer beyond what is written, or make assumptions.
6. If asked something outside the scope of the documents, politely redirect.

Citation format: After each claim, reference the source like this: [Source: filename.pdf, Page X]
"""
# Why this system prompt?
# - Rule 1 is the core hallucination guardrail. Claude must not invent answers.
# - Rule 2 gives Claude a safe, honest fallback instead of guessing.
# - Rule 3 ensures every answer is traceable to a real document chunk.
# - Rules 4-6 keep the tone professional and answers tight.


def build_rag_prompt(question: str, context: str, conversation_history: list[dict]) -> list[dict]:
    """
    Build the full message list to send to Claude.

    Structure:
      - Past conversation turns (memory)
      - Current user message containing the context + question

    Why inject context into the user message and not the system prompt?
    Because context changes with every query. Keeping it in the user
    turn makes the structure clear and auditable.
    """
    messages = []

    # Inject conversation history (memory)
    for turn in conversation_history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Current query with retrieved context
    user_message = f"""Here is the relevant context retrieved from your documents:

{context}

---

Based only on the context above, please answer the following question:

{question}

Remember to cite which source(s) you used in your answer."""

    messages.append({"role": "user", "content": user_message})

    return messages


def build_no_document_prompt(question: str) -> list[dict]:
    """
    Used when no documents have been uploaded yet.
    Prevents Claude from answering from its own knowledge.
    """
    return [{
        "role": "user",
        "content": (
            f"The user asked: '{question}'\n\n"
            "No documents have been uploaded yet. "
            "Please inform the user they need to upload a document first."
        )
    }]
