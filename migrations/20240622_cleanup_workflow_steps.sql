-- Delete old steps
DELETE FROM workflow_step_entity wse
USING workflow_sub_stage_entity wsse
WHERE wse.sub_stage_id = wsse.id
AND wsse.name = 'idea'
AND wse.name IN ('basic_idea', 'provisional_title'); 