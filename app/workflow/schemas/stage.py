from marshmallow import Schema, fields

class StageSchema(Schema):
    id = fields.Int(dump_only=True)
    workflow_id = fields.Int(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    stage_order = fields.Int(required=True)
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True) 