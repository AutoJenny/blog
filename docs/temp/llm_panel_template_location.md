# LLM Panel Template Location

The canonical location for LLM Panel templates is:

`app/templates/modules/llm_panel/templates/`

This includes:
- `panel.html` - The main panel template
- `components/` - Directory containing component templates:
  - `inputs.html`
  - `outputs.html`
  - `prompt.html`
  - `settings.html`

## Template Resolution

The LLM Panel blueprint (defined in `modules/llm_panel/__init__.py`) correctly points to this template directory. Any other template directories with similar names (containing "FUCKUP" etc.) are outdated and should be deleted.

## Verification

The template resolution was verified working on June 5th, 2025 using test markers in the templates. The templates are being correctly loaded from this location. 