# LLM Framework Stack Diagram

This document provides a visual and written overview of the LLM framework architecture for BlogForge.

---

## Mermaid Diagram

```mermaid
graph TD
  subgraph Data Models
    PromptPart["LLMPromptPart"]
    Provider["LLMProvider"]
    Model["LLMModel"]
    Message["LLMMessage"]
    Task["LLMTask"]
  end

  subgraph Service Layer
    PromptAssembly["Prompt Assembly"]
    ProviderAdapter["Provider/Model Adapter"]
    TaskRunner["Task Runner"]
  end

  subgraph API
    API["RESTful API (Flask-RESTful)"]
  end

  subgraph UI
    Dashboard["LLM Dashboard"]
    PromptUI["Prompt Assembly UI"]
    TaskUI["Task Runner UI"]
    WorkflowUI["Workflow Integration"]
  end

  PromptPart -->|used by| PromptAssembly
  Provider -->|registered in| ProviderAdapter
  Model -->|registered in| ProviderAdapter
  Message -->|used by| PromptAssembly
  PromptAssembly -->|calls| ProviderAdapter
  ProviderAdapter -->|executes| TaskRunner
  TaskRunner -->|exposes| API
  API -->|serves| Dashboard
  API -->|serves| PromptUI
  API -->|serves| TaskUI
  API -->|serves| WorkflowUI
  Task -->|tracked by| TaskRunner
  WorkflowUI -->|integrates with| Dashboard
```

---

## Component Overview

- **Data Models:**
  - `LLMPromptPart`: Modular parts of prompts (system, user, style, etc.)
  - `LLMProvider`/`LLMModel`: Registry of available providers/models
  - `LLMMessage`: Message-based prompt structure
  - `LLMTask`: Tracks LLM executions and results
- **Service Layer:**
  - Prompt assembly, provider/model adapters, and task runner logic
- **API:**
  - RESTful endpoints for managing providers, models, prompts, tasks, and results
- **UI:**
  - Dashboard for LLM management
  - Prompt assembly and preview
  - Task runner and results
  - Workflow integration (e.g., "Automate with LLM" in workflow stages)

---

## Updating This Diagram
- Update the Mermaid diagram and this doc as the stack evolves.
- Add PNGs or screenshots for more complex flows if needed.
- Reference this doc from the [README](./README.md) and implementation plan. 