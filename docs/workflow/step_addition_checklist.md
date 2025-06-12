# Workflow Step Addition Checklist

## 1. Configuration
- [ ] Add the new step to the correct substage in `app/workflow/config/planning_steps.json`.
    - Use a dict for `inputs` and `outputs` (not a list!).
    - Ensure each input/output has: `type`, `label`, `db_field`, `db_table`, and `required` (if needed).
    - Under `settings.llm`, specify `provider`, `model`, `system_prompt`, `task_prompt`, `input_mapping`, `output_mapping`, and `parameters`.
    - Double-check that the config structure matches other working steps.
    - Verify the step order is correct relative to other steps in the substage.
- [ ] Create a prompt file in `app/data/prompts/` if needed:
    - Name format: `planning_<substage>_<step>.json`
    - Include both `system_prompt` and `task_prompt`
    - Add example format in the task prompt
    - Test the prompt with sample data before proceeding

## 2. Database
- [ ] Check if the required input/output fields exist in the relevant database table (e.g., `post_development`):
    ```sql
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'post_development';
    ```
- [ ] If needed, add new fields to the database:
    ```sql
    ALTER TABLE post_development ADD COLUMN <field_name> TEXT;
    ```
- [ ] Document new fields in `/docs/database/` if added.

## 3. Navigation & Registration
- [ ] Get the correct `sub_stage_id` for the step:
    ```sql
    SELECT id FROM workflow_sub_stage_entity WHERE name = '<substage_name>';
    ```
- [ ] Add the step to `workflow_step_entity`:
    ```sql
    INSERT INTO workflow_step_entity (sub_stage_id, name, description, step_order) 
    VALUES (<sub_stage_id>, '<step_name>', '<description>', <order>);
    ```
- [ ] Verify the step appears in the UI navigation for its substage.

## 4. Backend Route Logic
- [ ] In any custom route (e.g., `/planning/structure/outline/`), always iterate over `step_config['inputs']` and `step_config['outputs']` as dicts using `.items()`, not as lists.
- [ ] When passing data to templates, always set:
    - `input_values` and `output_values` as dicts keyed by input/output id.
    - `output_field` and `output_value` for summary display (using the output mapping from config).
    - `fields` as a list of available DB fields for selectors.
- [ ] Use the same variable names and structure as the main `step` route for consistency.

## 5. Template Logic
- [ ] Create the step template in `app/templates/workflow/steps/<step>.html`:
    - Extend `planning_step.html`
    - Define the `step_content` block
    - Include input and output sections
    - Add any step-specific UI elements
- [ ] The shared `_workflow_content.html` template expects:
    - `step_config`
    - `input_values`
    - `output_values`
    - `output_field`
    - `output_value`
    - `fields`
- [ ] Do not hardcode logic for a specific step; rely on config and backend variables.

## 6. Testing
- [ ] Test the step route with curl:
    ```bash
    curl -v http://localhost:5000/workflow/<post_id>/<stage>/<substage>/<step>/
    ```
- [ ] Verify the page loads with no errors and displays:
    - Input fields
    - Output fields
    - Prompt section
    - Settings section
- [ ] Test the LLM generation:
    ```bash
    curl -X POST http://localhost:5000/workflow/<post_id>/<stage>/<substage>/<step>/run_llm \
    -H "Content-Type: application/json" \
    -d '{"input_field": "test input"}'
    ```
- [ ] If the UI shows "No inputs configured" or "No prompt configured", check:
    - The config structure (dicts, not lists)
    - That the backend is passing all required variables
    - That the database has the required fields and data
    - That the prompt file exists and is properly formatted

## 7. Documentation
- [ ] Update this checklist with any new learnings or requirements.
- [ ] Document all new fields, endpoints, and config changes in `/docs/database/`.
- [ ] Add any step-specific instructions to `/docs/workflow/`.

---

## Troubleshooting: Common Step Addition Issues

**1. 500 Error or Null step_id:**
- This almost always means the step is not registered in the `workflow_step_entity` table for the correct substage. Use SQL to check:
  ```sql
  SELECT * FROM workflow_step_entity WHERE name = '<step_name>';
  ```
  If missing, insert it:
  ```sql
  INSERT INTO workflow_step_entity (sub_stage_id, name, description, step_order) 
  VALUES (<sub_stage_id>, '<step_name>', '<description>', <order>);
  ```

**2. psycopg2.errors.UndefinedColumn:**
- This means the step config references a DB field that does not exist. Add the column to the relevant table:
  ```sql
  ALTER TABLE post_development ADD COLUMN <field_name> TEXT;
  ```
- Always check the config's `db_field` and `db_table` for each input/output.

**3. No new schema needed for new steps:**
- Most new steps only require registration in `workflow_step_entity` and ensuring the referenced DB field exists.
- You do NOT need to add new tables or change the schema for each step.

**4. Use the standard step route:**
- Do not create custom routes for new steps.
- Use the standard `/workflow/<post_id>/<stage>/<substage>/<step>/` route so all logic and navigation works consistently.

**5. Always test with curl:**
- After adding a step, test with curl to confirm the page loads and the step_id is not null:
  ```bash
  curl -v http://localhost:5000/workflow/<post_id>/<stage>/<substage>/<step>/
  ```
- Test the LLM endpoint with sample data:
  ```bash
  curl -X POST http://localhost:5000/workflow/<post_id>/<stage>/<substage>/<step>/run_llm \
  -H "Content-Type: application/json" \
  -d '{"input_field": "test input"}'
  ```

---

**Summary:**
1. Register the step in `workflow_step_entity`
2. Ensure the referenced DB field exists
3. Create/update the prompt file if needed
4. Add the step config to `planning_steps.json`
5. Create the step template
6. Test with curl
7. No new schema or custom routes needed for most steps

---

**Quick Reference for Common Pitfalls:**
- Always use dicts for `inputs` and `outputs` in config, not lists
- Always iterate with `.items()` in backend when loading values
- Always set `output_field` and `output_value` for summary display
- Always test with `curl` before considering a step "working"
- If the UI is blank or says "not configured", check:
  - Config structure
  - Backend variable passing
  - DB fields
  - Prompt file existence and format
- Always ensure `stepId` is passed from backend to template and checked in JavaScript before making API calls
- If `stepId` is null/undefined, log a warning and do not call the API to prevent 500 errors 