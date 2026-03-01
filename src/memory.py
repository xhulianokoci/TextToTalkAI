# ============================================================
# memory.py — Conversation Memory Manager
# ============================================================
# Responsibilities:
#   - Store conversation turns (user + assistant)
#   - Cap history to prevent context window overflow
#   - Provide clean history for prompt injection
#   - Reset memory on demand
#
# Design decision:
#   Memory is stored as a plain Python list in Streamlit session state.
#   No database. No persistence across sessions.
#
#   Why?
#   This is a single-user app. The conversation is tied to the browser tab.
#   Persisting chat history across sessions would require a database
#   (adds complexity) and is out of scope for v1.
#
#   What is kept: Last MAX_TURNS full exchanges (user + assistant pairs)
#   What is discarded: Older turns beyond MAX_TURNS
# ============================================================

MAX_TURNS = 6  # 3 user messages + 3 assistant responses
               # Why 6? Claude's context window is large, but RAG prompts
               # already inject retrieved chunks. Keeping 6 turns balances
               # conversational continuity with prompt size.


def add_turn(history: list[dict], role: str, content: str) -> list[dict]:
    """
    Append a new turn to the conversation history.
    Trims to MAX_TURNS if needed.

    Args:
        history: Current list of turns
        role: "user" or "assistant"
        content: The message text

    Returns:
        Updated history list
    """
    history.append({"role": role, "content": content})

    # Keep only the last MAX_TURNS messages
    if len(history) > MAX_TURNS:
        history = history[-MAX_TURNS:]

    return history


def get_history(history: list[dict]) -> list[dict]:
    """
    Return the current conversation history.
    Excludes the most recent user turn (that's handled by the prompt builder).
    """
    return history


def clear_history() -> list:
    """Return a fresh empty history list."""
    return []


def summarize_history_for_display(history: list[dict]) -> list[dict]:
    """
    Format history for display in the Streamlit chat UI.
    Returns list of dicts with 'role' and 'content' keys.
    """
    return [{"role": turn["role"], "content": turn["content"]} for turn in history]
