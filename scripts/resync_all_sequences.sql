-- Resync all sequences to the max(id) of their respective tables
-- Run after restores, migrations, or manual inserts to prevent duplicate key errors

SELECT setval('category_id_seq', (SELECT COALESCE(MAX(id), 1) FROM category), true);
SELECT setval('image_format_id_seq', (SELECT COALESCE(MAX(id), 1) FROM image_format), true);
SELECT setval('image_id_seq', (SELECT COALESCE(MAX(id), 1) FROM image), true);
SELECT setval('image_prompt_example_id_seq', (SELECT COALESCE(MAX(id), 1) FROM image_prompt_example), true);
SELECT setval('image_setting_id_seq', (SELECT COALESCE(MAX(id), 1) FROM image_setting), true);
SELECT setval('image_style_id_seq', (SELECT COALESCE(MAX(id), 1) FROM image_style), true);
SELECT setval('llm_action_history_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_action_history), true);
SELECT setval('llm_action_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_action), true);
SELECT setval('llm_interaction_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_interaction), true);
SELECT setval('llm_model_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_model), true);
SELECT setval('llm_prompt_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_prompt), true);
SELECT setval('llm_prompt_part_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_prompt_part), true);
SELECT setval('llm_provider_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_provider), true);
SELECT setval('post_development_id_seq', (SELECT COALESCE(MAX(id), 1) FROM post_development), true);
SELECT setval('post_id_seq', (SELECT COALESCE(MAX(id), 1) FROM post), true);
SELECT setval('post_section_id_seq', (SELECT COALESCE(MAX(id), 1) FROM post_section), true);
SELECT setval('post_substage_action_id_seq', (SELECT COALESCE(MAX(id), 1) FROM post_substage_action), true);
SELECT setval('post_workflow_stage_id_seq', (SELECT COALESCE(MAX(id), 1) FROM post_workflow_stage), true);
SELECT setval('post_workflow_sub_stage_id_seq', (SELECT COALESCE(MAX(id), 1) FROM post_workflow_sub_stage), true);
SELECT setval('substage_action_default_id_seq', (SELECT COALESCE(MAX(id), 1) FROM substage_action_default), true);
SELECT setval('tag_id_seq', (SELECT COALESCE(MAX(id), 1) FROM tag), true);
SELECT setval('user_id_seq', (SELECT COALESCE(MAX(id), 1) FROM "user"), true);
SELECT setval('workflow_id_seq', (SELECT COALESCE(MAX(id), 1) FROM workflow), true);
SELECT setval('workflow_stage_entity_id_seq', (SELECT COALESCE(MAX(id), 1) FROM workflow_stage_entity), true);
SELECT setval('workflow_sub_stage_entity_id_seq', (SELECT COALESCE(MAX(id), 1) FROM workflow_sub_stage_entity), true); 