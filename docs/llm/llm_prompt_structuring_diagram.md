# LLM Prompt Structuring: Data Flow Diagram

> **Note:** LLMs do not interpret custom JSON keys (like "voice" or "style") unless you explicitly include them in the prompt or message content. The backend must compose all elements into the prompt string or message array as required by the LLM API.

```mermaid
graph TD
    A[Frontend: User Input] -->|data, role, voice, operation| B[API: Canonical JSON]
    B --> C[Backend: Compose Prompt/Message]
    C -->|Provider-specific| D1[Ollama/OpenAI: messages array]
    C -->|Provider-specific| D2[Ollama/SD: prompt string]
    D1 & D2 --> E[LLM Provider]
    E --> F[Response]
    F --> G[Backend: Parse/Format]
    G --> H[Frontend: Display Output]
```

---

# LLM Prompt Composition Diagram

```mermaid
graph LR
    role[Role] --> prompt[Prompt Template]
    voice[Voice/Style] --> prompt
    operation[Operation] --> prompt
    data[Data] --> prompt
    prompt -->|Composed| LLM[LLM API]
``` 