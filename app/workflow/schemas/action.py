from marshmallow import Schema, fields

class ActionSchema(Schema):
    id = fields.Int(dump_only=True)
    substage_id = fields.Int(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    action_order = fields.Int(required=True)
    prompt_template = fields.Str(required=True)
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True) 