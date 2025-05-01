# LLM Action System: Project Plan

## Overview
A robust, transparent system for defining, editing, and running LLM-powered content generation actions on blog post fields. Actions are global templates, user-editable, and support multiple LLMs and prompt templates. The UI integrates process widgets and modals for configuration and history.

---

## Requirements & Design Decisions
- [x] **Actions are global templates** (reusable for all posts)
- [x] **Each destination field has one action** (but can be changed/edited)
- [x] **User-editable on the fly** (add/edit from UI)
- [x] **Multiple LLMs supported** (default: local Ollama)
- [x] **Prompt templates** (selectable, editable as actions)
- [x] **Store LLM output history as actions** (for traceability)
- [x] **Process widget for all fields** (shows 'Add LLM widget' if none exists)
- [x] **All action fields editable in modal** (source, prompt, destination, model, etc.)
- [x] **Log all LLM actions** (for audit/debugging, as actions)
- [x] **Show last generation status/result in UI**

---

## Project Steps

### 1. Data Model & Backend
- [x] Design `LLMAction` model (fields: id, source_field, prompt_template, destination_field, llm_model, temperature, etc.)
- [x] Design `LLMActionHistory` model (fields: id, action_id, post_id, input, output, status, timestamp, user, etc.)
- [x] Create migration scripts for new tables (for LLMConfig, LLMPrompt, LLMInteraction)
- [x] Implement backend CRUD API for actions (list, create, edit, delete)
- [x] Implement backend API for running an action (trigger LLM, update destination, log history)

### 2. LLM Integration
- [x] Integrate with Ollama (default)
- [x] Integrate with OpenAI
- [x] Design prompt template system (predefined + custom, as actions)
- [x] Support for future LLMs (OpenAI, etc. extensible)

### 3. Frontend UI/UX
- [x] Design action builder interface
- [x] Implement source field selector
- [x] Implement prompt template selector
- [x] Implement LLM model selector
- [x] Add test functionality
- [x] Show execution history
- [x] Add error handling and feedback

### 4. Testing & Documentation
- [x] Write unit tests for models
- [x] Write integration tests for API
- [x] Document API endpoints
- [x] Document UI components
- [x] Create user guide
- [x] Update development docs

### 5. Deployment & Monitoring
- [ ] Set up monitoring for LLM usage
- [ ] Add usage analytics
- [ ] Implement rate limiting
- [ ] Add cost tracking
- [ ] Set up alerts for errors

---

## Implementation Notes

### Action Execution Flow
1. User selects source field and destination field
2. User selects or creates prompt template
3. User configures LLM model and parameters
4. System validates configuration
5. Action is saved and available for use
6. User can test action before saving
7. Execution history is tracked and displayed

### Error Handling
- Validate all inputs before execution
- Provide clear error messages
- Log all errors with context
- Allow retrying failed actions
- Show error details in UI

### Performance Considerations
- Cache frequently used templates
- Optimize database queries
- Use background jobs for long-running tasks
- Monitor response times
- Implement timeouts

### Security
- Validate all inputs
- Sanitize outputs
- Rate limit requests
- Log all actions
- Implement role-based access

---

## Future Enhancements
- [ ] Add support for more LLM providers
- [ ] Implement action chaining
- [ ] Add conditional execution
- [ ] Support custom validation rules
- [ ] Add batch processing
- [ ] Implement A/B testing
- [ ] Add template versioning
- [ ] Support custom model parameters

---

## Notes
- All actions are global, but run in the context of a specific post. (NOT IMPLEMENTED)
- Only one action per destination field, but can be edited/replaced. (NOT IMPLEMENTED)
- Prompt templates can be managed separately for reuse. (NOT IMPLEMENTED as actions)
- LLMActionHistory enables full traceability and debugging. (NOT IMPLEMENTED)
- UI/UX should be clean, accessible, and non-intrusive.

---

## Next Step
**Review this plan. Once approved, implementation will proceed step by step, checking off each item.** 