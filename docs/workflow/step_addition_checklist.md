# Workflow Step Addition Checklist

## 1. Configuration
- [ ] Add the new step to the correct substage in `app/workflow/config/planning_steps.json`.
    - Use a dict for `inputs` and `outputs` (not a list!).
    - Ensure each input/output has: `type`, `label`, `db_field`, `db_table`, and `required` (if needed).
    - Under `settings.llm`, specify `provider`, `model`, `system_prompt`, `task_prompt`, `input_mapping`, `output_mapping`, and `parameters`.
    - Double-check that the config structure matches other working steps.
- [ ] If using a custom prompt file, ensure it exists in `app/data/prompts/` and is referenced correctly.

## 2. Database
- [ ] Confirm the required input/output fields exist in the relevant database table (e.g., `post_development`).
- [ ] If needed, add new fields to the database and document them in `/docs/database/`.

## 3. Navigation & Registration
- [ ] Ensure the new step is registered in the workflow navigation (database tables: `workflow_step_entity`, etc.).
- [ ] Confirm the step appears in the UI navigation for its substage.

## 4. Backend Route Logic
- [ ] In any custom route (e.g., `/planning/structure/outline/`), always iterate over `step_config['inputs']` and `step_config['outputs']` as dicts using `.items()`, not as lists.
- [ ] When passing data to templates, always set:
    - `input_values` and `output_values` as dicts keyed by input/output id.
    - `output_field` and `output_value` for summary display (using the output mapping from config).
    - `fields` as a list of available DB fields for selectors.
- [ ] Use the same variable names and structure as the main `step` route for consistency.

## 5. Template Logic
- [ ] Ensure the step template (e.g., `workflow/steps/outline.html`) extends `planning_step.html` and does not override core blocks unless needed.
- [ ] The shared `_workflow_content.html` template expects `step_config`, `input_values`, `output_values`, `output_field`, `output_value`, and `fields`.
- [ ] Do not hardcode logic for a specific step; rely on config and backend variables.

## 6. Testing
- [ ] Use `curl` to test the new step route (e.g., `curl -X GET http://localhost:5000/workflow/1/planning/structure/outline/`).
- [ ] Confirm the page loads with no errors and displays the correct input, output, and prompt sections.
- [ ] If the UI says "No inputs configured" or "No prompt configured", check:
    - The config structure (dicts, not lists)
    - That the backend is passing all required variables
    - That the database has the required fields and data
- [ ] Test the LLM generation for the step if applicable.

## 7. Documentation
- [ ] Update this checklist and `/docs/database/` as needed with any new learnings or requirements.
- [ ] Document all new fields, endpoints, and config changes.

---

## Troubleshooting: Common Step Addition Issues

**1. 500 Error or Null step_id:**
- This almost always means the step is not registered in the `workflow_step_entity` table for the correct substage. Use SQL to check:
  ```sql
  SELECT * FROM workflow_step_entity WHERE name = '<step_name>';
  ```
  If missing, insert it:
  ```sql
  INSERT INTO workflow_step_entity (sub_stage_id, name, description, step_order) VALUES (<sub_stage_id>, '<step_name>', '<description>', <order>);
  ```
- Example: For the 'outline' step in the 'structure' substage, add:
  ```sql
  INSERT INTO workflow_step_entity (sub_stage_id, name, description, step_order) VALUES (3, 'outline', 'Generate a detailed blog post outline based on the expanded idea.', 1);
  ```

**2. psycopg2.errors.UndefinedColumn:**
- This means the step config references a DB field that does not exist. Add the column to the relevant table:
  ```sql
  ALTER TABLE post_development ADD COLUMN outline TEXT;
  ```
- Always check the config's `db_field` and `db_table` for each input/output.

**3. No new schema needed for new steps:**
- Most new steps only require registration in `workflow_step_entity` and ensuring the referenced DB field exists. You do NOT need to add new tables or change the schema for each step.

**4. Use the standard step route:**
- Do not create custom routes for new steps. Use the standard `/workflow/<post_id>/<stage>/<substage>/<step>/` route so all logic and navigation works consistently.

**5. Always test with curl:**
- After adding a step, test with curl to confirm the page loads and the step_id is not null:
  ```sh
  curl -v http://localhost:5000/workflow/<post_id>/<stage>/<substage>/<step>/
  ```

---

**Summary:**
- Register the step in `workflow_step_entity`.
- Ensure the referenced DB field exists.
- Use the standard route.
- Test with curl.
- No new schema or custom routes needed for most steps.

---

**Quick Reference for Common Pitfalls:**
- Always use dicts for `inputs` and `outputs` in config, not lists.
- Always iterate with `.items()` in backend when loading values.
- Always set `output_field` and `output_value` for summary display.
- Always test with `curl` before considering a step "working".
- If the UI is blank or says "not configured", check config structure, backend variable passing, and DB fields.
- Always ensure `stepId` is passed from backend to template and checked in JavaScript before making API calls. If `stepId` is null/undefined, log a warning and do not call the API. This prevents 500 errors from invalid stepId values. 