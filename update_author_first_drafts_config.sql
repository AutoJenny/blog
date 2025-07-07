UPDATE workflow_step_entity SET config = '{
  "inputs": {
    "input1": {
      "type": "textarea",
      "label": "Ideas to Include",
      "db_field": "ideas_to_include",
      "db_table": "post_section"
    }
  },
  "outputs": {
    "output1": {
      "type": "textarea",
      "label": "First Draft Content",
      "db_field": "first_draft",
      "db_table": "post_section"
    }
  },
  "settings": {
    "llm": {
      "model": "llama3.2:latest",
      "timeout": 360,
      "provider": "ollama",
      "parameters": {
        "top_p": 0.9,
        "max_tokens": 1000,
        "temperature": 0.7,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
      },
      "user_output_mapping": {
        "field": "first_draft",
        "table": "post_section"
      }
    }
  },
  "llm_available_tables": ["post_development", "post_section"]
}'
WHERE name = 'Author First Drafts'; 