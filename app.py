# ============================================================
# app.py — Streamlit UI Entry Point
# ============================================================
# This is the only file you run. It wires together all modules.
#
# Run with:
#   streamlit run app.py
#
# User flow:
#   1. User uploads one or more PDF/TXT files
#   2. Files are chunked and embedded into Pinecone
#   3. User types a question in the chat box
#   4. App retrieves relevant chunks and sends to Claude
#   5. Claude's answer streams back with source citations
#   6. Conversation history is maintained for follow-up questions
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from src.ingestion import process_uploaded_file
from src.embeddings import upsert_chunks, delete_document_vectors
from src.retrieval import retrieve_relevant_chunks, format_context_for_prompt
from src.llm import stream_answer
from src.memory import add_turn, clear_history, summarize_history_for_display

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Talk to Documents",
    page_icon="📄",
    layout="wide"
)

# ── Session State Initialization ─────────────────────────────
# Streamlit re-runs the entire script on every interaction.
# Session state persists values across those re-runs.

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []  # List of filenames processed

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []  # For display only


# ── Layout ───────────────────────────────────────────────────
st.title("📄 Talk to Documents")
st.caption("Upload PDFs or text files and ask questions about them. Answers are grounded only in your documents.")

col_sidebar, col_chat = st.columns([1, 2.5])


# ── Sidebar: Document Upload ──────────────────────────────────
with col_sidebar:
    st.subheader("📁 Your Documents")

    uploaded_files = st.file_uploader(
        label="Upload PDF or TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="You can upload multiple files. Each will be chunked and indexed."
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name

            # Only process files we haven't seen yet
            if filename not in st.session_state.uploaded_documents:
                with st.spinner(f"Processing {filename}..."):
                    try:
                        file_bytes = uploaded_file.read()
                        chunks = process_uploaded_file(file_bytes, filename)
                        count = upsert_chunks(chunks)
                        st.session_state.uploaded_documents.append(filename)
                        st.success(f"✅ {filename} — {count} chunks indexed")
                    except Exception as e:
                        st.error(f"❌ Failed to process {filename}: {str(e)}")

    # Show currently loaded documents
    if st.session_state.uploaded_documents:
        st.markdown("**Indexed documents:**")
        for doc in st.session_state.uploaded_documents:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• `{doc}`")
            with col2:
                # Remove button per document
                if st.button("✕", key=f"remove_{doc}", help=f"Remove {doc}"):
                    with st.spinner(f"Removing {doc}..."):
                        try:
                            delete_document_vectors(doc)
                            st.session_state.uploaded_documents.remove(doc)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to remove {doc}: {str(e)}")
    else:
        st.info("No documents uploaded yet. Upload a file to get started.")

    st.divider()

    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.conversation_history = clear_history()
        st.session_state.chat_messages = []
        st.rerun()

    st.divider()
    st.caption("**How it works:** Your documents are split into chunks, converted to vectors, and stored in Pinecone. When you ask a question, the most relevant chunks are retrieved and sent to Claude to generate a grounded answer.")


# ── Main Chat Area ────────────────────────────────────────────
with col_chat:
    st.subheader("💬 Ask a Question")

    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show citations if present
            if message.get("citations"):
                with st.expander("📚 View Sources", expanded=False):
                    for i, citation in enumerate(message["citations"], 1):
                        st.markdown(
                            f"**Source {i}:** `{citation['source']}` — "
                            f"Page {citation['page_number']} "
                            f"*(relevance: {citation['score']})*"
                        )
                        st.caption(citation["text"][:300] + "..." if len(citation["text"]) > 300 else citation["text"])
                        if i < len(message["citations"]):
                            st.divider()

    # Chat input
    if prompt := st.chat_input("Ask something about your documents..."):

        # Display user message immediately
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            documents_uploaded = len(st.session_state.uploaded_documents) > 0

            if not documents_uploaded:
                # No documents — friendly prompt
                response_text = "Please upload at least one document before asking questions. Use the panel on the left to get started."
                st.markdown(response_text)
                retrieved_chunks = []

            else:
                # Retrieve relevant chunks
                with st.spinner("Searching documents..."):
                    try:
                        retrieved_chunks = retrieve_relevant_chunks(
                            query=prompt,
                            filter_sources=st.session_state.uploaded_documents
                        )
                        context = format_context_for_prompt(retrieved_chunks)
                    except Exception as e:
                        st.error(f"Retrieval failed: {str(e)}")
                        retrieved_chunks = []
                        context = "No context available."

                # Stream Claude's answer
                response_placeholder = st.empty()
                response_text = ""

                try:
                    for chunk in stream_answer(
                        question=prompt,
                        context=context,
                        conversation_history=st.session_state.conversation_history,
                        documents_uploaded=True
                    ):
                        response_text += chunk
                        response_placeholder.markdown(response_text + "▌")

                    # Final render without cursor
                    response_placeholder.markdown(response_text)

                except Exception as e:
                    response_text = f"I encountered an error generating a response: {str(e)}"
                    st.error(response_text)

                # Show citations
                if retrieved_chunks:
                    with st.expander("📚 View Sources", expanded=False):
                        for i, citation in enumerate(retrieved_chunks, 1):
                            st.markdown(
                                f"**Source {i}:** `{citation['source']}` — "
                                f"Page {citation['page_number']} "
                                f"*(relevance: {citation['score']})*"
                            )
                            st.caption(citation["text"][:300] + "..." if len(citation["text"]) > 300 else citation["text"])
                            if i < len(retrieved_chunks):
                                st.divider()

        # Update memory
        st.session_state.conversation_history = add_turn(
            st.session_state.conversation_history, "user", prompt
        )
        st.session_state.conversation_history = add_turn(
            st.session_state.conversation_history, "assistant", response_text
        )

        # Save to display history
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_text,
            "citations": retrieved_chunks if documents_uploaded else []
        })
