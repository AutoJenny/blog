# Development Rules & Best Practices

## File Size Limit (Golden Rule)

**CRITICAL: No file should exceed 400-500 lines of code.**

### Rationale
- Improves maintainability
- Enhances readability
- Makes code easier to test
- Reduces merge conflicts
- Encourages proper separation of concerns

### When a File Approaches the Limit

1. **Extract functionality into separate modules:**
   - Create focused utility classes
   - Split large functions into smaller, reusable functions
   - Move related functionality to dedicated modules

2. **Use composition over monolithic classes:**
   - Break large classes into smaller, focused classes
   - Use helper classes for specific responsibilities
   - Create service layers for complex operations

3. **Split API endpoints:**
   - Group related endpoints into separate blueprint files
   - Use route registration functions to organize endpoints
   - Keep each blueprint focused on a single domain

4. **Modularize templates:**
   - Use template partials/includes
   - Break large templates into reusable components
   - Keep templates focused on single responsibilities

### Examples from This Codebase

- **Vector Search:** Split into `chunking.py`, `embeddings.py`, `faiss_index.py`, `retrieval.py`
- **Imaging API:** Split into `imaging_api_config.py`, `imaging_api_data.py`, `imaging_api_generation.py`, etc.
- **Content Generation:** Will be split into focused modules (generation engine, prompt management, post creation, etc.)

### Enforcement

- **Before committing:** Review file sizes
- **During development:** Refactor proactively when approaching limits
- **Code review:** Flag files approaching or exceeding limits

---

## Other Development Practices

### Code Organization
- Keep related functionality together
- Use clear, descriptive module names
- Follow existing codebase patterns

### Documentation
- Document complex logic
- Include docstrings for public functions/classes
- Update planning docs as implementation progresses

### Testing
- Test functionality as you build
- Verify imports and basic functionality
- Document test results

---

**Last Updated:** 2025-01-10  
**Status:** Active

