# LLM Prompt Structuring: Principles and Implementation Guide

## Overview
This document provides a comprehensive reference for structuring prompts and API payloads for both text and image LLMs (Ollama, OpenAI, Stable Diffusion, etc.) in a robust, extensible, and provider-agnostic way. It covers:
- The four canonical elements of any LLM operation
- Canonical JSON structure for frontend/backend
- Mapping to provider-specific APIs (chat, single-prompt, image)
- Implementation principles
- Example diagrams for data flow and prompt composition

---

## 1. Canonical Elements

| Element      | Example (Text)                | Example (Image)           |
|--------------|-------------------------------|---------------------------|
| Data         | "dog breakfasts"              | "a Scottish terrier"      |
| Role         | "Scottish expert"             | "watercolour artist"      |
| Voice/Style  | "Billy Connolly"              | "in the style of Turner"  |
| Operation    | "Summarise", "Expand", etc.   | "Generate 3 variations"   |

---

## 2. Canonical JSON Structure

```json
{
  "data": "dog breakfasts",
  "role": "Scottish expert",
  "voice": "Billy Connolly",
  "operation": "Expand into a paragraph-length brief for a long-form blog article"
}
```

For images:
```json
{
  "data": "a Scottish terrier on a misty moor",
  "role": "watercolour artist",
  "voice": "in the style of Turner",
  "operation": "Generate 3 variations"
}
```

---

## 3. Mapping to LLM Provider APIs

### A. Text LLMs (Ollama, OpenAI, etc.)

#### a) Chat-based APIs

```json
{
  "model": "llama3.1:70b",
  "messages": [
    { "role": "system", "content": "You are a Scottish expert. Write in the style of Billy Connolly." },
    { "role": "user", "content": "Expand the following into a paragraph-length brief for a long-form blog article: dog breakfasts" }
  ],
  "temperature": 0.7,
  "max_tokens": 1003
}
```

#### b) Single-prompt APIs

```
You are a Scottish expert. Write in the style of Billy Connolly.
Task: Expand the following into a paragraph-length brief for a long-form blog article.
Input: dog breakfasts
```

### B. Image LLMs (Stable Diffusion, DALL-E, etc.)

- Compose all elements into a single prompt string.
- Add operation as needed (e.g., number of images).

```json
{
  "model": "dall-e-3",
  "prompt": "A Scottish terrier on a misty moor, in the style of Turner, painted by a watercolour artist.",
  "n": 3
}
```

---

## 4. Implementation Principles

- **Frontend:**
  - Collect all four elements as separate fields.
  - Send as a structured JSON object to the backend.
  - Do not build the final prompt in the frontend.

- **Backend:**
  - Compose the final prompt or message array for the target LLM/provider.
  - Use provider-specific logic to map the canonical structure to the required API format.
  - Prefer chat format for text LLMs if available; otherwise, concatenate as above.
  - For image LLMs, concatenate all elements into a single prompt string.

- **Prompt Templates:**
  - Store templates with placeholders for each element, e.g.:
    ```
    [role] [voice]
    Task: [operation]
    Input: [data]
    ```
  - Backend replaces placeholders with actual values.

## 4a. ⚠️ Important: LLMs Do Not Interpret Custom JSON Keys

> **Warning:** LLM APIs (OpenAI, Ollama, etc.) only interpret specific keys in their payloads, such as `messages` (with `role` and `content`) or `prompt`. **Custom keys** like `voice`, `style`, or `format` are ignored by the LLM unless you explicitly include their meaning in the prompt or message content.
>
> - If you send `{ "voice": "Billy Connolly", "format": "bullet points", ... }`, the LLM will ignore `voice` and `format` unless you build a prompt string like: `Write in the style of Billy Connolly. Format your answer as bullet points. ...`.
> - Only standard API keys (like `role`, `content`, `prompt`) are interpreted by the LLM API.

**Best Practice:**
- Always compose a natural language prompt or message content that includes all four elements.
- Use the backend to map your structured data to the correct prompt/message format for the LLM API.

**Example mapping:**

Canonical JSON:
```json
{
  "data": "dog breakfasts",
  "role": "Scottish expert",
  "voice": "Billy Connolly",
  "format": "bullet points",
  "operation": "Summarise"
}
```

Mapped for a chat API:
```json
{
  "messages": [
    { "role": "system", "content": "You are a Scottish expert. Write in the style of Billy Connolly. Format your answer as bullet points." },
    { "role": "user", "content": "Summarise the following: dog breakfasts" }
  ]
}
```

Mapped for a single-prompt API:
```
You are a Scottish expert. Write in the style of Billy Connolly. Format your answer as bullet points.
Task: Summarise the following.
Input: dog breakfasts
```

---

## 5. Data Flow Diagram

```