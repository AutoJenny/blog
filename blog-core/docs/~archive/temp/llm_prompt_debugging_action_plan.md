# LLM Prompt Debugging & Action Plan (May 2025)

## Summary: What We Learned

- **Direct LLM calls (curl, Python requests) with the correct prompt string always return the expected French poem.**
- **A minimal Flask app using requests and the same prompt also works perfectly.**
- **The main Flask app, when using its normal prompt construction logic, returns an English/incorrect response.**
- **When the main Flask app is patched to use the hardcoded prompt string, it works perfectly.**
- **A new /test-direct endpoint in the main app, using the same hardcoded prompt, also works.**
- **Conclusion:** The root cause is in the prompt construction logic (how modular prompts and fields are combined), not in Flask, requests, Ollama, or the environment.

---

## Action Plan: Fixing the Run Action Button

### 1. **Compare Prompt Strings**
- Log and compare the prompt string produced by the modular prompt construction logic to the hardcoded string that works.
- Look for differences in:
  - Whitespace, punctuation, or line breaks
  - Field substitution (e.g., input value)
  - Order and joining of prompt parts
  - Any extra or missing content

### 2. **Add Detailed Logging**
- Log the exact prompt string at every stage of construction (raw, after field merge, final string sent to LLM).
- Log the types and values of all fields used in prompt construction.

### 3. **Refactor Prompt Construction**
- Update `modular_prompt_to_canonical` and related functions to:
  - Join prompt parts in the same way as the hardcoded string (single space, no extra newlines).
  - Precede the data element with the exact label: `Data for this operation as follows: ...`.
  - Ensure all system, style, and operation parts are included in the correct order.
  - Remove any legacy or fallback logic that could alter the prompt.

### 4. **Test Iteratively**
- After each change, use the Run Action button and compare the prompt string and LLM output to the direct test.
- Continue until the constructed prompt matches the hardcoded string exactly and the LLM returns the correct French poem.

### 5. **Restore Normal Logic**
- Once the prompt construction is fixed, remove the hardcoded patch and restore normal action execution.
- Ensure all modular prompts and user inputs are handled correctly for all actions, not just the test case.

### 6. **Document and Commit**
- Update documentation in `/docs/llm/llm_prompt_structuring.md` and `/docs/llm/README.md` to reflect the correct prompt construction pattern.
- Commit all changes and update the changelog.

---

## Key Takeaways
- Always test LLM prompt construction logic against a known-good hardcoded string.
- Use minimal, direct tests to isolate bugs in complex workflows.
- Log everything at each stage for full transparency and reproducibility.

---

*This document should be used as a reference for future LLM prompt debugging and engineering.* 