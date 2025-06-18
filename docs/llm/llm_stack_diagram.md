# LLM Framework Stack Diagram

This document provides a visual and written overview of the LLM framework architecture for BlogForge, including how LLMs are integrated, extended, and used throughout the system.

---

## LLM Stack Overview

BlogForge's LLM stack is designed for flexibility, extensibility, and robust content automation. It supports multiple providers (OpenAI, Ollama, Anthropic, etc.), prompt templating, action orchestration, and full auditability.

### **Key Components**
- **Providers:** Pluggable backends (OpenAI, Ollama, etc.)
- **LLM Factory:** Central registry and instantiation for providers
- **LLM Service:** Unified interface for generating text, metadata, and executing actions
- **Prompt Management:** Database-driven prompt templates, versioned and reusable
- **LLM Actions:** Orchestrated tasks (summarize, tag, SEO, etc.)
- **LLM Interactions:** Full logging of all LLM calls and results
- **API Layer:** REST endpoints for config, invocation, and management
- **UI Integration:** Authoring, review, and admin interfaces

---

## Mermaid Diagram

```mermaid
graph TD
  subgraph Providers
    OpenAI[OpenAI]
    Ollama[Ollama]
    Anthropic[Anthropic]
    Custom[Custom/Other]
  end

  subgraph LLMFactory
    Factory[LLM Factory]
  end

  subgraph LLMService
    Service[LLM Service]
  end

  subgraph DataModels
    Prompt[LLMPrompt]
    Action[LLMAction]
    Interaction[LLMInteraction]
    Config[LLMConfig]
  end

  subgraph API
    API_Node[REST API]
  end

  subgraph UI
    Dashboard[Dashboard]
    Authoring[Authoring UI]
    Admin[Admin UI]
  end

  %% Connections
  OpenAI --> Factory
  Ollama --> Factory
  Anthropic --> Factory
  Custom --> Factory
  Factory --> Service
  Service --> Prompt
  Service --> Action
  Service --> Interaction
  Service --> Config
  Service --> API_Node
  API_Node --> Dashboard
  API_Node --> Authoring
  API_Node --> Admin
  Prompt --> Service
  Action --> Service
  Config --> Service
  Interaction --> Service
```

---

## How It Works

1. **Provider Abstraction:**
   - All LLM providers inherit from a common interface (`LLMProvider`).
   - Providers are registered with the `LLMFactory` for dynamic instantiation.
   - Example: Add a new provider by subclassing `LLMProvider` and registering it.

2. **LLM Factory:**
   - Central registry for all providers.
   - Handles instantiation and caching of provider instances.
   - Used by the `LLMService` to obtain the correct backend.

3. **LLM Service:**
   - Main entry point for all LLM operations (text generation, metadata, actions).
   - Handles prompt templating, context injection, and provider selection.
   - Logs all interactions for audit and debugging.

4. **Prompt & Action Management:**
   - Prompts and actions are stored in the database (`LLMPrompt`, `LLMAction`).
   - Prompts are versioned and reusable; actions can be chained or parameterized.
   - All LLM calls are logged as `LLMInteraction` records.

5. **API & UI Integration:**
   - REST API exposes LLM config, invocation, and management endpoints.
   - UI surfaces (dashboard, authoring, admin) allow users to trigger LLM actions, review results, and manage prompts.

---

## Extending the Stack

- **Add a Provider:**
  - Implement a new `LLMProvider` subclass.
  - Register it in the `LLMFactory`.
  - Add config options as needed.

- **Add a Prompt/Action:**
  - Create a new prompt template in the database.
  - Define a new `LLMAction` for custom workflows.

- **Audit & Debug:**
  - All LLM calls and results are logged in `LLMInteraction`.
  - Use the admin UI or API to review history and troubleshoot.

---

## References & Further Reading
- [LLM Reference Stack README](./README.md)
- [LLM Resources Index](./llm_resources.md)
- [LLM Integration Guide](../project/llm_architecture.md)
- [Hybrid LLM Framework Refactor Plan](../temp/llm_framework_hybrid_refactor.md)

---

## Example: Custom LLM Task/Action Workflow

This example shows how you can construct a Task or Action that takes data from one field (e.g., a blog post body), applies a pre-constructed LLM process (with configurable model, system/context messages, prompt instructions, etc.), and outputs results into another field (e.g., summary, tags, or SEO description).

### **Workflow Diagram**

```mermaid
graph TD
    A[Source Field (e.g., Post Body)] -->|Extract Data| B[LLMAction]
    B -->|Select Model & Config| C[LLMConfig]
    B -->|Apply System/Context Message| D[System Message]
    B -->|Apply Prompt Instructions| E[Prompt Template]
    B -->|Inject Context/Styling| F[Context/Styling Message]
    B -->|Call LLM Provider| G[LLMProvider]
    G -->|Generate Output| H[LLMInteraction]
    H -->|Store Result| I[Target Field (e.g., Summary, Tags)]
    I -->|Review/Edit| J[UI/Admin]
```

### **Step-by-Step Process**

1. **Define the Action/Task:**
   - Create an `LLMAction` in the database specifying:
     - Source field (e.g., `post.body`)
     - Target field (e.g., `post.summary`)
     - Model/provider to use (e.g., OpenAI GPT-4, Ollama Mistral)
     - System/context message (e.g., "You are a helpful summarizer...")
     - Prompt instructions (e.g., "Summarize the following text:")
     - Optional: context/styling message, temperature, max tokens, etc.

2. **Configure the Prompt:**
   - Use a stored `LLMPrompt` template, which can include variables for dynamic substitution (e.g., `{body}`).

3. **Execute the Action:**
   - The `LLMService` retrieves the action, prompt, and config.
   - It extracts the source field data, applies the system/context messages, and fills in the prompt template.
   - The configured provider/model is selected via `LLMFactory`.

4. **LLM Call & Output:**
   - The LLM is called with the constructed prompt and config.
   - The output is stored in the target field (e.g., `post.summary`).
   - The full interaction is logged in `LLMInteraction` for audit and review.

5. **Review & Edit:**
   - The result is shown in the UI for review, editing, or approval.
   - Admins can adjust prompts, configs, or rerun actions as needed.

---

**This workflow enables you to automate and customize LLM-powered content tasks, with full control over model selection, prompt engineering, and output handling.**

*For more advanced chaining, you can compose multiple actions/tasks, each with their own configs and prompts, to build complex content pipelines.*

*Update this diagram and section as the LLM stack evolves. For questions or contributions, see the README and implementation plan.* 