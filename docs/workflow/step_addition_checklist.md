# Workflow Step Addition Checklist

## Configuration
- [ ] Use dictionaries for `inputs` and `outputs` in the step configuration
- [ ] Ensure the step is properly defined in `app/workflow/config/planning_steps.json` or `app/workflow/config/writing_steps.json`
- [ ] Verify all required fields are present in the configuration

## Database
- [ ] Confirm required fields exist in the database
- [ ] Document any new fields added to the schema

## Navigation & Registration
- [ ] Register the new step in the workflow navigation
- [ ] Ensure the step appears correctly in the UI
- [ ] Check that the step is properly linked in the main navigation panel
- [ ] Verify the step appears in the correct substage tabs in `_workflow_nav.html`
- [ ] For substages with multiple steps, ensure the default step routing is correct in `routes.py`
  - [ ] If a specific step should be the default, add a condition in the substage route
  - [ ] Example: For content substage, explicitly route to 'sections' step
  - [ ] For other substages, use the first registered step

## Backend Route Logic
- [ ] Iterate over `step_config` as dictionaries
- [ ] Ensure consistent variable names throughout
- [ ] Handle input/output field mapping correctly

## Template Logic
- [ ] Ensure templates extend correctly
- [ ] Don't hardcode logic for specific steps

## Testing
- [ ] Test the new step route with `curl`
- [ ] Verify inputs and outputs display correctly
- [ ] Test the LLM endpoint with the new step

## Documentation
- [ ] Update this checklist
- [ ] Document any new fields or changes

## Troubleshooting
- [ ] If getting 500 errors, check the step configuration
- [ ] If undefined columns, verify database schema
- [ ] If navigation issues:
  - [ ] Check the step is registered in `workflow_step_entity`
  - [ ] Verify the step name matches in all places
  - [ ] Check the default step routing in `routes.py`
  - [ ] Ensure the step is properly linked in `_workflow_nav.html`
- [ ] If configuration loading issues:
  - [ ] Check the JSON file exists and is valid
  - [ ] Verify the step is defined in the correct stage/substage
  - [ ] Check for any custom prompt files

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

**6. Navigation Issues:**
- If the main navigation panel shows the wrong step name or link:
  1. Check the stage group section in `_workflow_nav.html` (e.g., Writing panel)
  2. Ensure the link uses the correct step name (e.g., 'sections' not 'draft')
  3. Verify the URL parameters match the registered step
- If the substage tabs are missing or incorrect:
  1. Check the `elif current_substage == '...'` blocks in `_workflow_nav.html`
  2. Add the step to the correct substage block
  3. Use the same step name consistently in both navigation elements

**7. Configuration Loading Issues:**
- If step configuration isn't loading:
  1. Check that the config file exists in the correct location (`planning_steps.json` or `writing_steps.json`)
  2. Verify the config structure matches other working steps
  3. Make sure custom prompt files are optional in `load_step_config()`
  4. Check that the step is registered in the database with the correct name

---

**Summary:**
- Register the step in `workflow_step_entity`.
- Ensure the referenced DB field exists.
- Use the standard route.
- Test with curl.
- No new schema or custom routes needed for most steps.
- Check both navigation elements (main panel and tabs).
- Use consistent step names throughout.

---

**Quick Reference for Common Pitfalls:**
- Always use dicts for `inputs` and `outputs` in config, not lists.
- Always iterate with `.items()` in backend when loading values.
- Always set `output_field` and `output_value` for summary display.
- Always test with `curl` before considering a step "working".
- If the UI is blank or says "not configured", check config structure, backend variable passing, and DB fields.
- Always ensure `stepId` is passed from backend to template and checked in JavaScript before making API calls.
- Check both navigation elements for correct step names and links.
- Use the correct config file for the stage (`planning_steps.json` or `writing_steps.json`).
- Make custom prompt files optional in `load_step_config()`. 