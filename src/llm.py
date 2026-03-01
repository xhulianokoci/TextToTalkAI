# ============================================================
# llm.py — Answer Generation via Claude
# ============================================================
# Responsibilities:
#   - Initialize Anthropic client
#   - Send retrieval-augmented prompts to Claude
#   - Return generated answers
#   - Handle API errors gracefully
# ============================================================

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import get_config
from src.prompts import SYSTEM_PROMPT, build_rag_prompt, build_no_document_prompt

# --- Constants ---
CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024   # Cap response length. 1024 tokens ≈ ~750 words.
                    # Enough for detailed answers, prevents runaway responses.


def get_anthropic_client() -> Anthropic:
    config = get_config()
    return Anthropic(api_key=config["ANTHROPIC_API_KEY"])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_answer(
    question: str,
    context: str,
    conversation_history: list[dict],
    documents_uploaded: bool = True
) -> str:
    """
    Send question + retrieved context to Claude and return the answer.

    Args:
        question: The user's natural language question
        context: Formatted string of retrieved document chunks
        conversation_history: Past conversation turns for memory
        documents_uploaded: False if no docs exist yet (shows friendly error)

    Returns:
        Claude's answer as a plain string

    Why retry?
    Anthropic's API can occasionally return transient errors (529 overloaded).
    Retrying 3 times with exponential backoff handles this invisibly.
    """
    client = get_anthropic_client()

    if not documents_uploaded:
        messages = build_no_document_prompt(question)
    else:
        messages = build_rag_prompt(question, context, conversation_history)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages
    )

    return response.content[0].text


def stream_answer(
    question: str,
    context: str,
    conversation_history: list[dict],
    documents_uploaded: bool = True
):
    """
    Stream Claude's response token by token.
    Used for a more responsive UI — text appears as it's generated
    rather than waiting for the full response.

    Yields string chunks as they arrive.
    """
    client = get_anthropic_client()

    if not documents_uploaded:
        messages = build_no_document_prompt(question)
    else:
        messages = build_rag_prompt(question, context, conversation_history)

    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text
