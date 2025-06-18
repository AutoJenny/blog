# Modular Config & Stylesheet Strategy for Firewalled Flask Branches

## Purpose
This document records the issues, requirements, and solutions for managing configuration and stylesheets in a modular, firewalled Flask project. It is the canonical reference for ensuring that each module/branch can be developed, tested, and merged into a unified core branch without conflicts or cross-contamination.

---

## 1. Config Management Issues & Solutions

### Issues
- Each module/branch may have unique config needs, but the core branch must run all modules together without conflicts.
- The current pattern (`from config import Config`) expects a single, global config.py, which is fragile for modularity.
- Missing config keys or conflicting settings can break merged branches.

### Solutions
- **Centralized, Extensible Config:**
  - Create a single `config.py` at the project root with a base `Config` class.
  - Allow each module to define its own config subclass (e.g., `WorkflowConfig(Config)`, `DocsConfig(Config)`) or use environment variables for module-specific settings.
  - The app factory (`create_app`) should accept a config class/object, so you can swap configs per branch or per module.
- **Environment Variable Overrides:**
  - Use `.env` files and `python-dotenv` to allow per-branch or per-developer overrides without changing code.
  - Each module can have its own `.env.module` file, loaded conditionally.
- **Config Discovery:**
  - The app factory should look for a config in a prioritized order:
    1. Explicit argument (for testing/CI)
    2. Environment variable (e.g., `APP_CONFIG`)
    3. Default to `Config` in `config.py`
- **Module Isolation:**
  - Each module should only read the config keys it needs.
  - Avoid global config mutations—pass config as needed.
- **Namespacing:**
  - Use namespaced config keys (e.g., `WORKFLOW_`, `DOCS_`) to avoid conflicts.
- **Secret Management:**
  - Never hardcode secrets; always use env vars.

---

## 2. Stylesheet Management Issues & Solutions

### Issues
- Each module/branch may require its own styles, but the core branch must present a unified look and feel.
- Stylesheet conflicts or missing styles can break merged branches or module previews.

### Solutions
- **Base Shared Stylesheet:**
  - Use a base stylesheet (e.g., `static/css/base.css` or `main.css`) for site-wide look and feel.
- **Per-Module Stylesheets:**
  - Each module can have its own stylesheet (e.g., `static/css/workflow.css`, `static/css/docs.css`) for module-specific overrides.
- **Dynamic Inclusion:**
  - Use Jinja blocks or context variables to include the correct stylesheets per module/page.
- **Merge Strategy:**
  - When merging, the core branch can concatenate or reference all needed stylesheets.
- **Documentation:**
  - Document required and optional stylesheets for each module in `/docs`.

---

## 3. Implementation Plan
1. Implement a robust `config.py` at the project root with a base `Config` class and support for module-specific configs.
2. Update all app factories to accept a config class/object.
3. Standardize on `.env` for secrets and per-branch overrides.
4. Document required config keys for each module in `/docs`.
5. Establish a base shared stylesheet and per-module stylesheets, with dynamic inclusion in templates.
6. Document stylesheet requirements and inclusion strategy in `/docs`.

---

## 4. Next Steps
- Begin implementation in the base-framework branch.
- Apply these principles to each module branch in turn.
- Review and update this document as the project evolves. 