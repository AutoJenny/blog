# Modular Git Branch Framework for Firewalled Components

## Overview
This document describes the architecture, schema, and operating manual for a robust modular development workflow using **firewalled git branches** for each major component/module. The goal is to ensure that no module can overwrite or interfere with another, while still allowing seamless integration and live testing in the main site (the HUB branch).

---

## 1. Directory & Branch Schema

```
repo-root/
├── docs/
│   └── git_modules/
│       └── README.md  # This file
├── modules/
│   ├── nav/           # Nav module (only in nav branch)
│   ├── llm_action/    # LLM-Action module (only in llm_action branch)
│   └── sections/      # Sections module (only in sections branch)
├── hub/               # Main site shell (in HUB branch)
├── ...                # Other shared assets
```

- **Each module branch** (e.g., `nav`, `llm_action`, `sections`) contains only its own `/modules/<module_name>/` directory and nothing else.
- **The `HUB` branch** contains the full site shell, with dynamic includes for modules.

---

## 2. Branching & Isolation

- **Module branches**: Only the code for that module exists in the branch. No other code is present.
- **HUB branch**: Contains only the shell and dynamic includes for modules. No module code is directly edited here.
- **No merging between module branches.** Only the HUB branch can "see" all modules, and only via includes.

---

## 3. Integration & Includes

- The HUB branch uses a dynamic import system (e.g., Flask blueprints, Python importlib, or JS dynamic imports) to load modules if present.
- If a module is missing, the site still runs, but that feature is disabled or stubbed.
- For local development, symlinks or scripts can be used to "mount" a module into the HUB branch for live testing.

---

## 4. Workflow & Operating Manual

### A. Developing a Module
1. **Checkout the module branch:**
   ```sh
   git checkout nav  # or llm_action, sections, etc.
   ```
2. **Work only in `/modules/<module_name>/`.**
3. **Test locally:** Use a script to symlink or copy the module into a local clone of the HUB branch for integration testing.

### B. Updating a Module in the Main Site
1. **Push changes to the module branch.**
2. **In the HUB branch, run:**
   ```sh
   ./scripts/update_module.sh <module_name>
   ```
   - This script pulls the latest from the module branch and integrates it into the HUB branch.
   - Runs tests/builds as needed.
   - Commits the update.

### C. CI/CD Enforcement
- CI checks ensure that only the intended module directory is updated in the HUB branch.
- No code outside `/modules/<module_name>/` is changed in a module update.
- The HUB branch only updates module includes, not module code directly.

### D. Restoring/Cloning
- After cloning, run:
  ```sh
  ./scripts/setup.sh
  ```
  - This script checks out the HUB branch and sets up symlinks or copies for all modules as needed.

---

## 5. Automation Scripts (to be implemented)
- `update_module.sh`: Updates a module in the HUB branch.
- `test_integration.sh`: Runs integration tests with all modules present.
- `dev_symlink.sh`: Symlinks a module for local development.
- `setup.sh`: Sets up the repo after clone.
- `ci_check.sh`: Ensures no cross-module contamination in PRs.

---

## 6. Best Practices
- **Never edit module code in the HUB branch.**
- **Never merge module branches into each other.**
- **Always use scripts for integration and updates.**
- **Document module APIs and contracts clearly.**

---

## 7. Example Workflow

1. Developer works on `modules/nav/` in the `nav` branch.
2. When ready, pushes changes to `nav` branch.
3. In the HUB branch, runs `./scripts/update_module.sh nav` to pull in the latest nav module.
4. CI checks ensure only `/modules/nav/` is updated.
5. The site is tested and deployed from the HUB branch.

---

## 8. FAQ

**Q: What if a module needs to communicate with another?**
- Use well-defined APIs, events, or shared database tables. Never direct imports.

**Q: What if a module breaks the site?**
- Revert the module branch or remove its include from the HUB branch.

**Q: Can I work on multiple modules at once?**
- Yes, but always in their own branches. Integrate via the HUB branch only.

---

## 9. Change Log
- _[Add entries here as the system evolves]_ 