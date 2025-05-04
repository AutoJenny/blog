# LLM Service Refactor (2025-05-04)

## Summary

- **All LLM service logic is now consolidated in `app/llm/services.py`.**
- The old service in `app/services/llm.py` is **deprecated** and replaced with a stub and warning comment.
- All imports and usages throughout the codebase now use `app.llm.services.LLMService` and `execute_llm_request`.
- The API and all LLM actions now use the new, unified service.
- The old file is left as a stub for backward compatibility but should not be used for any new code.

## Migration Steps

1. **Updated all imports** from `app.services.llm` to `app.llm.services`.
2. **Removed all code** from `app/services/llm.py` and replaced it with a deprecation notice.
3. **Verified** that all LLM API endpoints and LLM action execution use the new service.
4. **Tested** LLM action execution and confirmed timeouts and errors are now handled by the new service only.

## Next Steps
- Remove the deprecated file after a transition period if no legacy code depends on it.
- All future LLM-related development should use `app/llm/services.py` exclusively. 