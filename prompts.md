# RAG Assistant — Prompt Engineering Documentation

## Overview
All prompts live in `src/prompts.py`. This document explains every prompt, why it is structured the way it is, and what guardrails are in place.

---

## System Prompt

```
You are a precise document assistant. Your job is to answer questions
based strictly on the document context provided to you.

Rules you must follow:
1. ONLY use information from the provided context to answer. Do not use any outside knowledge.
2. If the context does not contain enough information to answer, say exactly:
   "I could not find an answer to that in the uploaded documents."
3. Always cite your sources using the [SOURCE N] labels from the context.
4. Keep answers clear and concise. Use bullet points for lists when appropriate.
5. Do not speculate, infer beyond what is written, or make assumptions.
6. If asked something outside the scope of the documents, politely redirect.

Citation format: After each claim, reference the source like this: [Source: filename.pdf, Page X]
```

### Why this structure?
Rule 1 is the primary hallucination guardrail. Without it, Claude would answer from its training data when document context is insufficient, making it impossible to verify whether answers are grounded.

Rule 2 gives Claude a safe, honest exit. A clearly defined fallback phrase is better than an evasive or partially fabricated answer.

Rule 3 makes every claim traceable. Users can open the "View Sources" expander and verify exactly which chunk Claude used.

Rules 4-6 are quality and scope controls. They keep responses professional and prevent Claude from drifting into general conversation mode.

---

## RAG Prompt (Per Query)

Built by `build_rag_prompt()` in prompts.py. Structure:

```
[Conversation history turns, if any]

User: Here is the relevant context retrieved from your documents:

[SOURCE 1] File: document.pdf | Page: 3
... chunk text ...

---

[SOURCE 2] File: report.txt | Page: 1
... chunk text ...

---

Based only on the context above, please answer the following question:

[User's question]

Remember to cite which source(s) you used in your answer.
```

### Why inject context into the user message and not the system prompt?
Context changes with every query. The system prompt is static — it defines behavior. Injecting dynamic content (retrieved chunks) into the user turn keeps the architecture clean: system = rules, user = data + question.

### Why the [SOURCE N] labeling format?
Explicit labels give Claude a clear reference system. Instead of vague citations, Claude can say "according to Source 2" and the user can immediately match that to the expander entry showing the exact chunk.

### Why the trailing reminder ("Remember to cite...")?
Claude follows instructions more reliably when reminded at the point of action, not just in the system prompt. The trailing reminder reinforces citation behavior at the moment Claude begins composing its answer.

---

## No-Document Fallback Prompt

Used when a user asks a question before uploading any documents.

```
The user asked: '[question]'

No documents have been uploaded yet.
Please inform the user they need to upload a document first.
```

### Why a separate prompt?
Sending an empty context block to Claude could result in it answering from its own knowledge (violating Rule 1). A dedicated prompt ensures the correct behavior: redirect, don't answer.

---

## Hallucination Guardrails Summary

| Guardrail | Implementation |
|---|---|
| Ground answers in context only | System prompt Rule 1 |
| Honest fallback when context insufficient | System prompt Rule 2 + defined phrase |
| Traceable citations | [SOURCE N] labels + citation expander in UI |
| No outside knowledge | Context injected with explicit "based only on" instruction |
| No documents = no answer | Separate prompt for zero-document state |
| Low-relevance chunks filtered | MIN_SCORE = 0.30 threshold in retrieval.py |

---

## Prompt Versioning
Any change to prompt text must be recorded in `docs/changelog.md` under the "Prompts" area. The previous prompt text should be noted in the change reason for rollback reference.
