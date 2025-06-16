from marshmallow import Schema, fields

class WorkflowSchema(Schema):
    id = fields.Int(dump_only=True)
    sub_stage_id = fields.Int()
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    step_order = fields.Int(required=True)
    config = fields.Dict(allow_none=True)
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True) 