# System Architecture

The Blog CMS is organized into modular components for maintainability and scalability. Below is a high-level overview of the system's architecture.

## Main Components
- **Flask App:** Core backend, routing, and business logic
- **Database:** PostgreSQL, managed via SQLAlchemy models and direct SQL scripts
- **LLM Service:** Handles AI-assisted content creation and suggestions
- **Frontend:** Jinja2 templates, Tailwind CSS, static assets
- **APIs:** RESTful endpoints for blog, LLM, and media
- **Scripts:** Utilities for migration, backup, and workflow automation

## Component Diagram

```mermaid
graph TD;
    A[User] -->|Web| B[Flask App]
    B -->|ORM| C[PostgreSQL]
    B -->|REST| D[LLM Service]
    B -->|Static| E[Frontend (Jinja2, Tailwind)]
    B -->|API| F[APIs]
    B -->|Scripts| G[Utilities]
```

- **User:** Interacts via web UI
- **Flask App:** Central logic, routes requests
- **PostgreSQL:** Stores all persistent data
- **LLM Service:** Provides AI features
- **Frontend:** Renders UI, uses Tailwind for styling
- **APIs:** Expose data and actions
- **Utilities:** Scripts for admin/dev tasks 