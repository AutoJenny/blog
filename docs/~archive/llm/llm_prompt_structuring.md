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
    { "role": "user", "content": "Expand the following into a paragraph-length brief for a long-form blog article." },
    { "role": "user", "content": "dog breakfasts" }
  ],
  "temperature": 0.7,
  "max_tokens": 1003
}
```

#### b) Single-prompt APIs

```
You are a Scottish expert. Write in the style of Billy Connolly.
Expand the following into a paragraph-length brief for a long-form blog article.
dog breakfasts
```

**Note:**
- The backend now composes a natural, explicit prompt string for single-prompt LLMs (Ollama, etc.), joining all system/role/style/voice parts into a single instruction, all operation parts into a single instruction, and appending the input as a final line.
- There are no longer any 'Task:' or 'Input:' prefixes in the canonical prompt string for single-prompt LLMs. The prompt is clean and direct.

**Example:**

If your modular prompt parts are:
```json
[
  { "type": "system", "tags": ["role"], "content": "You are a French poet" },
  { "type": "system", "tags": ["style"], "content": "Always write in French verse" },
  { "type": "user", "tags": ["operation"], "content": "Write a French poem about the following topic" },
  { "type": "data", "tags": ["data"], "content": "" }
]
```
And your input is "the sea at dawn", the backend will compose:

```
You are a French poet. Always write in French verse.
Write a French poem about the following topic.
the sea at dawn
```

---

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
    [operation]
    [data]
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
Summarise the following.
dog breakfasts
```

---

## 5. Data Flow Diagram

```
```

## Update (2025-05-29)

As of 2025-05-29, the backend now always uses `parse_tagged_prompt_to_messages` to build the canonical prompt for LLM actions. This ensures that all system, user, operation, and data elements are included in the prompt sent to the LLM, in accordance with this document. See the changelog entry for details of the bug fix that resolved prompt stripping issues.