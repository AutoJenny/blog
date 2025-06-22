-- Rename the Main step to initial
UPDATE workflow_step_entity wse
SET name = 'initial'
FROM workflow_sub_stage_entity wsse
WHERE wse.sub_stage_id = wsse.id
AND wsse.name = 'idea'
AND wse.name = 'Main'; 